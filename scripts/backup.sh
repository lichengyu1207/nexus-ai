#!/bin/bash

# 房算云AI 数据库备份脚本
# 用法: ./scripts/backup.sh [选项]
# 选项:
#   --full         完整备份（包含上传文件）
#   --upload       上传到远程存储
#   --rotate       清理旧备份

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置变量
PROJECT_DIR="/opt/property-ai"
BACKUP_DIR="/opt/backups/property-ai"
DATA_DIR="$PROJECT_DIR/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_DIR=$(date +%Y%m%d)

# 远程存储配置（可选）
REMOTE_ENABLED=false
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_PATH=""

# 解析参数
FULL_BACKUP=false
UPLOAD_BACKUP=false
ROTATE_BACKUP=false

for arg in "$@"; do
    case $arg in
        --full)
            FULL_BACKUP=true
            shift
            ;;
        --upload)
            UPLOAD_BACKUP=true
            shift
            ;;
        --rotate)
            ROTATE_BACKUP=true
            shift
            ;;
        *)
            log_error "未知参数: $arg"
            exit 1
            ;;
    esac
done

# 创建备份目录
mkdir -p $BACKUP_DIR/$DATE_DIR

# 备份文件名
DB_BACKUP="$BACKUP_DIR/$DATE_DIR/property-ai_db_$TIMESTAMP.db"
FULL_BACKUP_FILE="$BACKUP_DIR/$DATE_DIR/property-ai_full_$TIMESTAMP.tar.gz"

log_info "开始备份..."

# 1. 数据库备份
if [ -f "$DATA_DIR/property-ai.db" ]; then
    log_info "备份数据库..."
    cp $DATA_DIR/property-ai.db $DB_BACKUP
    
    # 验证备份
    if [ -f "$DB_BACKUP" ]; then
        SIZE=$(du -h $DB_BACKUP | cut -f1)
        log_success "数据库备份完成: $DB_BACKUP ($SIZE)"
    else
        log_error "数据库备份失败"
        exit 1
    fi
else
    log_error "数据库文件不存在: $DATA_DIR/property-ai.db"
    exit 1
fi

# 2. 完整备份（可选）
if [ "$FULL_BACKUP" = true ]; then
    log_info "创建完整备份..."
    
    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    
    # 复制需要备份的文件
    cp -r $DATA_DIR $TEMP_DIR/
    cp -r $PROJECT_DIR/logs $TEMP_DIR/ 2>/dev/null || true
    cp $PROJECT_DIR/.env $TEMP_DIR/ 2>/dev/null || true
    
    # 打包
    tar -czf $FULL_BACKUP_FILE -C $TEMP_DIR .
    rm -rf $TEMP_DIR
    
    if [ -f "$FULL_BACKUP_FILE" ]; then
        SIZE=$(du -h $FULL_BACKUP_FILE | cut -f1)
        log_success "完整备份完成: $FULL_BACKUP_FILE ($SIZE)"
    else
        log_error "完整备份失败"
        exit 1
    fi
fi

# 3. 上传到远程存储（可选）
if [ "$UPLOAD_BACKUP" = true ] && [ "$REMOTE_ENABLED" = true ]; then
    log_info "上传备份到远程存储..."
    
    if [ -n "$REMOTE_HOST" ] && [ -n "$REMOTE_USER" ] && [ -n "$REMOTE_PATH" ]; then
        scp $DB_BACKUP $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
        
        if [ "$FULL_BACKUP" = true ]; then
            scp $FULL_BACKUP_FILE $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
        fi
        
        log_success "备份上传完成"
    else
        log_error "远程存储配置不完整，跳过上传"
    fi
fi

# 4. 清理旧备份
if [ "$ROTATE_BACKUP" = true ]; then
    log_info "清理旧备份..."
    
    # 保留最近30天的数据库备份
    find $BACKUP_DIR -name "*.db" -mtime +30 -delete
    
    # 保留最近7天的完整备份
    find $BACKUP_DIR -name "*_full_*.tar.gz" -mtime +7 -delete
    
    # 清理空目录
    find $BACKUP_DIR -type d -empty -delete
    
    log_success "旧备份清理完成"
fi

# 5. 生成备份报告
echo ""
echo "========================================"
log_success "备份完成！"
echo "========================================"
echo ""
echo "备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "备份目录: $BACKUP_DIR/$DATE_DIR"
echo ""
echo "备份文件:"
ls -lh $BACKUP_DIR/$DATE_DIR/ 2>/dev/null || echo "  无"
echo ""
echo "磁盘使用:"
df -h $BACKUP_DIR | tail -1
echo ""

# 6. 备份完整性检查
log_info "验证备份完整性..."
if [ -f "$DB_BACKUP" ]; then
    # SQLite 完整性检查
    INTEGRITY=$(sqlite3 $DB_BACKUP "PRAGMA integrity_check;" 2>/dev/null || echo "error")
    if [ "$INTEGRITY" = "ok" ]; then
        log_success "数据库完整性检查通过"
    else
        log_error "数据库完整性检查失败: $INTEGRITY"
        exit 1
    fi
fi

log_success "备份流程全部完成"
