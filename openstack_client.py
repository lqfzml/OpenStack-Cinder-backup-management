import openstack
from openstack import connection
from collections import defaultdict
from datetime import datetime
import logging
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenStackClient:
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        """建立OpenStack连接 - 适配OpenStack 28.4.1"""
        try:
            auth_args = {
                "auth_url": Config.OS_AUTH_URL,
                "project_name": Config.OS_PROJECT_NAME,
                "username": Config.OS_USERNAME,
                "password": Config.OS_PASSWORD,
                "user_domain_name": Config.OS_USER_DOMAIN_NAME,
                "project_domain_name": Config.OS_PROJECT_DOMAIN_NAME,
                "identity_api_version": "3",  # 明确指定API版本
                "volume_api_version": "3"     # 明确指定Cinder API版本
            }
            self.conn = connection.Connection(**auth_args)
            logger.info("OpenStack 28.4.1连接成功")
        except Exception as e:
            logger.error(f"OpenStack连接失败: {e}")
            raise
    
    def get_volumes(self):
        """获取所有云硬盘 - 适配OpenStack 28.4.1"""
        try:
            volumes = []
            # 使用新的API调用方式
            for volume in self.conn.block_storage.volumes(details=True):
                volumes.append({
                    "id": volume.id,
                    "name": volume.name,
                    "size": volume.size,
                    "status": volume.status,
                    "created_at": volume.created_at,
                    "description": getattr(volume, 'description', ''),
                    "volume_type": getattr(volume, 'volume_type', ''),
                    "availability_zone": getattr(volume, 'availability_zone', ''),
                    "bootable": getattr(volume, 'bootable', False),
                    "encrypted": getattr(volume, 'encrypted', False)
                })
            return volumes
        except Exception as e:
            logger.error(f"获取云硬盘列表失败: {e}")
            return []
    
    def get_backups(self):
        """获取所有备份 - 适配OpenStack 28.4.1，根据描述判断备份类型"""
        try:
            backups = []
            # 使用新的API调用方式
            for backup in self.conn.block_storage.backups(details=True):
                description = getattr(backup, "description", "")
                is_incremental = getattr(backup, "is_incremental", False)
                
                # 根据描述判断备份类型
                backup_type = "unknown"
                if description:
                    if "Full backup" in description or "full backup" in description.lower():
                        backup_type = "full"
                    elif "Incremental backup" in description or "incremental backup" in description.lower():
                        backup_type = "incremental"
                    else:
                        # 如果描述中没有明确标识，则使用API的is_incremental字段
                        backup_type = "incremental" if is_incremental else "full"
                else:
                    # 如果描述为空，则使用API的is_incremental字段
                    backup_type = "incremental" if is_incremental else "full"
                
                backups.append({
                    "id": backup.id,
                    "name": backup.name,
                    "volume_id": backup.volume_id,
                    "status": backup.status,
                    "created_at": backup.created_at,
                    "is_incremental": is_incremental,
                    "backup_type": backup_type,  # 新增字段：根据描述判断的备份类型
                    "size": getattr(backup, "size", 0),
                    "description": description,
                    "availability_zone": getattr(backup, "availability_zone", ""),
                    "container": getattr(backup, "container", ""),
                    "fail_reason": getattr(backup, "fail_reason", ""),
                    "has_dependent_backups": getattr(backup, "has_dependent_backups", False),
                    "snapshot_id": getattr(backup, "snapshot_id", None),
                    "data_timestamp": getattr(backup, "data_timestamp", None)
                })
            return backups
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            return []
    
    def create_full_backup(self, volume_id, name=None):
        """创建全量备份 - 适配OpenStack 28.4.1"""
        try:
            if not name:
                name = f"full-backup-{volume_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # 使用新的备份创建API
            backup = self.conn.block_storage.create_backup(
                volume_id=volume_id,
                name=name,
                force=True,
                incremental=False,
                description=f"Full backup created at {datetime.now().isoformat()}"
            )
            logger.info(f"全量备份创建成功: {backup.id}")
            return {
                "id": backup.id,
                "name": backup.name,
                "status": backup.status,
                "success": True
            }
        except Exception as e:
            logger.error(f"创建全量备份失败: {e}")
            return {"success": False, "error": str(e)}
    
    def create_incremental_backup(self, volume_id, name=None):
        """创建增量备份 - 适配OpenStack 28.4.1"""
        try:
            if not name:
                name = f"incr-backup-{volume_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # 使用新的备份创建API
            backup = self.conn.block_storage.create_backup(
                volume_id=volume_id,
                name=name,
                force=True,
                incremental=True,
                description=f"Incremental backup created at {datetime.now().isoformat()}"
            )
            logger.info(f"增量备份创建成功: {backup.id}")
            return {
                "id": backup.id,
                "name": backup.name,
                "status": backup.status,
                "success": True
            }
        except Exception as e:
            logger.error(f"创建增量备份失败: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_backup(self, backup_id):
        """删除备份 - 适配OpenStack 28.4.1"""
        try:
            # 使用新的删除API
            self.conn.block_storage.delete_backup(backup_id, ignore_missing=True, force=False)
            logger.info(f"备份删除成功: {backup_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_backups(self, retention_days=30):
        """清理备份策略 - 适配OpenStack 28.4.1，支持自定义保留天数"""
        try:
            all_backups = self.get_backups()
            current_time = datetime.now()
            deleted_count = 0
            
            for backup in all_backups:
                try:
                    # 解析备份创建时间
                    backup_time = datetime.fromisoformat(backup["created_at"].replace('Z', '+00:00'))
                    # 计算备份天数
                    days_old = (current_time - backup_time).days
                    
                    # 如果备份超过指定天数，则删除
                    if days_old > retention_days:
                        result = self.delete_backup(backup["id"])
                        if result["success"]:
                            deleted_count += 1
                            logger.info(f"删除过期备份: {backup['name']} (创建于 {days_old} 天前，超过 {retention_days} 天保留期)")
                        else:
                            logger.error(f"删除过期备份失败: {backup['id']} - {result.get('error')}")
                except Exception as e:
                    logger.error(f"处理备份 {backup.get('id')} 时出错: {e}")
                    continue
            
            logger.info(f"备份清理完成，共删除 {deleted_count} 个超过 {retention_days} 天的过期备份")
            return {"success": True, "deleted_count": deleted_count, "retention_days": retention_days}
        except Exception as e:
            logger.error(f"备份清理失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_backup_status(self, backup_id):
        """获取备份状态 - 适配OpenStack 28.4.1"""
        try:
            backup = self.conn.block_storage.get_backup(backup_id)
            return {
                "id": backup.id,
                "name": backup.name,
                "status": backup.status,
                "created_at": backup.created_at,
                "is_incremental": getattr(backup, "is_incremental", False),
                "size": getattr(backup, "size", 0),
                "description": getattr(backup, "description", ""),
                "fail_reason": getattr(backup, "fail_reason", "")
            }
        except Exception as e:
            logger.error(f"获取备份状态失败: {e}")
            return None
    
    def restore_backup(self, backup_id, volume_id=None, name=None):
        """从备份恢复云硬盘 - 适配OpenStack 28.4.1"""
        try:
            if not name:
                name = f"restored-volume-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # 使用新的恢复API
            restored_volume = self.conn.block_storage.restore_backup(
                backup_id,
                volume_id=volume_id,
                name=name
            )
            logger.info(f"备份恢复成功: {restored_volume.id}")
            return {
                "id": restored_volume.id,
                "name": restored_volume.name,
                "status": restored_volume.status,
                "success": True
            }
        except Exception as e:
            logger.error(f"备份恢复失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_backup_export_record(self, backup_id):
        """获取备份导出记录 - 适配OpenStack 28.4.1"""
        try:
            export_record = self.conn.block_storage.get_backup_export_record(backup_id)
            return {
                "backup_service": export_record.backup_service,
                "backup_url": export_record.backup_url,
                "success": True
            }
        except Exception as e:
            logger.error(f"获取备份导出记录失败: {e}")
            return {"success": False, "error": str(e)}
    
    def import_backup(self, backup_service, backup_url, name=None):
        """导入备份 - 适配OpenStack 28.4.1"""
        try:
            if not name:
                name = f"imported-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            imported_backup = self.conn.block_storage.import_backup(
                backup_service,
                backup_url,
                name=name
            )
            logger.info(f"备份导入成功: {imported_backup.id}")
            return {
                "id": imported_backup.id,
                "name": imported_backup.name,
                "status": imported_backup.status,
                "success": True
            }
        except Exception as e:
            logger.error(f"备份导入失败: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_backups_by_volume(self, volume_retention_policies):
        """按云硬盘清理备份 - 支持不同云硬盘的不同保留策略"""
        try:
            all_backups = self.get_backups()
            current_time = datetime.now()
            deleted_count = 0
            volume_stats = defaultdict(lambda: {"total": 0, "deleted": 0})
            
            for backup in all_backups:
                try:
                    volume_id = backup["volume_id"]
                    volume_stats[volume_id]["total"] += 1
                    
                    # 获取该云硬盘的保留策略，默认为30天
                    retention_days = volume_retention_policies.get(volume_id, 30)
                    
                    # 解析备份创建时间
                    backup_time = datetime.fromisoformat(backup["created_at"].replace('Z', '+00:00'))
                    days_old = (current_time - backup_time).days
                    
                    # 如果备份超过指定天数，则删除
                    if days_old > retention_days:
                        result = self.delete_backup(backup["id"])
                        if result["success"]:
                            deleted_count += 1
                            volume_stats[volume_id]["deleted"] += 1
                            logger.info(f"删除过期备份: {backup['name']} (云硬盘: {volume_id}, 创建于 {days_old} 天前，超过 {retention_days} 天保留期)")
                        else:
                            logger.error(f"删除过期备份失败: {backup['id']} - {result.get('error')}")
                except Exception as e:
                    logger.error(f"处理备份 {backup.get('id')} 时出错: {e}")
                    continue
            
            logger.info(f"按云硬盘清理备份完成，共删除 {deleted_count} 个过期备份")
            return {
                "success": True, 
                "deleted_count": deleted_count, 
                "volume_stats": dict(volume_stats)
            }
        except Exception as e:
            logger.error(f"按云硬盘清理备份失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_system_info(self):
        """获取系统信息"""
        try:
            volumes = self.get_volumes()
            backups = self.get_backups()
            servers = self.get_servers()
            server_snapshots = self.get_server_snapshots()
            volume_snapshots = self.get_volume_snapshots()
            
            # 统计信息
            volume_stats = {
                "total": len(volumes),
                "available": len([v for v in volumes if v["status"] == "available"]),
                "in_use": len([v for v in volumes if v["status"] == "in-use"]),
                "error": len([v for v in volumes if v["status"] == "error"]),
                "creating": len([v for v in volumes if v["status"] == "creating"]),
                "deleting": len([v for v in volumes if v["status"] == "deleting"])
            }
            
            backup_stats = {
                "total": len(backups),
                "full": len([b for b in backups if b.get("backup_type") == "full"]),
                "incremental": len([b for b in backups if b.get("backup_type") == "incremental"]),
                "available": len([b for b in backups if b["status"] == "available"]),
                "creating": len([b for b in backups if b["status"] == "creating"]),
                "error": len([b for b in backups if b["status"] == "error"])
            }
            
            server_stats = {
                "total": len(servers),
                "active": len([s for s in servers if s["status"] == "ACTIVE"]),
                "shutoff": len([s for s in servers if s["status"] == "SHUTOFF"]),
                "error": len([s for s in servers if s["status"] == "ERROR"]),
                "building": len([s for s in servers if s["status"] == "BUILD"]),
                "deleted": len([s for s in servers if s["status"] == "DELETED"])
            }
            
            snapshot_stats = {
                "server_snapshots": {
                    "total": len(server_snapshots),
                    "active": len([s for s in server_snapshots if s["status"] == "ACTIVE"]),
                    "creating": len([s for s in server_snapshots if s["status"] == "BUILDING"]),
                    "error": len([s for s in server_snapshots if s["status"] == "ERROR"])
                },
                "volume_snapshots": {
                    "total": len(volume_snapshots),
                    "available": len([s for s in volume_snapshots if s["status"] == "available"]),
                    "creating": len([s for s in volume_snapshots if s["status"] == "creating"]),
                    "error": len([s for s in volume_snapshots if s["status"] == "error"])
                }
            }
            
            return {
                "volumes": volume_stats,
                "backups": backup_stats,
                "servers": server_stats,
                "snapshots": snapshot_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {"error": str(e)}
    
    # ==================== 云主机快照功能 ====================
    
    def get_servers(self):
        """获取所有云主机"""
        try:
            servers = []
            for server in self.conn.compute.servers(details=True):
                servers.append({
                    "id": server.id,
                    "name": server.name,
                    "status": server.status,
                    "created_at": server.created_at,
                    "flavor": {
                        "id": server.flavor.id,
                        "name": getattr(server.flavor, 'name', ''),
                        "ram": server.flavor.ram,
                        "vcpus": server.flavor.vcpus,
                        "disk": server.flavor.disk
                    },
                    "image": {
                        "id": server.image.id if server.image else None,
                        "name": getattr(server.image, 'name', '') if server.image else ''
                    },
                    "networks": server.networks,
                    "availability_zone": getattr(server, 'OS-EXT-AZ:availability_zone', ''),
                    "power_state": getattr(server, 'OS-EXT-STS:power_state', ''),
                    "task_state": getattr(server, 'OS-EXT-STS:task_state', ''),
                    "vm_state": getattr(server, 'OS-EXT-STS:vm_state', ''),
                    "key_name": getattr(server, 'key_name', ''),
                    "security_groups": getattr(server, 'security_groups', [])
                })
            return servers
        except Exception as e:
            logger.error(f"获取云主机列表失败: {e}")
            return []
    
    def get_server_snapshots(self):
        """获取所有云主机快照"""
        try:
            snapshots = []
            for snapshot in self.conn.compute.snapshots(details=True):
                snapshots.append({
                    "id": snapshot.id,
                    "name": snapshot.name,
                    "server_id": snapshot.server_id,
                    "status": snapshot.status,
                    "created_at": snapshot.created_at,
                    "updated_at": snapshot.updated_at,
                    "metadata": getattr(snapshot, 'metadata', {}),
                    "description": getattr(snapshot, 'description', ''),
                    "size": getattr(snapshot, 'size', 0),
                    "min_disk": getattr(snapshot, 'min_disk', 0),
                    "min_ram": getattr(snapshot, 'min_ram', 0),
                    "progress": getattr(snapshot, 'progress', 0),
                    "block_device_mapping": getattr(snapshot, 'block_device_mapping', [])
                })
            return snapshots
        except Exception as e:
            logger.error(f"获取云主机快照列表失败: {e}")
            return []
    
    def create_server_snapshot(self, server_id, name=None, description=None):
        """创建云主机快照"""
        try:
            if not name:
                name = f"server-snapshot-{server_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            snapshot = self.conn.compute.create_server_snapshot(
                server_id,
                name=name,
                description=description or f"Server snapshot created at {datetime.now().isoformat()}"
            )
            
            logger.info(f"云主机快照创建成功: {snapshot.id}")
            return {
                "id": snapshot.id,
                "name": snapshot.name,
                "status": snapshot.status,
                "success": True
            }
        except Exception as e:
            logger.error(f"创建云主机快照失败: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_server_snapshot(self, snapshot_id):
        """删除云主机快照"""
        try:
            self.conn.compute.delete_server_snapshot(snapshot_id, ignore_missing=True)
            logger.info(f"云主机快照删除成功: {snapshot_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"删除云主机快照失败: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_server_snapshots(self, retention_days=30):
        """清理云主机快照"""
        try:
            all_snapshots = self.get_server_snapshots()
            current_time = datetime.now()
            deleted_count = 0
            
            for snapshot in all_snapshots:
                try:
                    # 只处理已完成的快照
                    if snapshot["status"] != "ACTIVE":
                        continue
                    
                    # 解析快照创建时间
                    snapshot_time = datetime.fromisoformat(snapshot["created_at"].replace('Z', '+00:00'))
                    days_old = (current_time - snapshot_time).days
                    
                    # 如果快照超过指定天数，则删除
                    if days_old > retention_days:
                        result = self.delete_server_snapshot(snapshot["id"])
                        if result["success"]:
                            deleted_count += 1
                            logger.info(f"删除过期云主机快照: {snapshot['name']} (创建于 {days_old} 天前，超过 {retention_days} 天保留期)")
                        else:
                            logger.error(f"删除过期云主机快照失败: {snapshot['id']} - {result.get('error')}")
                except Exception as e:
                    logger.error(f"处理云主机快照 {snapshot.get('id')} 时出错: {e}")
                    continue
            
            logger.info(f"云主机快照清理完成，共删除 {deleted_count} 个超过 {retention_days} 天的过期快照")
            return {"success": True, "deleted_count": deleted_count, "retention_days": retention_days}
        except Exception as e:
            logger.error(f"云主机快照清理失败: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== 云硬盘快照功能 ====================
    
    def get_volume_snapshots(self):
        """获取所有云硬盘快照"""
        try:
            snapshots = []
            for snapshot in self.conn.block_storage.snapshots(details=True):
                snapshots.append({
                    "id": snapshot.id,
                    "name": snapshot.name,
                    "volume_id": snapshot.volume_id,
                    "status": snapshot.status,
                    "created_at": snapshot.created_at,
                    "updated_at": snapshot.updated_at,
                    "metadata": getattr(snapshot, 'metadata', {}),
                    "description": getattr(snapshot, 'description', ''),
                    "size": snapshot.size,
                    "force": getattr(snapshot, 'force', False),
                    "progress": getattr(snapshot, 'progress', 0),
                    "user_id": getattr(snapshot, 'user_id', ''),
                    "project_id": getattr(snapshot, 'project_id', '')
                })
            return snapshots
        except Exception as e:
            logger.error(f"获取云硬盘快照列表失败: {e}")
            return []
    
    def create_volume_snapshot(self, volume_id, name=None, description=None, force=False):
        """创建云硬盘快照"""
        try:
            if not name:
                name = f"volume-snapshot-{volume_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            snapshot = self.conn.block_storage.create_snapshot(
                volume_id=volume_id,
                name=name,
                description=description or f"Volume snapshot created at {datetime.now().isoformat()}",
                force=force
            )
            
            logger.info(f"云硬盘快照创建成功: {snapshot.id}")
            return {
                "id": snapshot.id,
                "name": snapshot.name,
                "status": snapshot.status,
                "success": True
            }
        except Exception as e:
            logger.error(f"创建云硬盘快照失败: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_volume_snapshot(self, snapshot_id):
        """删除云硬盘快照"""
        try:
            self.conn.block_storage.delete_snapshot(snapshot_id, ignore_missing=True, force=False)
            logger.info(f"云硬盘快照删除成功: {snapshot_id}")
            return {"success": True}
        except Exception as e:
            logger.error(f"删除云硬盘快照失败: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_volume_snapshots(self, retention_days=30):
        """清理云硬盘快照"""
        try:
            all_snapshots = self.get_volume_snapshots()
            current_time = datetime.now()
            deleted_count = 0
            
            for snapshot in all_snapshots:
                try:
                    # 只处理已完成的快照
                    if snapshot["status"] != "available":
                        continue
                    
                    # 解析快照创建时间
                    snapshot_time = datetime.fromisoformat(snapshot["created_at"].replace('Z', '+00:00'))
                    days_old = (current_time - snapshot_time).days
                    
                    # 如果快照超过指定天数，则删除
                    if days_old > retention_days:
                        result = self.delete_volume_snapshot(snapshot["id"])
                        if result["success"]:
                            deleted_count += 1
                            logger.info(f"删除过期云硬盘快照: {snapshot['name']} (创建于 {days_old} 天前，超过 {retention_days} 天保留期)")
                        else:
                            logger.error(f"删除过期云硬盘快照失败: {snapshot['id']} - {result.get('error')}")
                except Exception as e:
                    logger.error(f"处理云硬盘快照 {snapshot.get('id')} 时出错: {e}")
                    continue
            
            logger.info(f"云硬盘快照清理完成，共删除 {deleted_count} 个超过 {retention_days} 天的过期快照")
            return {"success": True, "deleted_count": deleted_count, "retention_days": retention_days}
        except Exception as e:
            logger.error(f"云硬盘快照清理失败: {e}")
            return {"success": False, "error": str(e)} 