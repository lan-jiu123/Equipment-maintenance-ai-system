#!/bin/bash
# ============================================================
# 设备检修AI系统 - 数据备份脚本
# 功能：备份环境配置、数据库、上传文件
# ============================================================

set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

mkdir -p "${BACKUP_PATH}"

echo "开始备份..."
echo "备份时间: $(date)"

# 备份 SQLite 数据库（如果有）
if [ -f "data/app.db" ]; then
    command -v sqlite3 >/dev/null 2>&1 || { echo "错误: sqlite3 未安装"; exit 1; }
    sqlite3 data/app.db ".backup '${BACKUP_PATH}/app.db'"
    echo "✓ SQLite 数据库备份完成"
fi

# 备份 .env 环境配置
if [ -f ".env" ]; then
    cp .env "${BACKUP_PATH}/.env"
    echo "✓ 环境配置备份完成"
fi

# 备份上传文件（如果有）
if [ -d "data/uploads" ]; then
    cp -r data/uploads "${BACKUP_PATH}/"
    echo "✓ 上传文件备份完成"
fi

# 打包为 tar.gz
tar -czf "${BACKUP_PATH}.tar.gz" -C "${BACKUP_DIR}" "backup_${TIMESTAMP}"
rm -rf "${BACKUP_PATH}"

# 验证备份完整性
if tar -tzf "${BACKUP_PATH}.tar.gz" > /dev/null 2>&1; then
    echo "✓ 备份验证通过"
else
    echo "✗ 备份验证失败!"
    exit 1
fi

echo "备份完成: ${BACKUP_PATH}.tar.gz"

# 仅保留最近 7 份备份
KEEP_COUNT=7
ls -t "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null | tail -n +$((KEEP_COUNT + 1)) | xargs -r rm
echo "已清理，仅保留最近 ${KEEP_COUNT} 个备份"
