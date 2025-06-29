#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据库模型和操作
"""

import mysql.connector
import json
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.connection = None
        self._connect()
        self._init_database()
    
    def _connect(self):
        """连接MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                charset=self.config.MYSQL_CHARSET,
                autocommit=True
            )
            logger.info("MySQL数据库连接成功")
        except Exception as e:
            logger.error(f"MySQL数据库连接失败: {e}")
            raise
    
    def _init_database(self):
        """初始化数据库和表结构"""
        try:
            cursor = self.connection.cursor()
            
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config.MYSQL_DATABASE}")
            cursor.execute(f"USE {self.config.MYSQL_DATABASE}")
            
            # 创建定时备份表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_schedules (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    backup_type ENUM('full', 'incremental') NOT NULL DEFAULT 'full',
                    schedule_type ENUM('daily', 'weekly') NOT NULL DEFAULT 'weekly',
                    schedule_time TIME NOT NULL DEFAULT '02:00:00',
                    weekdays JSON,
                    volume_ids JSON NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_run TIMESTAMP NULL,
                    next_run TIMESTAMP NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            cursor.close()
            logger.info("数据库表结构初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def load_schedules(self):
        """加载所有定时备份配置"""
        try:
            cursor = self.get_connection().cursor(dictionary=True)
            cursor.execute("SELECT * FROM backup_schedules ORDER BY created_at DESC")
            
            schedules = []
            for row in cursor.fetchall():
                schedule = {
                    'id': row['id'],
                    'name': row['name'],
                    'backup_type': row['backup_type'],
                    'schedule_type': row['schedule_type'],
                    'schedule_time': str(row['schedule_time']),
                    'weekdays': json.loads(row['weekdays']) if row['weekdays'] else [],
                    'volume_ids': json.loads(row['volume_ids']),
                    'enabled': bool(row['enabled']),
                    'created_at': row['created_at'].isoformat(),
                    'last_run': row['last_run'].isoformat() if row['last_run'] else None,
                    'next_run': row['next_run'].isoformat() if row['next_run'] else None
                }
                schedules.append(schedule)
            
            cursor.close()
            return schedules
            
        except Exception as e:
            logger.error(f"加载定时备份配置失败: {e}")
            return []
    
    def save_schedule(self, schedule):
        """保存单个定时备份配置"""
        try:
            cursor = self.get_connection().cursor()
            
            cursor.execute("""
                INSERT INTO backup_schedules 
                (id, name, backup_type, schedule_type, schedule_time, weekdays, volume_ids, enabled, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                backup_type = VALUES(backup_type),
                schedule_type = VALUES(schedule_type),
                schedule_time = VALUES(schedule_time),
                weekdays = VALUES(weekdays),
                volume_ids = VALUES(volume_ids),
                enabled = VALUES(enabled),
                updated_at = CURRENT_TIMESTAMP
            """, (
                schedule['id'],
                schedule['name'],
                schedule['backup_type'],
                schedule['schedule_type'],
                schedule['schedule_time'],
                json.dumps(schedule['weekdays']),
                json.dumps(schedule['volume_ids']),
                schedule['enabled'],
                schedule['created_at']
            ))
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"保存定时备份配置失败: {e}")
            return False
    
    def delete_schedule(self, schedule_id):
        """删除定时备份配置"""
        try:
            cursor = self.get_connection().cursor()
            cursor.execute("DELETE FROM backup_schedules WHERE id = %s", (schedule_id,))
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"删除定时备份配置失败: {e}")
            return False
    
    def update_schedule_enabled(self, schedule_id, enabled):
        """更新定时备份启用状态"""
        try:
            cursor = self.get_connection().cursor()
            cursor.execute("""
                UPDATE backup_schedules 
                SET enabled = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (enabled, schedule_id))
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"更新定时备份状态失败: {e}")
            return False
    
    def update_schedule_volumes(self, schedule_id, volume_ids):
        """更新定时备份的云硬盘列表"""
        try:
            cursor = self.get_connection().cursor()
            cursor.execute("""
                UPDATE backup_schedules 
                SET volume_ids = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (json.dumps(volume_ids), schedule_id))
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"更新定时备份云硬盘列表失败: {e}")
            return False
    
    def get_connection(self):
        """获取数据库连接"""
        if not self.connection or not self.connection.is_connected():
            self._connect()
        return self.connection
    
    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")

# 全局数据库管理器实例
db_manager = None

def get_db_manager():
    """获取数据库管理器实例"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager 