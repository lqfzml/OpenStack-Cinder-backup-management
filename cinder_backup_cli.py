#!/usr/bin/env python3
"""
OpenStack Cinder 备份管理命令行工具 - 适配OpenStack 28.4.1
支持全量备份、增量备份、备份恢复、导入导出和备份清理
"""

import argparse
import sys
import json
from datetime import datetime
from openstack_client import OpenStackClient
from config import Config

def print_json(data):
    """格式化输出JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

def print_table(headers, rows):
    """格式化输出表格"""
    if not rows:
        print("暂无数据")
        return
    
    # 计算每列的最大宽度
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width)
    
    # 打印表头
    header_line = " | ".join(header.ljust(width) for header, width in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    
    # 打印数据行
    for row in rows:
        row_line = " | ".join(str(cell).ljust(width) for cell, width in zip(row, col_widths))
        print(row_line)

def list_volumes(client):
    """列出云硬盘"""
    print("=== 云硬盘列表 (OpenStack 28.4.1) ===")
    volumes = client.get_volumes()
    
    if not volumes:
        print("暂无云硬盘")
        return
    
    headers = ["ID", "名称", "大小(GB)", "状态", "类型", "可用区", "可启动", "加密", "创建时间"]
    rows = []
    for volume in volumes:
        rows.append([
            volume['id'][:8] + "...",
            volume['name'] or "未命名",
            volume['size'],
            volume['status'],
            volume['volume_type'] or "默认",
            volume['availability_zone'] or "默认",
            "是" if volume['bootable'] else "否",
            "是" if volume['encrypted'] else "否",
            volume['created_at'][:19] if volume['created_at'] else "未知"
        ])
    
    print_table(headers, rows)

def list_backups(client):
    """列出备份"""
    print("=== 备份列表 (OpenStack 28.4.1) ===")
    backups = client.get_backups()
    
    if not backups:
        print("暂无备份")
        return
    
    headers = ["ID", "名称", "云硬盘ID", "类型", "大小(GB)", "状态", "可用区", "容器", "失败原因", "创建时间"]
    rows = []
    for backup in backups:
        rows.append([
            backup['id'][:8] + "...",
            backup['name'] or "未命名",
            backup['volume_id'][:8] + "...",
            "增量" if backup['is_incremental'] else "全量",
            backup['size'] or "未知",
            backup['status'],
            backup['availability_zone'] or "默认",
            backup['container'] or "默认",
            backup['fail_reason'] or "无",
            backup['created_at'][:19] if backup['created_at'] else "未知"
        ])
    
    print_table(headers, rows)

def create_backup(client, volume_id, backup_type, name=None):
    """创建备份"""
    print(f"=== 创建{backup_type}备份 (OpenStack 28.4.1) ===")
    print(f"云硬盘ID: {volume_id}")
    
    if backup_type == 'full':
        result = client.create_full_backup(volume_id, name)
    else:
        result = client.create_incremental_backup(volume_id, name)
    
    if result.get('success'):
        print(f"✅ 备份创建成功")
        print(f"备份ID: {result['id']}")
        print(f"备份名称: {result['name']}")
        print(f"状态: {result['status']}")
    else:
        print(f"❌ 备份创建失败: {result.get('error', '未知错误')}")
        sys.exit(1)

def cleanup_backups(client):
    """清理备份"""
    print("=== 执行备份清理 (OpenStack 28.4.1) ===")
    print(f"保留策略: 每个云硬盘保留 {Config.FULL_BACKUP_RETENTION} 个全量备份, {Config.INCREMENTAL_BACKUP_RETENTION} 个增量备份")
    
    result = client.cleanup_backups()
    
    if result.get('success'):
        print(f"✅ 备份清理完成")
        print(f"删除备份数量: {result.get('deleted_count', 0)}")
    else:
        print(f"❌ 备份清理失败: {result.get('error', '未知错误')}")
        sys.exit(1)

def delete_backup(client, backup_id):
    """删除备份"""
    print(f"=== 删除备份 (OpenStack 28.4.1) ===")
    print(f"备份ID: {backup_id}")
    
    result = client.delete_backup(backup_id)
    
    if result.get('success'):
        print("✅ 备份删除成功")
    else:
        print(f"❌ 备份删除失败: {result.get('error', '未知错误')}")
        sys.exit(1)

def get_backup_status(client, backup_id):
    """获取备份状态"""
    print(f"=== 备份状态 (OpenStack 28.4.1) ===")
    print(f"备份ID: {backup_id}")
    
    status = client.get_backup_status(backup_id)
    
    if status:
        print(f"备份名称: {status['name']}")
        print(f"状态: {status['status']}")
        print(f"类型: {'增量' if status['is_incremental'] else '全量'}")
        print(f"大小: {status['size']} GB")
        print(f"描述: {status['description'] or '无'}")
        print(f"失败原因: {status['fail_reason'] or '无'}")
        print(f"创建时间: {status['created_at']}")
    else:
        print("❌ 备份不存在或获取状态失败")
        sys.exit(1)

def restore_backup(client, backup_id, volume_id=None, name=None):
    """从备份恢复云硬盘"""
    print(f"=== 从备份恢复云硬盘 (OpenStack 28.4.1) ===")
    print(f"备份ID: {backup_id}")
    if volume_id:
        print(f"目标云硬盘ID: {volume_id}")
    if name:
        print(f"恢复名称: {name}")
    
    result = client.restore_backup(backup_id, volume_id, name)
    
    if result.get('success'):
        print("✅ 备份恢复成功")
        print(f"恢复的云硬盘ID: {result['id']}")
        print(f"恢复的云硬盘名称: {result['name']}")
        print(f"状态: {result['status']}")
    else:
        print(f"❌ 备份恢复失败: {result.get('error', '未知错误')}")
        sys.exit(1)

def export_backup(client, backup_id):
    """导出备份"""
    print(f"=== 导出备份 (OpenStack 28.4.1) ===")
    print(f"备份ID: {backup_id}")
    
    result = client.get_backup_export_record(backup_id)
    
    if result.get('success'):
        print("✅ 备份导出成功")
        print(f"备份服务: {result['backup_service']}")
        print(f"备份URL: {result['backup_url']}")
        print("\n📋 导出信息:")
        print(f"   cinder backup-export {backup_id}")
        print(f"   或使用以下信息导入:")
        print(f"   cinder backup-import {result['backup_service']} {result['backup_url']}")
    else:
        print(f"❌ 备份导出失败: {result.get('error', '未知错误')}")
        sys.exit(1)

def import_backup(client, backup_service, backup_url, name=None):
    """导入备份"""
    print(f"=== 导入备份 (OpenStack 28.4.1) ===")
    print(f"备份服务: {backup_service}")
    print(f"备份URL: {backup_url}")
    if name:
        print(f"导入名称: {name}")
    
    result = client.import_backup(backup_service, backup_url, name)
    
    if result.get('success'):
        print("✅ 备份导入成功")
        print(f"导入的备份ID: {result['id']}")
        print(f"导入的备份名称: {result['name']}")
        print(f"状态: {result['status']}")
    else:
        print(f"❌ 备份导入失败: {result.get('error', '未知错误')}")
        sys.exit(1)

def show_system_info(client):
    """显示系统信息"""
    print("=== 系统信息 (OpenStack 28.4.1) ===")
    
    volumes = client.get_volumes()
    backups = client.get_backups()
    
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
    
    print(f"OpenStack版本: 28.4.1")
    print(f"\n📊 云硬盘统计:")
    print(f"  总数: {volume_stats['total']}")
    print(f"  可用: {volume_stats['available']}")
    print(f"  使用中: {volume_stats['in_use']}")
    print(f"  错误: {volume_stats['error']}")
    
    print(f"\n📊 备份统计:")
    print(f"  总数: {backup_stats['total']}")
    print(f"  全量: {backup_stats['full']}")
    print(f"  增量: {backup_stats['incremental']}")
    print(f"  可用: {backup_stats['available']}")
    print(f"  创建中: {backup_stats['creating']}")
    print(f"  错误: {backup_stats['error']}")
    
    print(f"\n⚙️  保留策略:")
    print(f"  全量备份保留: {Config.FULL_BACKUP_RETENTION} 个")
    print(f"  增量备份保留: {Config.INCREMENTAL_BACKUP_RETENTION} 个")

def main():
    parser = argparse.ArgumentParser(description='OpenStack Cinder 备份管理工具 (28.4.1)')
    parser.add_argument('--config', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出资源')
    list_parser.add_argument('type', choices=['volumes', 'backups'], help='资源类型')
    
    # backup 命令
    backup_parser = subparsers.add_parser('backup', help='创建备份')
    backup_parser.add_argument('type', choices=['full', 'incremental'], help='备份类型')
    backup_parser.add_argument('volume_id', help='云硬盘ID')
    backup_parser.add_argument('--name', help='备份名称')
    
    # cleanup 命令
    subparsers.add_parser('cleanup', help='清理备份')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除备份')
    delete_parser.add_argument('backup_id', help='备份ID')
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='获取备份状态')
    status_parser.add_argument('backup_id', help='备份ID')
    
    # restore 命令
    restore_parser = subparsers.add_parser('restore', help='从备份恢复云硬盘')
    restore_parser.add_argument('backup_id', help='备份ID')
    restore_parser.add_argument('--volume-id', help='目标云硬盘ID')
    restore_parser.add_argument('--name', help='恢复后的云硬盘名称')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出备份')
    export_parser.add_argument('backup_id', help='备份ID')
    
    # import 命令
    import_parser = subparsers.add_parser('import', help='导入备份')
    import_parser.add_argument('backup_service', help='备份服务')
    import_parser.add_argument('backup_url', help='备份URL')
    import_parser.add_argument('--name', help='导入后的备份名称')
    
    # info 命令
    subparsers.add_parser('info', help='显示系统信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # 初始化OpenStack客户端
        client = OpenStackClient()
        
        if args.command == 'list':
            if args.type == 'volumes':
                list_volumes(client)
            elif args.type == 'backups':
                list_backups(client)
        
        elif args.command == 'backup':
            create_backup(client, args.volume_id, args.type, args.name)
        
        elif args.command == 'cleanup':
            cleanup_backups(client)
        
        elif args.command == 'delete':
            delete_backup(client, args.backup_id)
        
        elif args.command == 'status':
            get_backup_status(client, args.backup_id)
        
        elif args.command == 'restore':
            restore_backup(client, args.backup_id, args.volume_id, args.name)
        
        elif args.command == 'export':
            export_backup(client, args.backup_id)
        
        elif args.command == 'import':
            import_backup(client, args.backup_service, args.backup_url, args.name)
        
        elif args.command == 'info':
            show_system_info(client)
    
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 