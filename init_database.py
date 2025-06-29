#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据库初始化脚本
用于创建数据库、用户和表结构
"""

import mysql.connector
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def init_database():
    """初始化数据库"""
    try:
        # 连接MySQL服务器（使用root用户）
        root_password = os.getenv('MYSQL_ROOT_PASSWORD', '')
        if not root_password:
            print("错误: 请设置 MYSQL_ROOT_PASSWORD 环境变量")
            return False
        
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            user='root',
            password=root_password,
            charset=os.getenv('MYSQL_CHARSET', 'utf8mb4')
        )
        
        cursor = connection.cursor()
        
        # 创建数据库
        database = os.getenv('MYSQL_DATABASE', 'cinder_backup_db')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"数据库 {database} 创建成功")
        
        # 创建用户
        user = os.getenv('MYSQL_USER', 'cinder_backup')
        password = os.getenv('MYSQL_PASSWORD', 'cinder_backup_pass')
        
        cursor.execute(f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{password}'")
        print(f"用户 {user} 创建成功")
        
        # 授权
        cursor.execute(f"GRANT ALL PRIVILEGES ON {database}.* TO '{user}'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        print(f"用户 {user} 授权成功")
        
        cursor.close()
        connection.close()
        
        print("数据库初始化完成！")
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

def create_tables():
    """创建表结构"""
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        print("表结构创建成功！")
        return True
        
    except Exception as e:
        print(f"表结构创建失败: {e}")
        return False

def main():
    """主函数"""
    print("开始初始化MySQL数据库...")
    
    # 初始化数据库和用户
    if not init_database():
        sys.exit(1)
    
    # 创建表结构
    if not create_tables():
        sys.exit(1)
    
    print("MySQL数据库初始化完成！")
    print("\n请确保在 .env 文件中配置了正确的数据库连接信息：")
    print("MYSQL_HOST=localhost")
    print("MYSQL_PORT=3306")
    print("MYSQL_USER=cinder_backup")
    print("MYSQL_PASSWORD=cinder_backup_pass")
    print("MYSQL_DATABASE=cinder_backup_db")

if __name__ == '__main__':
    main() 