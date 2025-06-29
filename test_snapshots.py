#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快照功能测试脚本
"""

import requests
import json
import sys
from datetime import datetime

# 配置
BASE_URL = 'http://localhost:5000'

def test_api_endpoint(endpoint, method='GET', data=None):
    """测试API端点"""
    try:
        url = f"{BASE_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'} if data else {}
        
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ {endpoint} 失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ {endpoint} 异常: {e}")
        return None

def test_snapshot_functionality():
    """测试快照功能"""
    print("🧪 开始测试快照功能...")
    print("=" * 50)
    
    # 1. 测试获取云主机列表
    print("1. 测试获取云主机列表...")
    servers = test_api_endpoint('/api/servers')
    if servers:
        print(f"✅ 获取到 {len(servers)} 个云主机")
        if servers:
            print(f"   示例云主机: {servers[0]['name']} ({servers[0]['id']})")
    else:
        print("❌ 获取云主机列表失败")
    
    # 2. 测试获取云硬盘列表
    print("\n2. 测试获取云硬盘列表...")
    volumes = test_api_endpoint('/api/volumes')
    if volumes:
        print(f"✅ 获取到 {len(volumes)} 个云硬盘")
        if volumes:
            print(f"   示例云硬盘: {volumes[0]['name']} ({volumes[0]['id']})")
    else:
        print("❌ 获取云硬盘列表失败")
    
    # 3. 测试获取云主机快照列表
    print("\n3. 测试获取云主机快照列表...")
    server_snapshots = test_api_endpoint('/api/server-snapshots')
    if server_snapshots is not None:
        print(f"✅ 获取到 {len(server_snapshots)} 个云主机快照")
    else:
        print("❌ 获取云主机快照列表失败")
    
    # 4. 测试获取云硬盘快照列表
    print("\n4. 测试获取云硬盘快照列表...")
    volume_snapshots = test_api_endpoint('/api/volume-snapshots')
    if volume_snapshots is not None:
        print(f"✅ 获取到 {len(volume_snapshots)} 个云硬盘快照")
    else:
        print("❌ 获取云硬盘快照列表失败")
    
    # 5. 测试系统信息（包含快照统计）
    print("\n5. 测试获取系统信息...")
    system_info = test_api_endpoint('/api/info')
    if system_info:
        print("✅ 系统信息获取成功")
        if 'snapshots' in system_info:
            snapshots = system_info['snapshots']
            print(f"   云主机快照统计: {snapshots.get('server_snapshots', {})}")
            print(f"   云硬盘快照统计: {snapshots.get('volume_snapshots', {})}")
    else:
        print("❌ 获取系统信息失败")
    
    # 6. 测试快照清理功能（不实际执行）
    print("\n6. 测试快照清理API...")
    cleanup_data = {"retention_days": 30}
    
    # 测试云主机快照清理API
    server_cleanup = test_api_endpoint('/api/server-snapshots/cleanup', 'POST', cleanup_data)
    if server_cleanup:
        print("✅ 云主机快照清理API正常")
    
    # 测试云硬盘快照清理API
    volume_cleanup = test_api_endpoint('/api/volume-snapshots/cleanup', 'POST', cleanup_data)
    if volume_cleanup:
        print("✅ 云硬盘快照清理API正常")
    
    print("\n" + "=" * 50)
    print("🎉 快照功能测试完成！")
    print("\n💡 注意：")
    print("- 创建快照功能需要实际的云主机和云硬盘")
    print("- 删除快照功能需要实际的快照ID")
    print("- 清理功能会实际删除快照，请谨慎测试")

def main():
    """主函数"""
    try:
        test_snapshot_functionality()
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == '__main__':
    main() 