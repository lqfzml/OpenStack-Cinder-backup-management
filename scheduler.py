#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时备份任务执行器
支持每日和每周定时备份
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from openstack_client import OpenStackClient
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupScheduler:
    def __init__(self):
        self.schedule_file = 'backup_schedules.json'
        self.openstack_client = None
        self._init_openstack_client()
    
    def _init_openstack_client(self):
        """初始化OpenStack客户端"""
        try:
            self.openstack_client = OpenStackClient()
            logger.info("OpenStack客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenStack客户端初始化失败: {e}")
            self.openstack_client = None
    
    def load_schedules(self):
        """加载定时备份配置"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载定时备份配置失败: {e}")
        return []
    
    def save_schedules(self, schedules):
        """保存定时备份配置"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存定时备份配置失败: {e}")
            return False
    
    def should_run_schedule(self, schedule):
        """判断定时任务是否应该执行"""
        if not schedule.get('enabled', True):
            return False
        
        now = datetime.now()
        schedule_time = schedule.get('schedule_time', '02:00')
        
        try:
            hour, minute = map(int, schedule_time.split(':'))
            schedule_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            logger.error(f"无效的时间格式: {schedule_time}")
            return False
        
        # 检查是否是每日执行
        if schedule.get('schedule_type') == 'daily':
            # 如果当前时间接近计划时间（前后5分钟内），则执行
            time_diff = abs((now - schedule_datetime).total_seconds())
            return time_diff <= 300  # 5分钟 = 300秒
        
        # 检查是否是每周执行
        elif schedule.get('schedule_type') == 'weekly':
            weekdays = schedule.get('weekdays', [])
            if not weekdays:
                return False
            
            # 检查今天是否是计划中的星期
            current_weekday = now.isoweekday()  # 1=周一, 7=周日
            if current_weekday not in weekdays:
                return False
            
            # 检查时间是否接近
            time_diff = abs((now - schedule_datetime).total_seconds())
            return time_diff <= 300  # 5分钟 = 300秒
        
        return False
    
    def execute_schedule(self, schedule):
        """执行定时备份任务"""
        if not self.openstack_client:
            logger.error("OpenStack客户端未初始化，无法执行备份")
            return False
        
        try:
            volume_ids = schedule.get('volume_ids', [])
            backup_type = schedule.get('backup_type', 'full')
            schedule_name = schedule.get('name', '')
            
            if not volume_ids:
                logger.warning(f"定时备份 {schedule.get('id')} 没有选择云硬盘")
                return False
            
            logger.info(f"开始执行定时备份: {schedule_name} ({backup_type})")
            
            success_count = 0
            for volume_id in volume_ids:
                try:
                    # 获取云硬盘信息以生成备份名称
                    volume_info = None
                    try:
                        volume = self.openstack_client.conn.block_storage.get_volume(volume_id)
                        volume_info = {
                            'name': volume.name or 'unnamed',
                            'id': volume.id
                        }
                    except:
                        volume_info = {'name': 'unknown', 'id': volume_id}
                    
                    # 生成备份名称：云硬盘名称-backup-云硬盘ID-时间戳
                    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M')
                    backup_name = f"{volume_info['name']}-backup-{volume_info['id']}-{current_time}"
                    
                    if backup_type == 'full':
                        result = self.openstack_client.create_full_backup(volume_id, backup_name)
                    else:
                        result = self.openstack_client.create_incremental_backup(volume_id, backup_name)
                    
                    if result.get('success'):
                        success_count += 1
                        logger.info(f"云硬盘 {volume_info['name']} ({volume_id}) 备份创建成功: {result.get('id')}")
                    else:
                        logger.error(f"云硬盘 {volume_info['name']} ({volume_id}) 备份创建失败: {result.get('error')}")
                
                except Exception as e:
                    logger.error(f"云硬盘 {volume_id} 备份创建异常: {e}")
            
            logger.info(f"定时备份执行完成: {success_count}/{len(volume_ids)} 成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"执行定时备份失败: {e}")
            return False
    
    def update_schedule_last_run(self, schedule_id):
        """更新定时任务最后执行时间"""
        schedules = self.load_schedules()
        for schedule in schedules:
            if schedule.get('id') == schedule_id:
                schedule['last_run'] = datetime.now().isoformat()
                break
        
        self.save_schedules(schedules)
    
    def run(self):
        """运行定时任务调度器"""
        logger.info("定时备份调度器启动")
        
        while True:
            try:
                schedules = self.load_schedules()
                
                for schedule in schedules:
                    if self.should_run_schedule(schedule):
                        logger.info(f"执行定时备份: {schedule.get('name', schedule.get('id'))}")
                        
                        if self.execute_schedule(schedule):
                            self.update_schedule_last_run(schedule.get('id'))
                            logger.info(f"定时备份执行成功: {schedule.get('name', schedule.get('id'))}")
                        else:
                            logger.error(f"定时备份执行失败: {schedule.get('name', schedule.get('id'))}")
                
                # 每分钟检查一次
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("定时备份调度器停止")
                break
            except Exception as e:
                logger.error(f"定时备份调度器异常: {e}")
                time.sleep(60)  # 发生异常时等待1分钟后继续

def main():
    """主函数"""
    scheduler = BackupScheduler()
    scheduler.run()

if __name__ == '__main__':
    main() 