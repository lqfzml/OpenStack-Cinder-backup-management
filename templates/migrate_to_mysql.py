#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从JSON文件迁移到MySQL数据库的脚本
"""

import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def migrate_from_json():
    """从JSON文件迁移到MySQL数据库"""
    try:
        # 检查JSON文件是否存在
        json_file = 'backup_schedules.json'
        if not os.path.exists(json_file):
            print(f"✅ 未找到 {json_file} 文件，无需迁移")
            return True
        
        print(f"📁 发现 {json_file} 文件，开始迁移...")
        
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            schedules = json.load(f)
        
        if not schedules:
            print("✅ JSON文件中没有数据，无需迁移")
            return True
        
        print(f"📊 发现 {len(schedules)} 个定时备份配置")
        
        # 导入数据库模块
        from database import get_db_manager
        db_manager = get_db_manager()
        
        # 迁移每个定时备份配置
        success_count = 0
        for schedule in schedules:
            try:
                # 确保必要字段存在
                if 'id' not in schedule:
                    schedule['id'] = f"migrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                if 'name' not in schedule:
                    schedule['name'] = f"迁移的定时备份 {schedule['id']}"
                
                if 'created_at' not in schedule:
                    schedule['created_at'] = datetime.now().isoformat()
                
                # 保存到数据库
                if db_manager.save_schedule(schedule):
                    success_count += 1
                    print(f"✅ 迁移成功: {schedule.get('name', schedule['id'])}")
                else:
                    print(f"❌ 迁移失败: {schedule.get('name', schedule['id'])}")
                    
            except Exception as e:
                print(f"❌ 迁移异常: {schedule.get('name', schedule.get('id', 'unknown'))} - {e}")
        
        print(f"📈 迁移完成: {success_count}/{len(schedules)} 成功")
        
        if success_count > 0:
            # 备份原JSON文件
            backup_file = f"{json_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(json_file, backup_file)
            print(f"💾 原文件已备份为: {backup_file}")
            
            print("🎉 迁移完成！系统现在使用MySQL数据库存储")
            print("💡 建议在确认系统正常运行后删除备份文件")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 迁移过程发生错误: {e}")
        return False

def main():
    """主函数"""
    print("🔄 开始从JSON文件迁移到MySQL数据库...")
    print("=" * 50)
    
    # 检查数据库连接
    try:
        from database import get_db_manager
        db_manager = get_db_manager()
        print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("请确保MySQL服务正在运行，并且.env文件中的数据库配置正确")
        return False
    
    # 执行迁移
    if migrate_from_json():
        print("=" * 50)
        print("🎉 迁移成功完成！")
        print("💡 现在可以启动系统使用MySQL数据库了")
        return True
    else:
        print("=" * 50)
        print("❌ 迁移失败")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 