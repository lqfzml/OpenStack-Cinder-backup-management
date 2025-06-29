from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging
import json
import os
from datetime import datetime, timedelta
from openstack_client import OpenStackClient
from config import Config
from database import get_db_manager

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

# 初始化数据库管理器
try:
    db_manager = get_db_manager()
except Exception as e:
    logger.error(f"初始化数据库管理器失败: {e}")
    db_manager = None

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
        if not db_manager:
            return jsonify({"error": "数据库连接失败"}), 500
        
        schedules = db_manager.load_schedules()
        return jsonify(schedules)
    except Exception as e:
        logger.error(f"获取定时备份列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    """创建定时备份"""
    try:
        if not db_manager:
            return jsonify({"error": "数据库连接失败"}), 500
        
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
            "created_at": datetime.now().isoformat()
        }
        
        if db_manager.save_schedule(new_schedule):
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
        if not db_manager:
            return jsonify({"error": "数据库连接失败"}), 500
        
        if db_manager.delete_schedule(schedule_id):
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
        if not db_manager:
            return jsonify({"error": "数据库连接失败"}), 500
        
        # 获取当前状态
        schedules = db_manager.load_schedules()
        current_schedule = None
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                current_schedule = schedule
                break
        
        if not current_schedule:
            return jsonify({"error": "定时备份不存在"}), 404
        
        new_enabled = not current_schedule.get('enabled', True)
        
        if db_manager.update_schedule_enabled(schedule_id, new_enabled):
            return jsonify({
                "success": True, 
                "message": f"定时备份已{'启用' if new_enabled else '禁用'}",
                "enabled": new_enabled
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
        
        info = openstack_client.get_system_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules/<schedule_id>/volumes', methods=['POST'])
def add_volumes_to_schedule(schedule_id):
    """为定时备份添加云硬盘"""
    try:
        if not db_manager:
            return jsonify({"error": "数据库连接失败"}), 500
        
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        
        if not volume_ids:
            return jsonify({"error": "请选择要添加的云硬盘"}), 400
        
        # 获取当前定时备份配置
        schedules = db_manager.load_schedules()
        current_schedule = None
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                current_schedule = schedule
                break
        
        if not current_schedule:
            return jsonify({"error": "定时备份不存在"}), 404
        
        # 添加新的云硬盘ID（避免重复）
        existing_ids = set(current_schedule['volume_ids'])
        new_ids = [vid for vid in volume_ids if vid not in existing_ids]
        updated_volume_ids = current_schedule['volume_ids'] + new_ids
        
        if db_manager.update_schedule_volumes(schedule_id, updated_volume_ids):
            return jsonify({
                "success": True,
                "message": f"成功添加 {len(new_ids)} 个云硬盘到定时备份",
                "added_count": len(new_ids),
                "total_volumes": len(updated_volume_ids)
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
        if not db_manager:
            return jsonify({"error": "数据库连接失败"}), 500
        
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        
        if not volume_ids:
            return jsonify({"error": "请选择要移除的云硬盘"}), 400
        
        # 获取当前定时备份配置
        schedules = db_manager.load_schedules()
        current_schedule = None
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                current_schedule = schedule
                break
        
        if not current_schedule:
            return jsonify({"error": "定时备份不存在"}), 404
        
        # 移除指定的云硬盘ID
        original_count = len(current_schedule['volume_ids'])
        updated_volume_ids = [vid for vid in current_schedule['volume_ids'] if vid not in volume_ids]
        removed_count = original_count - len(updated_volume_ids)
        
        if db_manager.update_schedule_volumes(schedule_id, updated_volume_ids):
            return jsonify({
                "success": True,
                "message": f"成功移除 {removed_count} 个云硬盘",
                "removed_count": removed_count,
                "total_volumes": len(updated_volume_ids)
            })
        else:
            return jsonify({"error": "保存定时备份配置失败"}), 500
            
    except Exception as e:
        logger.error(f"从定时备份移除云硬盘失败: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== 云主机快照API ====================

@app.route('/api/servers')
def get_servers():
    """获取云主机列表"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        servers = openstack_client.get_servers()
        return jsonify(servers)
    except Exception as e:
        logger.error(f"获取云主机列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/server-snapshots')
def get_server_snapshots():
    """获取云主机快照列表"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        snapshots = openstack_client.get_server_snapshots()
        return jsonify(snapshots)
    except Exception as e:
        logger.error(f"获取云主机快照列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/server-snapshots', methods=['POST'])
def create_server_snapshot():
    """创建云主机快照"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json()
        server_ids = data.get('server_ids', [])
        name = data.get('name')
        description = data.get('description')
        
        if not server_ids:
            return jsonify({"error": "请选择要创建快照的云主机"}), 400
        
        results = []
        for server_id in server_ids:
            result = openstack_client.create_server_snapshot(server_id, name, description)
            results.append(result)
        
        success_count = sum(1 for r in results if r.get('success'))
        return jsonify({
            "success": success_count > 0,
            "results": results,
            "message": f"成功创建 {success_count} 个云主机快照"
        })
    except Exception as e:
        logger.error(f"创建云主机快照失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/server-snapshots/<snapshot_id>', methods=['DELETE'])
def delete_server_snapshot(snapshot_id):
    """删除云主机快照"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        result = openstack_client.delete_server_snapshot(snapshot_id)
        if result.get('success'):
            return jsonify({"success": True, "message": "云主机快照删除成功"})
        else:
            return jsonify({"error": result.get('error', '删除失败')}), 500
    except Exception as e:
        logger.error(f"删除云主机快照失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/server-snapshots/cleanup', methods=['POST'])
def cleanup_server_snapshots():
    """清理云主机快照"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json()
        retention_days = data.get('retention_days', 30)
        
        if not isinstance(retention_days, int) or retention_days < 1 or retention_days > 365:
            return jsonify({"error": "保留天数必须在1-365之间"}), 400
        
        result = openstack_client.cleanup_server_snapshots(retention_days)
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": f"云主机快照清理完成，删除了 {result.get('deleted_count', 0)} 个超过 {retention_days} 天的快照",
                "deleted_count": result.get('deleted_count', 0),
                "retention_days": retention_days
            })
        else:
            return jsonify({"error": result.get('error', '清理失败')}), 500
    except Exception as e:
        logger.error(f"清理云主机快照失败: {e}")
        return jsonify({"error": str(e)}), 500

# ==================== 云硬盘快照API ====================

@app.route('/api/volume-snapshots')
def get_volume_snapshots():
    """获取云硬盘快照列表"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        snapshots = openstack_client.get_volume_snapshots()
        return jsonify(snapshots)
    except Exception as e:
        logger.error(f"获取云硬盘快照列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/volume-snapshots', methods=['POST'])
def create_volume_snapshot():
    """创建云硬盘快照"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json()
        volume_ids = data.get('volume_ids', [])
        name = data.get('name')
        description = data.get('description')
        force = data.get('force', False)
        
        if not volume_ids:
            return jsonify({"error": "请选择要创建快照的云硬盘"}), 400
        
        results = []
        for volume_id in volume_ids:
            result = openstack_client.create_volume_snapshot(volume_id, name, description, force)
            results.append(result)
        
        success_count = sum(1 for r in results if r.get('success'))
        return jsonify({
            "success": success_count > 0,
            "results": results,
            "message": f"成功创建 {success_count} 个云硬盘快照"
        })
    except Exception as e:
        logger.error(f"创建云硬盘快照失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/volume-snapshots/<snapshot_id>', methods=['DELETE'])
def delete_volume_snapshot(snapshot_id):
    """删除云硬盘快照"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        result = openstack_client.delete_volume_snapshot(snapshot_id)
        if result.get('success'):
            return jsonify({"success": True, "message": "云硬盘快照删除成功"})
        else:
            return jsonify({"error": result.get('error', '删除失败')}), 500
    except Exception as e:
        logger.error(f"删除云硬盘快照失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/volume-snapshots/cleanup', methods=['POST'])
def cleanup_volume_snapshots():
    """清理云硬盘快照"""
    try:
        if not openstack_client:
            return jsonify({"error": "OpenStack连接失败"}), 500
        
        data = request.get_json()
        retention_days = data.get('retention_days', 30)
        
        if not isinstance(retention_days, int) or retention_days < 1 or retention_days > 365:
            return jsonify({"error": "保留天数必须在1-365之间"}), 400
        
        result = openstack_client.cleanup_volume_snapshots(retention_days)
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": f"云硬盘快照清理完成，删除了 {result.get('deleted_count', 0)} 个超过 {retention_days} 天的快照",
                "deleted_count": result.get('deleted_count', 0),
                "retention_days": retention_days
            })
        else:
            return jsonify({"error": result.get('error', '清理失败')}), 500
    except Exception as e:
        logger.error(f"清理云硬盘快照失败: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG) 