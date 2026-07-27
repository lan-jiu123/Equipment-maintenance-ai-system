"""
作业指导功能 - 数据库验证脚本
验证目标：
1. guides 表包含 maintenance_level 和 checklist_json 字段
2. 20 条指导数据已设置检修等级
3. guide_executions 表可正常读写
4. 勾选状态持久化到数据库（非 localStorage）
"""
import sys, json, sqlite3
sys.path.insert(0, '.')

DB_PATH = 'equipai.db'
PASS = 0
FAIL = 0

def test(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f'  ✓ PASS: {name}')
    else:
        FAIL += 1
        print(f'  ✗ FAIL: {name}')

print('=' * 60)
print('  作业指导功能 - 数据库验证')
print('=' * 60)
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ========== 测试1: 表结构验证 ==========
print('【测试1】表结构验证')
cursor.execute("PRAGMA table_info(guides)")
guides_cols = [row[1] for row in cursor.fetchall()]
test('guides 表存在', len(guides_cols) > 0)
test('maintenance_level 字段存在', 'maintenance_level' in guides_cols)
test('checklist_json 字段存在', 'checklist_json' in guides_cols)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='guide_executions'")
test('guide_executions 表存在', cursor.fetchone() is not None)

if 'guide_executions' in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
    cursor.execute("PRAGMA table_info(guide_executions)")
    exec_cols = [row[1] for row in cursor.fetchall()]
    test('guide_executions: ticket_id 字段', 'ticket_id' in exec_cols)
    test('guide_executions: guide_id 字段', 'guide_id' in exec_cols)
    test('guide_executions: status 字段', 'status' in exec_cols)
    test('guide_executions: checklist_status_json 字段', 'checklist_status_json' in exec_cols)
    test('guide_executions: steps_status_json 字段', 'steps_status_json' in exec_cols)

print()

# ========== 测试2: 指导数据验证 ==========
print('【测试2】指导数据验证')
cursor.execute('SELECT COUNT(*) FROM guides')
total = cursor.fetchone()[0]
test(f'guides 表记录数 > 0 (共 {total} 条)', total > 0)

cursor.execute("SELECT COUNT(*) FROM guides WHERE maintenance_level IS NOT NULL")
level_count = cursor.fetchone()[0]
test(f'已设置 maintenance_level (共 {level_count} 条)', level_count >= 20)

cursor.execute("SELECT COUNT(*) FROM guides WHERE checklist_json IS NOT NULL AND checklist_json != '[]' AND checklist_json != ''")
checklist_count = cursor.fetchone()[0]
test(f'已设置 checklist (共 {checklist_count} 条)', checklist_count >= 20)

# 按等级统计
cursor.execute("SELECT maintenance_level, COUNT(*) FROM guides GROUP BY maintenance_level")
level_stats = dict(cursor.fetchall())
print(f'    等级分布: {level_stats}')
test('low 等级存在', 'low' in level_stats)
test('mid 等级存在', 'mid' in level_stats)
test('high 等级存在', 'high' in level_stats)

# 验证 checklist 格式
cursor.execute("SELECT id, title, checklist_json FROM guides WHERE checklist_json IS NOT NULL AND checklist_json != '' LIMIT 3")
for row in cursor.fetchall():
    id, title, cj = row
    try:
        checklist = json.loads(cj)
        test(f'checklist JSON 格式正确: {title[:20]}', isinstance(checklist, list) and len(checklist) > 0)
    except:
        test(f'checklist JSON 格式错误: ID={id}', False)

print()

# ========== 测试3: 执行记录 CRUD 验证 ==========
print('【测试3】执行记录 CRUD 验证')

# 获取一个有效 guide_id、ticket_id 和 user_id
cursor.execute('SELECT id FROM guides LIMIT 1')
guide_row = cursor.fetchone()
guide_id = guide_row[0] if guide_row else None

cursor.execute('SELECT id FROM tickets LIMIT 1')
ticket_row = cursor.fetchone()
ticket_id = ticket_row[0] if ticket_row else None

cursor.execute('SELECT id FROM users LIMIT 1')
user_row = cursor.fetchone()
user_id = user_row[0] if user_row else None

if guide_id and ticket_id and user_id:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    # INSERT
    cursor.execute("""
        INSERT INTO guide_executions (ticket_id, guide_id, user_id, status, checklist_status_json, steps_status_json, started_at)
        VALUES (?, ?, ?, 'pending', '{}', '{}', ?)
    """, (ticket_id, guide_id, user_id, now))
    exec_id = cursor.lastrowid
    test(f'INSERT 成功 (exec_id={exec_id})', exec_id is not None)
    
    # SELECT
    cursor.execute('SELECT * FROM guide_executions WHERE id = ?', (exec_id,))
    row = cursor.fetchone()
    test('SELECT 成功', row is not None)
    
    # UPDATE - 模拟勾选状态持久化
    checklist_status = json.dumps({"0": True, "1": False, "2": True})
    steps_status = json.dumps({"0": "completed", "1": "in_progress"})
    cursor.execute("""
        UPDATE guide_executions 
        SET checklist_status_json = ?, steps_status_json = ?, status = 'in_progress'
        WHERE id = ?
    """, (checklist_status, steps_status, exec_id))
    test('UPDATE 成功 (勾选状态持久化)', cursor.rowcount > 0)
    
    # 验证更新后的数据
    cursor.execute('SELECT checklist_status_json, steps_status_json, status FROM guide_executions WHERE id = ?', (exec_id,))
    row = cursor.fetchone()
    test('checklist_status_json 已存储', row[0] == checklist_status)
    test('steps_status_json 已存储', row[1] == steps_status)
    test('status 已更新为 in_progress', row[2] == 'in_progress')
    
    # DELETE - 清理测试数据
    cursor.execute('DELETE FROM guide_executions WHERE id = ?', (exec_id,))
    test('DELETE 成功', cursor.rowcount > 0)
else:
    print('  ⚠️ 跳过 CRUD 测试 (缺少 guide_id 或 ticket_id)')

conn.commit()
conn.close()

print()
print('=' * 60)
print(f'  测试结果: {PASS} 通过 / {PASS + FAIL} 总计')
if FAIL == 0:
    print('  ✅ 全部通过！')
else:
    print(f'  ❌ {FAIL} 项未通过')
print('=' * 60)
