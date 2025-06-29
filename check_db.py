#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库状态检查脚本
"""

import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def check_database():
    """检查数据库状态"""
    try:
        from database import get_db_manager
        db_manager = get_db_manager()
        
        print("✅ 数据库连接正常")
        
        # 检查表结构
        connection = db_manager.get_connection()
        cursor = connection.cursor()
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📊 数据库表: {', '.join(tables)}")
        
        # 检查定时备份数量
        schedules = db_manager.load_schedules()
        print(f"⏰ 定时备份配置: {len(schedules)} 个")
        
        # 检查备份历史数量
        history = db_manager.get_backup_history(limit=1000)
        print(f"📋 备份历史记录: {len(history)} 条")
        
        cursor.close()
        
        print("🎉 数据库状态检查完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库状态检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🔍 检查数据库状态...")
    print("=" * 40)
    
    if check_database():
        print("=" * 40)
        print("✅ 数据库状态正常")
        return True
    else:
        print("=" * 40)
        print("❌ 数据库状态异常")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 