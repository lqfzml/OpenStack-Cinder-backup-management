import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # OpenStack 认证配置
    OS_AUTH_URL = os.getenv('OS_AUTH_URL', 'http://your-openstack-auth-url:5000/v3')
    OS_USERNAME = os.getenv('OS_USERNAME', 'your_user')
    OS_PASSWORD = os.getenv('OS_PASSWORD', 'your_password')
    OS_PROJECT_NAME = os.getenv('OS_PROJECT_NAME', 'your_project')
    OS_USER_DOMAIN_NAME = os.getenv('OS_USER_DOMAIN_NAME', 'Default')
    OS_PROJECT_DOMAIN_NAME = os.getenv('OS_PROJECT_DOMAIN_NAME', 'Default')
    
    # MySQL 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'cinder_backup')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'cinder_backup_pass')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'cinder_backup_db')
    MYSQL_CHARSET = os.getenv('MYSQL_CHARSET', 'utf8mb4')
    
    # 备份策略配置
    FULL_BACKUP_RETENTION = int(os.getenv('FULL_BACKUP_RETENTION', '4'))
    INCREMENTAL_BACKUP_RETENTION = int(os.getenv('INCREMENTAL_BACKUP_RETENTION', '6'))
    
    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true' 