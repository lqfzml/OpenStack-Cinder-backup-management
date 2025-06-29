from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import json
import os
from datetime import datetime, timedelta
from openstack_client import OpenStackClient
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # 允许跨域请求

# 初始化OpenStack客户端
try:
    openstack_client = OpenStackClient()
except Exception as e:
    logger.error(f"初始化OpenStack客户端失败: {e}")
    openstack_client = None

# 定时备份配置文件路径
SCHEDULE_FILE = 'backup_schedules.json'

def load_schedules():
    """加载定时备份配置"""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载定时备份配置失败: {e}")
    return []

def save_schedules(schedules):
    """保存定时备份配置"""
    try:
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存定时备份配置失败: {e}")
        return False

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/volumes')
def get_volumes():
    """获取云硬盘列表 - 显示所有状态，标记可备份状态"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        volumes = openstack_client.get_volumes()
        # 为每个云硬盘添加可备份标记
        for volume in volumes:
            volume['backupable'] = volume['status'] in ['in-use', 'available']
        
        return jsonify(volumes)
    except Exception as e:
        logger.error(f"获取云硬盘列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backups')
def get_backups():
    """获取备份列表 - 根据描述判断备份类型，分离全量备份和增量备份"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        backups = openstack_client.get_backups()
        
        # 根据backup_type字段分离全量备份和增量备份
        full_backups = [b for b in backups if b.get('backup_type') == 'full']
        incremental_backups = [b for b in backups if b.get('backup_type') == 'incremental']
        
        return jsonify({
            "full_backups": full_backups,
            "incremental_backups": incremental_backups,
            "all_backups": backups
        })
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules')
def get_schedules():
    """获取定时备份列表"""
    try:
        schedules = load_schedules()
        return jsonify(schedules)
    except Exception as e:
        logger.error(f"获取定时备份列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    """创建定时备份"""
    try:
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        backup_type = data.get('backup_type', 'full')  # full 或 incremental
        schedule_type = data.get('schedule_type', 'weekly')  # weekly 或 daily
        schedule_time = data.get('schedule_time', '02:00')  # 默认凌晨2点
        weekdays = data.get('weekdays', [])  # 周一到周日 [1,2,3,4,5,6,7]
        name = data.get('name', '')
        
        if not volume_ids:
            return jsonify({"error": "请选择要备份的云硬盘"}), 400
        
        if schedule_type == 'weekly' and not weekdays:
            return jsonify({"error": "请选择备份的星期"}), 400
        
        schedules = load_schedules()
        
        # 创建新的定时备份配置
        new_schedule = {
            "id": f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "volume_ids": volume_ids,
            "backup_type": backup_type,
            "schedule_type": schedule_type,
            "schedule_time": schedule_time,
            "weekdays": weekdays,
            "name": name,
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": None
        }
        
        schedules.append(new_schedule)
        
        if save_schedules(schedules):
            return jsonify({
                "success": True,
                "message": "定时备份创建成功",
                "schedule": new_schedule
            })
        else:
            return jsonify({"error": "保存定时备份配置失败"}), 500
            
    except Exception as e:
        logger.error(f"创建定时备份失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """删除定时备份"""
    try:
        schedules = load_schedules()
        schedules = [s for s in schedules if s['id'] != schedule_id]
        
        if save_schedules(schedules):
            return jsonify({"success": True, "message": "定时备份删除成功"})
        else:
            return jsonify({"error": "删除定时备份配置失败"}), 500
            
    except Exception as e:
        logger.error(f"删除定时备份失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules/<schedule_id>/toggle', methods=['POST'])
def toggle_schedule(schedule_id):
    """启用/禁用定时备份"""
    try:
        schedules = load_schedules()
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule['enabled'] = not schedule.get('enabled', True)
                break
        
        if save_schedules(schedules):
            return jsonify({
                "success": True, 
                "message": f"定时备份已{'启用' if schedule['enabled'] else '禁用'}",
                "enabled": schedule['enabled']
            })
        else:
            return jsonify({"error": "更新定时备份配置失败"}), 500
            
    except Exception as e:
        logger.error(f"切换定时备份状态失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/full', methods=['POST'])
def create_full_backup():
    """创建全量备份"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        name = data.get('name')
        
        if not volume_ids:
            return jsonify({"error": "请选择要备份的云硬盘"}), 400
        
        results = []
        for volume_id in volume_ids:
            result = openstack_client.create_full_backup(volume_id, name)
            results.append(result)
        
        success_count = sum(1 for r in results if r.get('success'))
        return jsonify({
            "success": success_count > 0,
            "results": results,
            "message": f"成功创建 {success_count} 个全量备份"
        })
    except Exception as e:
        logger.error(f"创建全量备份失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/incremental', methods=['POST'])
def create_incremental_backup():
    """创建增量备份"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        name = data.get('name')
        
        if not volume_ids:
            return jsonify({"error": "请选择要备份的云硬盘"}), 400
        
        results = []
        for volume_id in volume_ids:
            result = openstack_client.create_incremental_backup(volume_id, name)
            results.append(result)
        
        success_count = sum(1 for r in results if r.get('success'))
        return jsonify({
            "success": success_count > 0,
            "results": results,
            "message": f"成功创建 {success_count} 个增量备份"
        })
    except Exception as e:
        logger.error(f"创建增量备份失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/cleanup', methods=['POST'])
def cleanup_backups():
    """清理备份 - 支持自定义天数和按云硬盘策略"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json() or {}
        retention_days = data.get('retention_days', 30)  # 默认30天
        volume_policies = data.get('volume_policies', {})  # 按云硬盘的策略
        
        # 如果提供了按云硬盘的策略，则使用按云硬盘清理
        if volume_policies:
            result = openstack_client.cleanup_backups_by_volume(volume_policies)
            if result.get('success'):
                deleted_details = result.get('deleted_details', [])
                policy_summary = []
                for policy_volume_id, policy_days in volume_policies.items():
                    policy_summary.append(f"云硬盘 {policy_volume_id}: {policy_days}天")
                
                return jsonify({
                    "success": True,
                    "message": f"按云硬盘策略清理完成，共删除 {result.get('deleted_count', 0)} 个备份。策略: {'; '.join(policy_summary)}",
                    "deleted_count": result.get('deleted_count', 0),
                    "deleted_details": deleted_details,
                    "policies_applied": volume_policies
                })
            else:
                return jsonify({"error": result.get('error', '清理失败')}), 500
        else:
            # 使用统一的保留天数
            try:
                retention_days = int(retention_days)
                if retention_days < 1:
                    return jsonify({"error": "保留天数必须大于0"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "保留天数必须是有效的数字"}), 400
            
            result = openstack_client.cleanup_backups(retention_days)
            if result.get('success'):
                return jsonify({
                    "success": True,
                    "message": f"备份清理完成，共删除 {result.get('deleted_count', 0)} 个超过 {retention_days} 天的备份"
                })
            else:
                return jsonify({"error": result.get('error', '清理失败')}), 500
    except Exception as e:
        logger.error(f"备份清理失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/<backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """删除指定备份"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        result = openstack_client.delete_backup(backup_id)
        if result.get('success'):
            return jsonify({"success": True, "message": "备份删除成功"})
        else:
            return jsonify({"error": result.get('error', '删除失败')}), 500
    except Exception as e:
        logger.error(f"删除备份失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/<backup_id>/status')
def get_backup_status(backup_id):
    """获取备份状态"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        status = openstack_client.get_backup_status(backup_id)
        if status:
            return jsonify(status)
        else:
            return jsonify({"error": "备份不存在"}), 404
    except Exception as e:
        logger.error(f"获取备份状态失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/<backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """从备份恢复云硬盘"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json() or {}
        volume_id = data.get('volume_id')
        name = data.get('name')
        
        result = openstack_client.restore_backup(backup_id, volume_id, name)
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": "备份恢复成功",
                "volume_id": result.get('id'),
                "volume_name": result.get('name')
            })
        else:
            return jsonify({"error": result.get('error', '恢复失败')}), 500
    except Exception as e:
        logger.error(f"备份恢复失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/<backup_id>/export')
def export_backup(backup_id):
    """导出备份"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        result = openstack_client.get_backup_export_record(backup_id)
        if result.get('success'):
            return jsonify({
                "success": True,
                "backup_service": result.get('backup_service'),
                "backup_url": result.get('backup_url')
            })
        else:
            return jsonify({"error": result.get('error', '导出失败')}), 500
    except Exception as e:
        logger.error(f"备份导出失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/backup/import', methods=['POST'])
def import_backup():
    """导入备份"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json()
        backup_service = data.get('backup_service')
        backup_url = data.get('backup_url')
        name = data.get('name')
        
        if not backup_service or not backup_url:
            return jsonify({"error": "缺少必要的参数"}), 400
        
        result = openstack_client.import_backup(backup_service, backup_url, name)
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": "备份导入成功",
                "backup_id": result.get('id'),
                "backup_name": result.get('name')
            })
        else:
            return jsonify({"error": result.get('error', '导入失败')}), 500
    except Exception as e:
        logger.error(f"备份导入失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """健康检查"""
    try:
        if openstack_client:
            # 尝试获取云硬盘列表来测试连接
            volumes = openstack_client.get_volumes()
            return jsonify({
                "status": "healthy",
                "openstack_connected": True,
                "openstack_version": "28.4.1",
                "volume_count": len(volumes)
            })
        else:
            return jsonify({
                "status": "unhealthy",
                "openstack_connected": False,
                "openstack_version": "28.4.1",
                "error": "OpenStack连接失败"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "openstack_connected": False,
            "openstack_version": "28.4.1",
            "error": str(e)
        }), 500

@app.route('/api/info')
def get_system_info():
    """获取系统信息"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        volumes = openstack_client.get_volumes()
        backups = openstack_client.get_backups()
        
        # 统计信息
        volume_stats = {
            "total": len(volumes),
            "available": len([v for v in volumes if v['status'] == 'available']),
            "in_use": len([v for v in volumes if v['status'] == 'in-use']),
            "error": len([v for v in volumes if v['status'] == 'error'])
        }
        
        backup_stats = {
            "total": len(backups),
            "full": len([b for b in backups if not b['is_incremental']]),
            "incremental": len([b for b in backups if b['is_incremental']]),
            "available": len([b for b in backups if b['status'] == 'available']),
            "creating": len([b for b in backups if b['status'] == 'creating']),
            "error": len([b for b in backups if b['status'] == 'error'])
        }
        
        return jsonify({
            "openstack_version": "28.4.1",
            "volume_stats": volume_stats,
            "backup_stats": backup_stats,
            "retention_policy": {
                "full_backup_retention": Config.FULL_BACKUP_RETENTION,
                "incremental_backup_retention": Config.INCREMENTAL_BACKUP_RETENTION
            }
        })
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules/<schedule_id>/volumes', methods=['POST'])
def add_volumes_to_schedule(schedule_id):
    """为定时备份添加云硬盘"""
    try:
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        
        if not volume_ids:
            return jsonify({"error": "请选择要添加的云硬盘"}), 400
        
        schedules = load_schedules()
        schedule = None
        
        for s in schedules:
            if s['id'] == schedule_id:
                schedule = s
                # 添加新的云硬盘ID（避免重复）
                existing_ids = set(schedule['volume_ids'])
                new_ids = [vid for vid in volume_ids if vid not in existing_ids]
                schedule['volume_ids'].extend(new_ids)
                break
        
        if not schedule:
            return jsonify({"error": "定时备份不存在"}), 404
        
        if save_schedules(schedules):
            return jsonify({
                "success": True,
                "message": f"成功添加 {len(new_ids)} 个云硬盘到定时备份",
                "added_count": len(new_ids),
                "total_volumes": len(schedule['volume_ids'])
            })
        else:
            return jsonify({"error": "保存定时备份配置失败"}), 500
            
    except Exception as e:
        logger.error(f"添加云硬盘到定时备份失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules/<schedule_id>/volumes', methods=['DELETE'])
def remove_volumes_from_schedule(schedule_id):
    """从定时备份移除云硬盘"""
    try:
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        
        if not volume_ids:
            return jsonify({"error": "请选择要移除的云硬盘"}), 400
        
        schedules = load_schedules()
        schedule = None
        
        for s in schedules:
            if s['id'] == schedule_id:
                schedule = s
                # 移除指定的云硬盘ID
                original_count = len(schedule['volume_ids'])
                schedule['volume_ids'] = [vid for vid in schedule['volume_ids'] if vid not in volume_ids]
                removed_count = original_count - len(schedule['volume_ids'])
                break
        
        if not schedule:
            return jsonify({"error": "定时备份不存在"}), 404
        
        if save_schedules(schedules):
            return jsonify({
                "success": True,
                "message": f"成功移除 {removed_count} 个云硬盘",
                "removed_count": removed_count,
                "total_volumes": len(schedule['volume_ids'])
            })
        else:
            return jsonify({"error": "保存定时备份配置失败"}), 500
            
    except Exception as e:
        logger.error(f"从定时备份移除云硬盘失败: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG) 