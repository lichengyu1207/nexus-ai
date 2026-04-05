#!/bin/bash

# 房算云AI 自动化部署脚本
# 用法: ./scripts/deploy.sh [选项]
# 选项:
#   --skip-pull    跳过代码拉取
#   --skip-build   跳过前端构建
#   --skip-deps    跳过依赖安装
#   --restart      强制重启服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置变量
PROJECT_DIR="/opt/property-ai"
SERVICE_NAME="property-ai"
BACKUP_DIR="/opt/backups/property-ai"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 解析参数
SKIP_PULL=false
SKIP_BUILD=false
SKIP_DEPS=false
FORCE_RESTART=false

for arg in "$@"; do
    case $arg in
        --skip-pull)
            SKIP_PULL=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --restart)
            FORCE_RESTART=true
            shift
            ;;
        *)
            log_error "未知参数: $arg"
            exit 1
            ;;
    esac
done

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    log_error "请使用 root 用户或 sudo 运行此脚本"
    exit 1
fi

# 创建必要的目录
log_info "创建必要的目录..."
mkdir -p $BACKUP_DIR
mkdir -p $PROJECT_DIR/data
mkdir -p $PROJECT_DIR/logs

# 进入项目目录
cd $PROJECT_DIR

# 1. 拉取最新代码
if [ "$SKIP_PULL" = false ]; then
    log_info "拉取最新代码..."
    git fetch origin
    git reset --hard origin/main
    log_success "代码更新完成"
else
    log_warning "跳过代码拉取"
fi

# 2. 安装后端依赖
if [ "$SKIP_DEPS" = false ]; then
    log_info "安装后端依赖..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        python3 -m venv venv
        source venv/bin/activate
    fi
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    log_success "后端依赖安装完成"
    
    # 3. 安装前端依赖
    log_info "安装前端依赖..."
    npm install
    log_success "前端依赖安装完成"
else
    log_warning "跳过依赖安装"
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
fi

# 4. 构建前端
if [ "$SKIP_BUILD" = false ]; then
    log_info "构建前端..."
    npm run build
    log_success "前端构建完成"
else
    log_warning "跳过前端构建"
fi

# 5. 数据库迁移
log_info "执行数据库迁移..."
python -c "import sys; sys.path.insert(0, 'backend'); from database import init_db; import asyncio; asyncio.run(init_db())"
log_success "数据库迁移完成"

# 6. 备份当前版本
if [ -f "data/property-ai.db" ]; then
    log_info "备份数据库..."
    cp data/property-ai.db $BACKUP_DIR/property-ai_$TIMESTAMP.db
    # 保留最近7天的备份
    find $BACKUP_DIR -name "*.db" -mtime +7 -delete
    log_success "数据库备份完成"
fi

# 7. 检查环境变量
if [ ! -f ".env" ]; then
    log_warning ".env 文件不存在，从模板创建..."
    if [ -f ".env.production.example" ]; then
        cp .env.production.example .env
        log_warning "请编辑 .env 文件配置生产环境变量"
    fi
fi

# 8. 重启服务
log_info "重启服务..."
if systemctl is-active --quiet $SERVICE_NAME; then
    systemctl restart $SERVICE_NAME
    log_success "服务重启完成"
else
    systemctl start $SERVICE_NAME
    log_success "服务启动完成"
fi

# 9. 检查服务状态
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    log_success "服务运行正常"
else
    log_error "服务启动失败，请检查日志"
    journalctl -u $SERVICE_NAME -n 50 --no-pager
    exit 1
fi

# 10. 重载 Nginx
log_info "重载 Nginx 配置..."
nginx -t && systemctl reload nginx
log_success "Nginx 配置重载完成"

# 11. 显示部署信息
echo ""
echo "========================================"
log_success "部署完成！"
echo "========================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "服务状态: $(systemctl is-active $SERVICE_NAME)"
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "常用命令:"
echo "  查看日志: journalctl -u $SERVICE_NAME -f"
echo "  重启服务: systemctl restart $SERVICE_NAME"
echo "  查看状态: systemctl status $SERVICE_NAME"
echo ""
