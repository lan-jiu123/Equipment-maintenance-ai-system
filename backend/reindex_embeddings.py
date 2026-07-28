"""
text-embedding-v3 迁移脚本：清空旧向量索引，重启后自动重建。
用法：python reindex_embeddings.py   # 然后重启后端服务
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "equipai.db"
if not DB_PATH.is_file():
    # 尝试其他路径
    DB_PATH = Path(__file__).parent / "app" / "equipai.db"

if not DB_PATH.is_file():
    print("❌ 未找到 equipai.db，请确认数据库路径")
    exit(1)

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

# 1. 清空旧 chunk 和 embedding 数据（确保新向量维度匹配）
tables = ["chunk_embeddings", "document_chunks"]
for table in tables:
    try:
        cur.execute(f"DELETE FROM {table}")
        print(f"✅ 已清空 {table}")
    except sqlite3.OperationalError as e:
        print(f"⚠️  {table}: {e}")

# 2. 将文档状态重置为 "uploaded"，让启动时自动重建索引
try:
    cur.execute("UPDATE documents SET status = 'uploaded' WHERE status = 'ready'")
    print(f"✅ 已重置 {cur.rowcount} 个文档状态（ready → uploaded）")
except sqlite3.OperationalError as e:
    print(f"⚠️  documents 表: {e}")

conn.commit()
conn.close()

print("\n🎉 清理完成！请重启后端服务（uvicorn 或 start.sh）使 text-embedding-v3 生效")
print("   重启后知识库文档将自动重新向量化。")
