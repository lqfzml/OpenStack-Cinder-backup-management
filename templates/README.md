# OpenStack Cinder 备份管理系统 (28.4.1)

这是一个完整的 OpenStack Cinder 云硬盘备份管理解决方案，专门适配 OpenStack 28.4.1 版本，支持全量备份、增量备份、备份恢复、导入导出、智能清理策略和定时备份功能。

## 🆕 最新功能更新

- ✅ **v6 优化功能**: MySQL数据库存储支持
- ✅ **v5 优化功能**: 根据备份描述判断类型和按云硬盘制定清理策略
- ✅ **v4 优化功能**: 定时备份云硬盘管理和自定义清理天数
- ✅ **云硬盘状态支持**: 支持 `in-use` 和 `available` 状态的云硬盘备份
- ✅ **分离备份列表**: 全量备份和增量备份分别显示在不同标签页
- ✅ **定时备份功能**: 支持每日和每周定时备份，可选择具体时间
- ✅ **备份恢复**: 从备份直接恢复云硬盘
- ✅ **备份导出**: 导出备份到外部存储
- ✅ **备份导入**: 从外部存储导入备份
- ✅ **增强API**: 使用最新的 Cinder API v3
- ✅ **详细状态**: 显示更多备份和云硬盘信息
- ✅ **系统统计**: 提供详细的系统统计信息

## 🆕 OpenStack 28.4.1 新功能

- ✅ **备份恢复**: 从备份直接恢复云硬盘
- ✅ **备份导出**: 导出备份到外部存储
- ✅ **备份导入**: 从外部存储导入备份
- ✅ **增强API**: 使用最新的 Cinder API v3
- ✅ **详细状态**: 显示更多备份和云硬盘信息
- ✅ **系统统计**: 提供详细的系统统计信息

## 🆕 v3 优化功能

- ✅ **30天自动清理**: 超过30天的备份自动清理（全量+增量）
- ✅ **完整云硬盘显示**: 显示所有状态的云硬盘，✓ 标记可备份状态
- ✅ **智能备份命名**: 定时备份自动生成详细名称格式
- ✅ **增量备份修复**: 修复增量备份列表显示问题
- ✅ **定时备份优化**: 改进定时备份执行逻辑和错误处理

## 🆕 v4 优化功能

- ✅ **定时备份云硬盘管理**: 支持为现有定时备份添加/删除云硬盘
- ✅ **自定义清理天数**: 清理备份时可自由选择保留天数（1-365天）
- ✅ **增强的用户界面**: 改进的定时备份管理界面和清理备份界面
- ✅ **实时云硬盘管理**: 在定时备份中动态管理云硬盘列表
- ✅ **智能重复检测**: 添加云硬盘时自动避免重复添加

## 🆕 v5 优化功能

- ✅ **智能备份类型判断**: 根据备份描述（description）自动判断全量/增量备份
- ✅ **按云硬盘清理策略**: 支持为不同云硬盘制定不同的保留天数
- ✅ **增强清理界面**: 支持统一清理和按云硬盘清理两种模式
- ✅ **备份描述解析**: 自动识别 "Full backup" 和 "Incremental backup" 描述
- ✅ **灵活清理策略**: 可为每个云硬盘设置1-365天的不同保留期

## 🆕 v6 优化功能

- ✅ **MySQL数据库存储**: 使用MySQL 15.1 (MariaDB 10.11.5) 替代JSON文件存储
- ✅ **数据持久化**: 提供更好的数据一致性和持久性
- ✅ **并发访问支持**: 支持多用户并发访问和操作
- ✅ **备份历史记录**: 自动记录定时备份的执行历史
- ✅ **数据库初始化**: 提供自动化的数据库和表结构初始化脚本
- ✅ **连接池管理**: 智能的数据库连接管理和重连机制

## 功能特性

- ✅ **全量备份**: 创建云硬盘的完整备份
- ✅ **增量备份**: 创建云硬盘的增量备份
- ✅ **定时备份**: 支持每日和每周定时备份
- ✅ **备份恢复**: 从备份恢复云硬盘
- ✅ **备份导出**: 导出备份到外部存储
- ✅ **备份导入**: 从外部存储导入备份
- ✅ **智能清理**: 自动清理超出保留策略的备份
- ✅ **Web界面**: 现代化的Web管理界面
- ✅ **命令行工具**: 支持命令行操作
- ✅ **REST API**: 提供完整的REST API接口
- ✅ **实时监控**: 实时显示备份状态和进度
- ✅ **批量操作**: 支持批量备份和清理
- ✅ **系统统计**: 详细的系统使用统计

## 项目结构

```
cinder-backup-manager/
├── app.py                 # Flask Web应用主文件
├── config.py              # 配置文件
├── database.py            # MySQL数据库模型和操作
├── init_database.py       # 数据库初始化脚本
├── migrate_to_mysql.py    # JSON到MySQL迁移脚本
├── openstack_client.py    # OpenStack客户端封装 (28.4.1)
├── scheduler.py           # 定时备份调度器
├── cinder_backup_cli.py   # 命令行工具
├── requirements.txt       # Python依赖
├── env_example.txt        # 环境变量示例
├── README.md             # 项目说明
├── start.sh              # Linux/Mac启动脚本
├── start.bat             # Windows启动脚本
├── templates/
│   └── index.html        # Web界面模板
└── static/
    └── js/
        └── main.js       # 前端JavaScript
```

## 安装部署

### 1. 环境要求

- Python 3.7+
- MySQL 15.1 (MariaDB 10.11.5) 或更高版本
- OpenStack 28.4.1 环境（支持 Cinder 服务）
- 网络访问 OpenStack API

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `env_example.txt` 为 `.env` 并修改配置：

```bash
cp env_example.txt .env
```

编辑 `.env` 文件，填入你的 OpenStack 认证信息和MySQL数据库配置：

```bash
# OpenStack 认证配置
OS_AUTH_URL=http://your-openstack-auth-url:5000/v3
OS_USERNAME=your_user
OS_PASSWORD=your_password
OS_PROJECT_NAME=your_project
OS_USER_DOMAIN_NAME=Default
OS_PROJECT_DOMAIN_NAME=Default

# MySQL 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=cinder_backup
MYSQL_PASSWORD=cinder_backup_pass
MYSQL_DATABASE=cinder_backup_db
MYSQL_CHARSET=utf8mb4

# 备份策略配置
FULL_BACKUP_RETENTION=4
INCREMENTAL_BACKUP_RETENTION=6

# Flask 配置
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. 初始化数据库

在启动服务之前，需要先初始化MySQL数据库：

```bash
# 设置MySQL root密码环境变量
export MYSQL_ROOT_PASSWORD=your_mysql_root_password

# 运行数据库初始化脚本
python init_database.py
```

初始化脚本将自动：
- 创建数据库 `cinder_backup_db`
- 创建用户 `cinder_backup` 并设置密码
- 创建必要的表结构
- 设置适当的权限

#### 从JSON文件迁移（可选）

如果你之前使用JSON文件存储定时备份配置，可以运行迁移脚本：

```bash
# 运行迁移脚本
python migrate_to_mysql.py
```

迁移脚本将：
- 自动检测并读取 `backup_schedules.json` 文件
- 将配置迁移到MySQL数据库
- 备份原JSON文件
- 显示迁移结果

### 5. 启动服务

#### 启动Web服务
```bash
# Linux/Mac:
./start.sh

# Windows:
start.bat
```

#### 启动定时备份调度器
```bash
# Linux/Mac:
./start.sh scheduler

# Windows:
start.bat scheduler
```

#### 同时启动Web服务和调度器
```bash
# Linux/Mac:
./start.sh both

# Windows:
start.bat both
```

访问 http://localhost:5000 即可使用Web界面。

## 使用方法

### Web界面操作

1. **查看云硬盘和备份**
   - 打开Web界面，自动显示所有云硬盘和备份列表
   - 支持实时刷新和状态监控
   - 显示详细的云硬盘和备份信息
   - 云硬盘列表支持 `in-use` 和 `available` 状态的选择

2. **创建备份**
   - 选择要备份的云硬盘（可多选，支持 in-use 和 available 状态）
   - 点击"全量备份"或"增量备份"按钮
   - 可选择输入备份名称

3. **定时备份管理**
   - 点击"定时备份"按钮打开创建界面
   - 选择备份类型（全量/增量）
   - 设置执行频率（每日/每周）
   - 选择执行时间
   - 选择星期（每周执行时）
   - 选择要备份的云硬盘
   - 在定时备份列表中管理所有定时任务

4. **备份列表管理**
   - 全量备份和增量备份分别显示在不同标签页
   - 支持删除单个备份
   - 显示备份的详细信息

5. **备份恢复**
   - 在备份列表中选择要恢复的备份
   - 点击恢复按钮
   - 可选择目标云硬盘和恢复名称

6. **备份导出/导入**
   - 支持导出备份到外部存储
   - 支持从外部存储导入备份

7. **清理备份**
   - 点击"清理备份"按钮
   - 选择清理模式：
     - **统一清理策略**: 为所有备份设置相同的保留天数（1-365天）
     - **按云硬盘制定策略**: 为不同云硬盘设置不同的保留天数
   - 确认后系统将删除超过指定天数的备份

8. **定时备份云硬盘管理**
   - 在定时备份列表中点击"管理云硬盘"按钮（齿轮图标）
   - 在左侧查看当前定时备份包含的云硬盘
   - 在右侧查看可添加的云硬盘
   - 选择云硬盘后点击"添加选中云硬盘"或"移除选中云硬盘"

### 命令行操作

```bash
# 查看云硬盘列表
python cinder_backup_cli.py list volumes

# 查看备份列表
python cinder_backup_cli.py list backups

# 创建全量备份
python cinder_backup_cli.py backup full <volume_id> --name "my-backup"

# 创建增量备份
python cinder_backup_cli.py backup incremental <volume_id> --name "my-backup"

# 从备份恢复云硬盘
python cinder_backup_cli.py restore <backup_id> --name "restored-volume"

# 导出备份
python cinder_backup_cli.py export <backup_id>

# 导入备份
python cinder_backup_cli.py import <backup_service> <backup_url> --name "imported-backup"

# 清理备份
python cinder_backup_cli.py cleanup

# 删除指定备份
python cinder_backup_cli.py delete <backup_id>

# 查看备份状态
python cinder_backup_cli.py status <backup_id>

# 显示系统信息
python cinder_backup_cli.py info
```

### API接口

#### 获取云硬盘列表
```bash
GET /api/volumes
```

#### 获取备份列表（分离全量备份和增量备份）
```bash
GET /api/backups
```

#### 获取定时备份列表
```bash
GET /api/schedules
```

#### 创建定时备份
```bash
POST /api/schedules
Content-Type: application/json

{
    "volume_ids": ["volume-id-1", "volume-id-2"],
    "backup_type": "full",
    "schedule_type": "weekly",
    "schedule_time": "02:00",
    "weekdays": [1, 3, 5],
    "name": "weekly-backup"
}
```

#### 切换定时备份状态
```bash
POST /api/schedules/<schedule_id>/toggle
```

#### 删除定时备份
```bash
DELETE /api/schedules/<schedule_id>
```

#### 创建全量备份
```bash
POST /api/backup/full
Content-Type: application/json

{
    "volume_ids": ["volume-id-1", "volume-id-2"],
    "name": "backup-name"
}
```

#### 创建增量备份
```bash
POST /api/backup/incremental
Content-Type: application/json

{
    "volume_ids": ["volume-id-1"],
    "name": "backup-name"
}
```

#### 从备份恢复云硬盘
```bash
POST /api/backup/<backup_id>/restore
Content-Type: application/json

{
    "volume_id": "target-volume-id",
    "name": "restored-volume-name"
}
```

#### 导出备份
```bash
GET /api/backup/<backup_id>/export
```

#### 导入备份
```bash
POST /api/backup/import
Content-Type: application/json

{
    "backup_service": "cinder.backup.drivers.swift",
    "backup_url": "swift://container/backup",
    "name": "imported-backup-name"
}
```

#### 清理备份
```bash
# 统一清理策略
POST /api/backup/cleanup
Content-Type: application/json

{
    "retention_days": 30
}

# 按云硬盘制定策略
POST /api/backup/cleanup
Content-Type: application/json

{
    "volume_policies": {
        "volume-id-1": 20,
        "volume-id-2": 15,
        "volume-id-3": 30
    }
}
```

#### 为定时备份添加云硬盘
```bash
POST /api/schedules/<schedule_id>/volumes
Content-Type: application/json

{
    "volume_ids": ["volume-id-1", "volume-id-2"]
}
```

#### 从定时备份移除云硬盘
```bash
DELETE /api/schedules/<schedule_id>/volumes
Content-Type: application/json

{
    "volume_ids": ["volume-id-1", "volume-id-2"]
}
```

#### 删除备份
```bash
DELETE /api/backup/<backup_id>
```

#### 获取备份状态
```bash
GET /api/backup/<backup_id>/status
```

#### 健康检查
```bash
GET /api/health
```

#### 获取系统信息
```bash
GET /api/info
```

## 定时备份功能

### 定时备份类型

1. **每日备份**: 每天在指定时间执行备份
2. **每周备份**: 在指定星期的指定时间执行备份

### 定时备份配置

- **备份类型**: 全量备份或增量备份
- **执行时间**: 24小时制时间格式（如 02:00）
- **星期选择**: 周一至周日（每周备份时）
- **云硬盘选择**: 支持选择多个云硬盘
- **状态管理**: 可启用/禁用定时备份

### 定时备份调度器

定时备份调度器会：
- 每分钟检查一次定时任务
- 在指定时间前后5分钟内执行备份
- 记录执行日志到 `scheduler.log`
- 更新最后执行时间

### 启动定时备份调度器

```bash
# 单独启动调度器
./start.sh scheduler

# 同时启动Web服务和调度器
./start.sh both
```

## 备份策略

### 清理策略

系统采用智能清理策略：

- **智能备份类型判断**: 根据备份描述自动识别全量备份和增量备份
- **统一清理策略**: 支持1-365天的自定义保留期设置
- **按云硬盘清理策略**: 为不同云硬盘制定不同的保留天数
- **手动清理**: 通过Web界面或API手动触发清理，支持两种模式
- **自动清理**: 超出保留时间的备份会被自动删除
- **定时执行**: 可通过定时任务或手动触发清理
- **全量增量统一**: 全量备份和增量备份使用相同的保留策略

### 备份类型判断

系统通过以下方式判断备份类型：

1. **描述优先**: 首先检查备份描述（description）字段
   - 包含 "Full backup" 或 "full backup" → 全量备份
   - 包含 "Incremental backup" 或 "incremental backup" → 增量备份
2. **API字段**: 如果描述中没有明确标识，则使用API的 `is_incremental` 字段
3. **默认策略**: 如果描述为空且API字段不可用，则默认为全量备份

### 备份类型

- **全量备份**: 备份整个云硬盘的所有数据，恢复简单但占用空间大
- **增量备份**: 只备份自上次备份以来变化的数据，节省空间但需要依赖链

### 备份命名规则

- **手动备份**: 用户自定义名称或系统自动生成
- **定时备份**: `云硬盘名称-backup-云硬盘ID-时间戳` 格式
- **示例**: `etone-2-backup-e732e30b-5ef4-408c-ac13-e80dee41a4d5-2025-06-29-20-08`

### 云硬盘状态支持

- **显示所有状态**: 系统显示所有状态的云硬盘（available, in-use, error, creating, deleting等）
- **可备份状态**: 只有 `available` 和 `in-use` 状态的云硬盘可以进行备份
- **状态标记**: 可备份的云硬盘在界面上显示 ✓ 标记
- **智能过滤**: 定时备份创建时自动过滤出可备份的云硬盘

### 备份恢复

- **直接恢复**: 从备份直接创建新的云硬盘
- **覆盖恢复**: 恢复到指定的现有云硬盘
- **跨区域恢复**: 支持跨可用区恢复

### 备份导入导出

- **导出格式**: 支持多种存储后端导出
- **导入支持**: 支持从外部存储导入备份
- **兼容性**: 支持不同OpenStack版本间的备份迁移

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| OS_AUTH_URL | OpenStack认证URL | - |
| OS_USERNAME | OpenStack用户名 | - |
| OS_PASSWORD | OpenStack密码 | - |
| OS_PROJECT_NAME | OpenStack项目名 | - |
| OS_USER_DOMAIN_NAME | 用户域名 | Default |
| OS_PROJECT_DOMAIN_NAME | 项目域名 | Default |
| FULL_BACKUP_RETENTION | 全量备份保留数量 | 4 |
| INCREMENTAL_BACKUP_RETENTION | 增量备份保留数量 | 6 |
| SECRET_KEY | Flask密钥 | - |
| DEBUG | 调试模式 | True |

## OpenStack 28.4.1 兼容性

### API版本
- **Identity API**: v3
- **Volume API**: v3
- **Backup API**: v3

### 新功能支持
- ✅ 备份恢复功能
- ✅ 备份导入导出
- ✅ 增强的备份元数据
- ✅ 详细的错误信息
- ✅ 备份依赖关系管理
- ✅ 云硬盘状态支持（in-use, available）

### 命令兼容性
```bash
# 传统OpenStack CLI命令
openstack volume backup create --force --incremental <volume_id>

# 对应本工具命令
python cinder_backup_cli.py backup incremental <volume_id>
```

## 故障排除

### 常见问题

1. **OpenStack连接失败**
   - 检查认证信息是否正确
   - 确认网络可以访问OpenStack API
   - 验证用户权限是否足够
   - 确认OpenStack版本为28.4.1

2. **备份创建失败**
   - 确认云硬盘状态为available或in-use
   - 检查云硬盘是否被挂载
   - 验证存储后端是否支持备份
   - 检查备份服务是否正常运行

3. **备份恢复失败**
   - 确认备份状态为available
   - 检查目标可用区是否有足够空间
   - 验证用户权限是否足够

4. **Web界面无法访问**
   - 确认Flask服务已启动
   - 检查防火墙设置
   - 验证端口是否被占用

5. **定时备份不执行**
   - 确认调度器已启动
   - 检查定时配置是否正确
   - 查看scheduler.log日志
   - 确认定时任务已启用

### 日志查看

系统会输出详细的日志信息，包括：
- OpenStack连接状态
- 备份操作结果
- 错误信息和堆栈跟踪
- API调用详情
- 定时备份执行日志（scheduler.log）

## 开发说明

### 扩展功能

1. **添加更多定时策略**
   - 每月备份
   - 自定义cron表达式
   - 基于事件触发

2. **增加通知功能**
   - 邮件通知备份结果
   - 短信或钉钉通知
   - 备份失败告警

3. **监控告警**
   - 备份失败告警
   - 存储空间告警
   - 备份依赖关系告警
   - 定时备份执行状态告警

4. **备份验证**
   - 备份完整性检查
   - 恢复测试功能
   - 备份一致性验证

### 代码结构

- `openstack_client.py`: OpenStack操作封装 (28.4.1适配)
- `app.py`: Flask Web应用
- `scheduler.py`: 定时备份调度器
- `config.py`: 配置管理
- `cinder_backup_cli.py`: 命令行工具
- `templates/index.html`: Web界面
- `static/js/main.js`: 前端逻辑

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 更新日志

### v2.1.0 (最新版本)
- ✅ 支持 in-use 和 available 状态的云硬盘备份
- ✅ 分离全量备份和增量备份列表显示
- ✅ 新增定时备份功能（每日/每周）
- ✅ 新增定时备份调度器
- ✅ 改进Web界面用户体验
- ✅ 增强错误处理和日志记录

### v2.0.0 (OpenStack 28.4.1)
- ✅ 适配OpenStack 28.4.1版本
- ✅ 新增备份恢复功能
- ✅ 新增备份导入导出功能
- ✅ 增强API接口
- ✅ 改进错误处理
- ✅ 添加系统统计信息
