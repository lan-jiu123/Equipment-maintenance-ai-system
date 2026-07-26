#!/bin/bash
# ============================================================
# 设备检修AI系统 - 一键部署启动脚本（融合版：千问/RAG/知识库）
# 适配：银河麒麟 V10/V11 + LoongArch / 通用 x86_64 虚拟机
#
# 用法：
#   bash deploy/start.sh --qwen      # 默认推荐：云端千问（队友申请的 Key）
#   bash deploy/start.sh --longcat   # LongCat 云端模式
#   bash deploy/start.sh --offline   # 离线模式（Ollama 本地模型）
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

MODE="${1:-qwen}"
INSTALL_LOG="$PROJECT_DIR/install.log"
: > "$INSTALL_LOG"

echo "=========================================="
echo "  设备检修AI系统 - 部署启动脚本 v3.0（融合版）"
echo "  含：千问云端 LLM + RAG 混合检索 + 知识库自动导入"
echo "=========================================="
echo ""

# ---- 颜色定义 ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK ]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERR ]${NC} $1"; }

# ============================================================
#  [1/8] 系统环境检测
# ============================================================
echo "=========================================="
echo "  [步骤 1/8] 系统环境检测"
echo "=========================================="

ARCH=$(uname -m 2>/dev/null || echo "unknown")
CPU_CORES=$(nproc 2>/dev/null || echo "4")
MEM_TOTAL=$(free -m 2>/dev/null | awk '/Mem:/{print $2}' || echo "8192")
DISK_AVAIL=$(df -BG . 2>/dev/null | awk 'NR==2{print $4}' | sed 's/G//' || echo "50")

log_info "CPU架构     : $ARCH"
log_info "CPU核心数   : $CPU_CORES (推荐 ≥4 核)"
log_info "内存        : ${MEM_TOTAL}MB (推荐 ≥8GB，千问云端模式 ≥4GB 可运行)"
log_info "可用磁盘    : ${DISK_AVAIL}GB (推荐 ≥20GB)"

[ -f /etc/kylin-release ] && log_ok "检测到银河麒麟: $(head -1 /etc/kylin-release)"
[ -f /etc/os-release ] && . /etc/os-release && log_info "操作系统  : $NAME $VERSION"

# Python 检测
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 --version 2>&1)
    log_info "$PY_VER"
    if [[ ! "$PY_VER" =~ Python\ 3\.(10|11|12) ]]; then
        log_warn "推荐 Python 3.10~3.12，当前版本可能有兼容性问题"
    fi
else
    log_error "未检测到 python3，请先安装 (yum/apt install -y python3 python3-pip python3-venv)"
    exit 1
fi

# Node 检测（如果 dist 不存在就需要 build）
if [ ! -d "frontend/dist" ] || [ -z "$(ls -A frontend/dist 2>/dev/null)" ]; then
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
        log_info "Node $(node -v) / npm $(npm -v) 就绪（将自动 build 前端）"
    else
        log_warn "前端未构建且未检测到 node/npm，请先在本机 build 后再上传，或："
        echo "       (Ubuntu/Debian) sudo apt install -y nodejs npm"
        echo "       (CentOS/Kylin)  sudo yum install -y nodejs npm"
    fi
fi

echo ""

# ============================================================
#  [2/8] 系统依赖安装（curl/git/nginx 可选）
# ============================================================
echo "=========================================="
echo "  [步骤 2/8] 系统依赖"
echo "=========================================="
install_pkg() {
    local p="$1"
    command -v "$p" >/dev/null 2>&1 && { log_ok "$p 已存在"; return 0; }
    log_info "安装 $p..."
    if command -v yum >/dev/null 2>&1; then sudo yum install -y "$p" >> "$INSTALL_LOG" 2>&1 || true
    elif command -v apt >/dev/null 2>&1; then sudo apt install -y "$p" >> "$INSTALL_LOG" 2>&1 || true
    elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y "$p" >> "$INSTALL_LOG" 2>&1 || true; fi
    command -v "$p" >/dev/null 2>&1 && log_ok "$p 安装完成" || log_warn "$p 安装失败（通常不影响运行）"
}
install_pkg curl
install_pkg nginx || true
echo ""

# ============================================================
#  [3/8] 虚拟环境 + Python 依赖
# ============================================================
echo "=========================================="
echo "  [步骤 3/8] 虚拟环境 + Python 依赖"
echo "=========================================="

set +e

cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    log_info "创建虚拟环境..."
    python3 -m venv venv 2>>"$INSTALL_LOG"
    log_ok "虚拟环境创建: $PROJECT_DIR/venv"
else
    log_ok "虚拟环境已存在"
fi
# shellcheck disable=SC1091
source venv/bin/activate
log_ok "虚拟环境已激活"

log_info "升级 pip..."
pip install --upgrade pip >> "$INSTALL_LOG" 2>&1

# LoongArch 编译环境准备
if [ "$ARCH" = "loongarch64" ] || [ -f /etc/kylin-release ]; then
    log_info "LoongArch/银河麒麟：安装编译依赖（gcc python3-devel）..."
    if command -v yum >/dev/null 2>&1; then
        sudo yum install -y gcc python3-devel make cmake >> "$INSTALL_LOG" 2>&1 || true
    elif command -v apt >/dev/null 2>&1; then
        sudo apt install -y gcc python3-dev make cmake >> "$INSTALL_LOG" 2>&1 || true
    fi
    log_ok "编译环境准备完成"
fi

log_info "安装 Python 依赖（分阶段：纯Python包 → 易编译包 → 特殊处理包）..."

MIRROR_LOONG="https://pypi.loongnix.cn/loongnix/pypi/simple"
MIRROR_TUNA="https://pypi.tuna.tsinghua.edu.cn/simple"
MIRROR_HUAWEI="https://mirrors.huaweicloud.com/repository/pypi/simple"

pip_install_with_retry() {
    local pkg="$1"
    log_info "安装 $pkg..."
    pip install --no-cache-dir "$pkg" -i "$MIRROR_LOONG" --trusted-host pypi.loongnix.cn >> "$INSTALL_LOG" 2>&1 || \
    pip install --no-cache-dir "$pkg" -i "$MIRROR_TUNA" >> "$INSTALL_LOG" 2>&1 || \
    pip install --no-cache-dir "$pkg" -i "$MIRROR_HUAWEI" >> "$INSTALL_LOG" 2>&1 || \
    pip install --no-cache-dir "$pkg" >> "$INSTALL_LOG" 2>&1
    if [ $? -eq 0 ]; then
        log_ok "$pkg 安装成功"
        return 0
    else
        log_warn "$pkg 安装失败，尝试备选方案..."
        return 1
    fi
}

log_info "[阶段1] 纯Python包（fastapi, sqlalchemy, requests, pypdf, jieba...）"
pip_install_with_retry "fastapi>=0.100"
pip_install_with_retry "uvicorn>=0.20"
pip_install_with_retry "sqlalchemy>=2.0"
pip_install_with_retry "requests>=2.28"
pip_install_with_retry "pypdf>=4.0"
pip_install_with_retry "jieba>=0.42.1"
pip_install_with_retry "python-multipart>=0.0.9"
pip_install_with_retry "python-dotenv>=1.0"

log_info "[阶段2] pydantic（兼容 v1/v2，避免 Rust 编译问题）"
pip_install_with_retry "pydantic>=1.10,<3" || pip_install_with_retry "pydantic==1.10.14"
log_info "跳过 pydantic-settings（LoongArch兼容优化）"

log_info "[阶段3] openai SDK"
pip_install_with_retry "openai==1.30.5"

log_info "[阶段4] 安全相关包（passlib, jose）"
pip_install_with_retry "passlib"
pip_install_with_retry "passlib[bcrypt]" || {
    log_warn "bcrypt 编译失败，使用纯Python pbkdf2 替代"
    pip_install_with_retry "passlib"
}
pip_install_with_retry "python-jose[cryptography]" || {
    log_warn "cryptography 编译失败，尝试纯Python版本"
    pip_install_with_retry "python-jose"
}

log_ok "Python 依赖安装完成（部分包使用备选方案）"

set -e

echo ""

# ============================================================
#  [4/8] 环境变量 .env 配置 + 模式切换
# ============================================================
echo "=========================================="
echo "  [步骤 4/8] 环境变量配置（模式：$MODE）"
echo "=========================================="

if [ ! -f ".env" ]; then
    cp .env.example .env
    log_ok "已创建 .env（从 .env.example 复制）"
else
    log_ok ".env 已存在（保留原配置）"
fi

set_env() {
    # set_env KEY VALUE  ——  修改或追加 .env 里的 KEY=VALUE
    local key="$1" val="$2"
    if grep -q "^${key}=" .env 2>/dev/null; then
        # shellcheck disable=SC2016
        sed -i "s|^${key}=.*|${key}=${val}|" .env
    else
        echo "${key}=${val}" >> .env
    fi
}

case "$MODE" in
    --qwen)
        log_info "模式：云端千问（阿里云百炼）"
        set_env "LLM_BACKEND" "longcat"  # 保留兼容值，实际优先看 QWEN_API_KEY
        set_env "EMBEDDING_BACKEND" "local_hash"
        set_env "AUTO_IMPORT_KNOWLEDGE" "true"
        log_ok "默认模式：只要 .env 内 QWEN_API_KEY 非空，即自动走千问云端"
        log_warn "请务必编辑 $PROJECT_DIR/.env 填入申请的 QWEN_API_KEY=sk-xxxx"
        ;;
    --longcat)
        log_info "模式：LongCat 云端"
        set_env "LLM_BACKEND" "longcat"
        ;;
    --offline)
        log_info "模式：Ollama 离线本地模型"
        set_env "LLM_BACKEND" "ollama"
        ;;
    *)
        log_info "未指定模式，默认按 .env 已有配置运行（千问优先）"
        ;;
esac

# 融合后：数据/上传目录（config.py 计算属性默认值）
mkdir -p data data/logs data/uploads data/raw deploy/backend
log_ok "数据目录创建: data/ data/logs data/uploads data/raw"

echo ""

# ============================================================
#  [5/8] 前端构建（dist 不存在时自动 build）
# ============================================================
echo "=========================================="
echo "  [步骤 5/8] 前端文件"
echo "=========================================="

if [ -d "frontend/dist" ] && [ -n "$(ls -A frontend/dist 2>/dev/null)" ]; then
    log_ok "前端构建产物存在: frontend/dist/"
else
    if command -v npm >/dev/null 2>&1; then
        log_info "自动构建前端（首次可能较慢）..."
        cd frontend
        if [ ! -d "node_modules" ]; then
            log_info "npm ci（安装依赖）..."
            npm ci --registry=https://registry.npmmirror.com >> "$INSTALL_LOG" 2>&1 || \
            npm install --registry=https://registry.npmmirror.com >> "$INSTALL_LOG" 2>&1
        fi
        log_info "npm run build..."
        npm run build >> "$INSTALL_LOG" 2>&1
        cd "$PROJECT_DIR"
        log_ok "前端构建完成: frontend/dist/"
    else
        log_warn "未检测到 npm，跳过前端构建。请先在本机 build 再上传整个 frontend/dist 目录。"
    fi
fi

# 复制到 deploy/frontend/dist 给 nginx 用（保持 nginx.conf 注释路径一致）
if [ -d "frontend/dist" ]; then
    mkdir -p deploy/frontend
    rm -rf deploy/frontend/dist
    cp -r frontend/dist deploy/frontend/
    log_ok "前端文件同步: deploy/frontend/dist/ （供 nginx 部署）"
fi

echo ""

# ============================================================
#  [6/8] 初始化数据库 + seed 演示数据
# ============================================================
echo "=========================================="
echo "  [步骤 6/8] 数据库 + 演示数据（可选）"
echo "=========================================="

cd "$PROJECT_DIR/backend"
DB_INIT_FLAG="../data/.db_initialized.flag"
if [ ! -f "$DB_INIT_FLAG" ]; then
    log_info "首次启动：初始化数据库结构 + seed 演示数据（admin/worker1/worker2/worker3）..."
    python -c "from app.database import init_database; init_database()" >> "$INSTALL_LOG" 2>&1 || true
    if [ -f "app/seed.py" ]; then
        python -m app.seed >> "$INSTALL_LOG" 2>&1 || python app/seed.py >> "$INSTALL_LOG" 2>&1 || true
    fi
    touch "$DB_INIT_FLAG"
    log_ok "数据库初始化完成（flag: $DB_INIT_FLAG）"
else
    log_ok "数据库已初始化，跳过（如需重置：rm $DB_INIT_FLAG 后重跑）"
fi

echo ""

# ============================================================
#  [7/8] systemd 服务配置
# ============================================================
echo "=========================================="
echo "  [步骤 7/8] 注册 systemd 服务"
echo "=========================================="

sudo tee /etc/systemd/system/equipai.service > /dev/null << EOF
[Unit]
Description=Equipment Maintenance AI System (融合版：千问 + RAG + 知识库)
After=network.target

[Service]
Type=simple
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=-$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=5
StandardOutput=append:$PROJECT_DIR/data/logs/api.log
StandardError=append:$PROJECT_DIR/data/logs/api.err.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload 2>/dev/null || true
sudo systemctl enable equipai.service 2>/dev/null || true
log_ok "systemd 服务已注册: equipai.service"

echo ""

# ============================================================
#  [8/8] 启动后端 + 健康检查
# ============================================================
echo "=========================================="
echo "  [步骤 8/8] 启动服务 + 健康检查"
echo "=========================================="

cd "$PROJECT_DIR/backend"

log_info "启动后端（uvicorn，监听 0.0.0.0:8000）..."
nohup "$PROJECT_DIR/venv/bin/uvicorn" app.main:app \
    --host 0.0.0.0 --port 8000 --workers 1 \
    >> "$PROJECT_DIR/data/logs/api.log" 2>>"$PROJECT_DIR/data/logs/api.err.log" &
API_PID=$!
echo $API_PID > "$PROJECT_DIR/data/logs/api.pid"
log_ok "后端 PID: $API_PID （日志: data/logs/api.{log,err.log}）"

# 等待就绪
echo ""
log_info "等待后端就绪（最长 60s）..."
READY=0
for i in $(seq 1 60); do
    if curl -sf http://127.0.0.1:8000/health/ready > /dev/null 2>&1; then
        READY=1
        break
    fi
    sleep 1
done
if [ "$READY" = "1" ]; then
    log_ok "后端就绪，开始验证..."
    HR=$(curl -sf http://127.0.0.1:8000/health/ready 2>/dev/null)
    LLM_OK=$(echo "$HR" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('checks',{}).get('llm'))" 2>/dev/null || echo "?")
    KB=$(echo "$HR" | python3 -c "import sys,json;d=json.load(sys.stdin);b=d.get('knowledge_bootstrap',{});print(f'{b.get('ready',0)} ready / {b.get('imported',0)} imported')" 2>/dev/null || echo "?")
    log_info "大模型连通性 (llm): $LLM_OK （true=千问/LongCat 识别）"
    log_info "知识库导入: $KB"
else
    log_warn "60 秒内未就绪，请查看日志 data/logs/api.err.log"
fi

# ---- nginx 建议 ----
echo ""
echo "=========================================="
echo -e "  ${GREEN}✓ 部署脚本执行完成${NC}"
echo "=========================================="
echo ""
echo "  直接访问（不经过 nginx）："
echo "    前端如果没 build，需要先前端单独 npm run dev -> http://虚拟机IP:5173"
echo "    API 文档  : http://虚拟机IP:8000/docs"
echo "    健康检查  : http://虚拟机IP:8000/health/ready"
echo ""
echo "  推荐：用 nginx 统一 80 端口对外（前后端同域）："
echo "    sudo cp deploy/nginx.conf /etc/nginx/conf.d/equipai.conf"
echo "    # 编辑 /etc/nginx/conf.d/equipai.conf 里的 root 为：$PROJECT_DIR/deploy/frontend/dist"
echo "    sudo nginx -t && sudo systemctl restart nginx"
echo "    访问：http://虚拟机IP/"
echo ""
echo "  演示账号："
echo "    管理员   admin    / ad1234     (赵五 · 仪表盘)"
echo "    检修员1  worker1  / 123456     (李建华)"
echo "    检修员2  worker2  / 234567     (张伟)"
echo "    检修员3  worker3  / 345678     (黄丽)"
echo ""
echo "  ❗ 必做一步：打开 $PROJECT_DIR/.env，在 QWEN_API_KEY= 后面填入队友申请的千问 Key"
echo ""
echo "  常用命令："
echo "    systemctl status equipai          # 服务状态"
echo "    systemctl restart equipai         # 重启（改完 .env/代码后必须）"
echo "    tail -f data/logs/api.log         # 实时日志"
echo "    bash deploy/backup.sh             # 备份 .env + 数据库 + 上传文件"
echo ""

trap 'echo ""; echo "停止中..."; kill -TERM $API_PID 2>/dev/null; rm -f "$PROJECT_DIR/data/logs/api.pid"; echo "已停止"' SIGINT SIGTERM

# 不阻塞退出，交给 systemd/前台自行观察
exit 0
