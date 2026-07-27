"""
初始数据填充
- 判空规则：只有 users 表为空才执行，避免重复插入
- 随机用户数 + 随机工单数 + 随机案例/指南数（池化生成，避免硬编码）
- 所有时间锚定在 2026-01-01 ~ now 之间（比赛演示年度统一）
- 通过 `python -m backend.app.reset_seed` 可清库重植
"""

from __future__ import annotations
import json
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from .models import (
    User, Device, Ticket, Case, Guide, KnowledgeReport,
    DEVICE_STATUS_NORMAL, DEVICE_STATUS_REPAIRING, DEVICE_STATUS_DOWN,
    TICKET_PENDING, TICKET_DOING, TICKET_DONE, TICKET_OVER,
    REPORT_PENDING, REPORT_APPROVED, REPORT_REJECTED,
    REPORT_SYNCED_CASE, REPORT_SYNCED_GUIDE,
    REPORT_SOURCE_SEARCH, REPORT_SOURCE_TICKET, REPORT_SOURCE_MANUAL,
    TYPE_CASE, TYPE_GUIDE,
)
from .users import ROLE_SYSADMIN, ROLE_MANAGER, ROLE_WORKER
from .auth import hash_password

# ============================================================
# 日期锚点：2026-01-01 ~ now，所有种子数据落在此区间
# ============================================================
_ANCHOR_2026 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_NOW = datetime.now(timezone.utc)
_DAYS_SINCE_2026 = max(1, (_NOW - _ANCHOR_2026).days)


def _ts_2026(max_days_ago: int | None = None) -> datetime:
    """2026-01-01 ~ now 之间的随机时间戳"""
    upper = _DAYS_SINCE_2026
    if max_days_ago is not None:
        upper = min(upper, max_days_ago)
    days = random.randint(0, upper)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    return _NOW - timedelta(days=days, hours=hours, minutes=minutes)


def _short_id(prefix: str, n: int) -> str:
    return f"{prefix}-{str(n).zfill(3)}"


# ============================================================
# 随机配置池
# ============================================================
_SEED_CFG = {
    "n_workers": (3, 6),
    "n_tickets": (40, 80),
    "n_pending_ratio": (0.10, 0.20),
    "n_doing_ratio": (0.20, 0.35),
    "n_done_ratio": (0.45, 0.65),
    "n_cases": (15, 30),
    "n_guides": (8, 15),
}

_SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻窦章云苏潘葛奚范彭郎鲁马苗凤花方俞任袁柳"
_TITLES = "主任 师傅 工 工程师 班长 技术员 安全员 组长 作业员 巡检员".split()
_AVATAR_PRESETS = [f"preset:{i}" for i in range(1, 7)]

# 工单标题池（按设备 tag 随机组合 + 具象化）
_FAULT_TEMPLATES = [
    ("{dev} 主轴异响，加工表面振纹超标", "机械"),
    ("{dev} 液压油温过高报警（当前 {temp}℃）", "液压"),
    ("{dev} 压力漂移示值不稳", "仪表"),
    ("{dev} 冷却泵流量不足", "机械"),
    ("{dev} 控制柜温度过高告警", "电气"),
    ("{dev} 刀库换刀失败", "机械"),
    ("{dev} 润滑油泵启动失败", "液压"),
    ("{dev} 皮带跑偏，摩擦冒烟", "机械"),
    ("{dev} 变频器过载跳闸 F30001", "电气"),
    ("{dev} 安全阀起跳后无法完全回座", "安全"),
    ("{dev} 轴承温度超限报警（{temp}℃）", "机械"),
    ("{dev} 电磁流量计空管误报警", "仪表"),
    ("{dev} 紧急停机按钮无响应", "安全"),
    ("{dev} PLC 通讯 BF 灯闪断", "电气"),
    ("{dev} 液压系统压力建不起来", "液压"),
    ("{dev} 注塑机料筒温度超调", "机械"),
    ("{dev} 电机振动值超标 {vib}mm/s", "机械"),
    ("{dev} 配电柜红外测温超限", "电气"),
    ("{dev} 比例阀中位漂移", "液压"),
    ("{dev} 锅炉水位假液位", "仪表"),
    ("{dev} 离心泵入口汽蚀振动", "机械"),
    ("{dev} 伺服驱动器过流报警", "电气"),
    ("{dev} 液压缸爬行抖动", "液压"),
    ("{dev} 压力变送器 HART 零点漂移", "仪表"),
]


# ============================================================
# 1. 用户（2 管理员 + 随机 3~6 维修工）
# ============================================================


def _create_users(db: Session) -> dict[str, User]:
    """
    固定账号（比赛评委演示用）：
      admin / ad1234    → 赵五  （维修管理员）
      worker1 / 123456  → 李建华（维修工，资深，done 多）
      worker2 / 234567  → 张伟  （维修工，中生代，doing 多）
      worker3 / 345678  → 黄丽  （维修工，新人，pending/doing 一般）
    + 2 个临时用户 extra01/extra02，专门承接 over 工单（3 个测试用户都没有超期工单）
    """
    fixed = [
        # username, password, fullname, role, avatar, dept, position, emp_no, join_date
        ("admin",   "ad1234",  "赵五",   ROLE_SYSADMIN, "preset:1",
            "设备管理部", "系统管理主管", "EMP-ADM-001", "2021-03-18",
            "139****9527", "admin@equipai.com", "021-8888-0001", "主厂区·中心办公楼 A801"),
        ("worker1", "123456", "李建华", ROLE_WORKER, "preset:3",
            "设备维修中心·机械工段", "高级维修工程师", "EMP-W-0101", "2019-07-02",
            "138****1122", "lijh@equipai.com", "021-8888-1101", "主厂区·维修车间 A207"),
        ("worker2", "234567", "张伟",   ROLE_WORKER, "preset:2",
            "设备维修中心·电气工段", "维修技师", "EMP-W-0201", "2021-11-15",
            "137****3344", "zhangw@equipai.com", "021-8888-1201", "副楼·综合维修间 B305"),
        ("worker3", "345678", "黄丽",   ROLE_WORKER, "preset:5",
            "生产运营部·巡检组", "巡检员", "EMP-W-0301", "2023-05-20",
            "136****5566", "huangl@equipai.com", "021-8888-1301", "B车间·工具房"),
        # 临时用户：承接 over 工单（3 个演示账号不出现超期），密码统一 123456
        ("extra01", "123456", "孙师傅", ROLE_WORKER, "preset:4",
            "设备维修中心·液压工段", "液压技师", "EMP-W-0401", "2020-09-08",
            "135****7788", "sunshifu@equipai.com", "021-8888-2001", "B车间·液压间"),
        ("extra02", "123456", "周师傅", ROLE_WORKER, "preset:6",
            "动力车间·泵站", "机械维修技工", "EMP-W-0501", "2022-02-14",
            "134****9900", "zhoushifu@equipai.com", "021-8888-2101", "动力车间·泵站"),
    ]
    out: dict[str, User] = {}
    for uname, pwd, fname, role, avt, dept, pos, emp_no, jdate, mb, em, tl, off in fixed:
        u = User(
            username=uname,
            password_hash=hash_password(pwd),
            fullname=fname,
            role=role,
            avatar_preset=avt,
            created_at=_ts_2026(max_days_ago=200),
            dept=dept, position=pos, emp_no=emp_no, join_date=jdate,
            mobile=mb, email=em, tel=tl, office=off,
        )
        db.add(u); out[uname] = u
    db.flush()
    return out


# ============================================================
# 2. 设备（6 大类共 120 台）
# ============================================================
_DEVICE_TYPES = [
    # tag, prefix, name_template, 数量, 位置模板
    # 机械动力设备
    ("机械动力", "P",    "离心泵 {}",              12, "动力车间·泵站-{}"),
    ("机械动力", "AC",   "空压机 {}",               8, "压缩空气站·{} 号机组"),
    ("机械动力", "FAN",  "风机 {}",                6, "通风系统·{} 号风机"),
    ("机械动力", "GB",   "减速机 {}",              5, "传动单元·{} 号"),
    # 智能制造设备
    ("智能制造", "MC",   "CNC 加工中心 {}",       15, "A 车间·精加工单元-{}"),
    ("智能制造", "LC",   "数控车床 {}",            12, "A 车间·车削工段-{}"),
    ("智能制造", "HY",   "四柱液压机 {}",           6, "B 车间·冲压段-{}"),
    ("智能制造", "CV",   "皮带输送机 {}",           8, "C 车间·物流线-{}"),
    # 电气控制设备
    ("电气控制", "PD",   "低压配电柜 {}",           8, "配电房 {} 号柜"),
    ("电气控制", "VFD",  "变频器驱动站 {}",         7, "A 车间·变频间-{}"),
    ("电气控制", "PLC",  "PLC 控制站 {}",           7, "中央控制室 S{}"),
    # 液压与执行设备
    ("液压执行", "HP",   "液压动力站 {}",           6, "B 车间·液压间 {}"),
    ("液压执行", "VA",   "比例阀组 {}",             6, "B 车间·阀岛 {}"),
    # 工业仪表设备
    ("工业仪表", "PT",   "压力变送器 {}",           8, "管廊 {} 号节点"),
    ("工业仪表", "FT",   "电磁流量计 {}",           5, "管廊 {} 号主管"),
    # 安全保护设备
    ("安全保护", "ESD",  "紧急停机系统 {}",          4, "全车间·ESD 站 {}"),
    ("安全保护", "SG",   "安全光幕 {}",             4, "加工单元·{} 号门"),
    ("安全保护", "SV",   "安全阀 {}",              5, "锅炉房·{} 号"),
]


def _create_devices(db: Session) -> list[Device]:
    devices: list[Device] = []
    idx = 1
    for tag, prefix, name_tpl, count, loc_tpl in _DEVICE_TYPES:
        for seq in range(1, count + 1):
            code = _short_id(prefix, seq)
            # 状态分布：正常 88%，维修中 7%，故障停机 5%
            r = idx % 100
            if r < 5:
                status = DEVICE_STATUS_DOWN
            elif r < 12:
                status = DEVICE_STATUS_REPAIRING
            else:
                status = DEVICE_STATUS_NORMAL
            last_repair = (
                _ts_2026(max_days_ago=120)
                if status != DEVICE_STATUS_NORMAL else None
            )
            dev = Device(
                code=code,
                name=name_tpl.format(seq),
                tag=tag,
                location=loc_tpl.format(seq),
                status=status,
                last_repair_at=last_repair,
            )
            db.add(dev)
            devices.append(dev)
            idx += 1
    db.flush()
    return devices


# ============================================================
# 3. 工单（30 条：5 待派 + 8 进行中 + 15 完成 + 2 超时）
# ============================================================
_TICKET_TITLES = [
    "{} 主轴异响，加工表面振纹超标",
    "{} 液压油温过高报警",
    "{} 出现压力漂移示值不稳",
    "{} 冷却泵流量不足",
    "{} 控制柜温度过高告警",
    "{} 刀库换刀失败",
    "{} 润滑油泵启动失败",
    "{} 皮带跑偏，摩擦冒烟",
    "{} 变频器过载跳闸",
    "{} 安全阀起跳后无法完全回座",
]


def _create_tickets(db: Session, users: dict[str, User], devices: list[Device]) -> None:
    admins = [u for u in users.values() if u.role != ROLE_WORKER]
    if not admins:
        admins = [u for u in users.values()][:1]

    # 按账号用途分成 3 个池子（严格避免 3 个测试用户接到 over 工单）
    core_w1 = users.get("worker1")
    core_w2 = users.get("worker2")
    core_w3 = users.get("worker3")
    over_pool = [users.get("extra01"), users.get("extra02")]
    over_pool = [u for u in over_pool if u is not None]
    core_all = [u for u in (core_w1, core_w2, core_w3) if u is not None]
    # pending 接单池 + 转派池：可以包含 core_all + over_pool，所有维修工都能被派
    all_workers = core_all + over_pool

    # —— 固定工单数配置 ——
    # worker1: 待处理3 + 处理中4 + 已完成10 = 17
    # worker2: 待处理1 + 处理中5 + 已完成12 = 18
    # worker3: 待处理2 + 处理中3 + 已完成9 = 14
    # extra01/02: over + 少量其他
    done_splits = [10, 12, 9, 5]
    doing_splits = [4, 5, 3, 3]
    pend_per_core = [3, 1, 2]
    pend_unassigned = 4
    n_over = 2
    n_done = sum(done_splits)
    n_doing = sum(doing_splits)
    n_pend = sum(pend_per_core) + pend_unassigned
    total = n_done + n_doing + n_pend + n_over

    count = 0
    SOLUTION_STEPS = [
        "1. 停机断电挂牌；\n2. 拆解相关部件，确认失效点；\n3. 按原厂规格更换备件并调整间隙；\n4. 带载试机 2 小时温度、振动、电流均正常后交付生产。",
        "① 现场停机降温至 40℃ 以下；② 用振动分析仪定位故障轴承；③ 更换同规格 SKF 轴承；④ 监测 48h 振动值达标。",
        "1. 清洁并重新紧固所有接线端子；\n2. 复测绝缘电阻 >10MΩ；\n3. 空载 / 半载 / 满载三段试运行；\n4. 加入季度巡检计划。",
        "① 清洗入口 Y 型滤网并更新滤芯；② 调整系统压力至上限 -10%；③ 连续运行 72h 观察趋势；④ 与操作工完成交接。",
    ]

    def _pick_solution():
        return random.choice(SOLUTION_STEPS)

    def _one(status: str, submit_time: datetime, assignee: User | None, solution: str | None):
        nonlocal count
        count += 1
        dev = random.choice(devices)
        title_template, _ = random.choice(_FAULT_TEMPLATES)
        temperature = random.randint(60, 95)
        vibration = round(random.uniform(3.0, 9.5), 1)
        title = title_template.format(dev=dev.name, temp=temperature, vib=vibration)
        finish_time = None
        if status in (TICKET_DONE, TICKET_OVER):
            max_finish = min(_NOW, submit_time + timedelta(days=3))
            delta = timedelta(hours=random.randint(2, 36), minutes=random.randint(0, 59))
            finish_time = min(max_finish, submit_time + delta)
        code = f"TK-{submit_time.strftime('%Y%m%d')}-{str(count).zfill(3)}"
        level = random.choice(["low", "mid", "mid", "mid", "mid", "high", "critical"])
        problem_flavor = random.choice([
            f"现场报告问题：{title}\n初步观察：设备运行电流高于额定 {random.randint(8,25)}%，振动值 {vibration}mm/s。",
            f"现象：{title}\n已检查：三相电压平衡，无缺相；当前振动 {vibration}mm/s。",
            f"问题：{title}\n夜班已带病运行 4h，申请立即停机处理。",
        ])
        ticket = Ticket(
            code=code, title=title,
            device_id=dev.id, device_name=f"{dev.code} {dev.name}",
            level=level, status=status,
            submitter_id=random.choice(admins).id,
            assignee_id=assignee.id if assignee else None,
            problem=problem_flavor,
            solution=solution,
            submit_time=submit_time,
            finish_time=finish_time,
        )
        db.add(ticket)

    def _many(n, status, worker_iter, submit_days, solution_factory):
        for _ in range(max(0, n)):
            try:
                w = next(worker_iter)
            except StopIteration:
                w = None
            sol = solution_factory() if solution_factory else None
            _one(status, _ts_2026(max_days_ago=submit_days), w, sol)

    def _cycle(workers, n):
        """按数量循环产出 worker，支持 [w1,w2,w3] + 各数量分布"""
        i = 0
        while i < n:
            for w in workers:
                if i >= n:
                    return
                yield w
                i += 1

    # ============ 时间分配：近 7 天强制均匀 + 远期均匀 ============
    def _distribute(n, recent=7, far=120):
        """返回 n 个 day_ago 列表：一半均匀落在 [0,recent)，一半均匀落在 [recent,far)"""
        half = n // 2
        out = []
        for i in range(half):
            out.append(int(i / max(1, half) * recent))            # 近 7 天
        for i in range(n - half):
            out.append(recent + int(i / max(1, n - half) * (far - recent)))  # 远期
        random.shuffle(out)
        return out

    def _fixed_ts(day_ago: int) -> datetime:
        """精确到某一天（当天随机时分），确保折线图该天计数准确"""
        d = _NOW - timedelta(days=day_ago)
        return d.replace(hour=random.randint(7, 22), minute=random.randint(0, 59), second=random.randint(0, 59))

    # ============ done ============
    # w1(资深): 45%  w2(中生代):30%  w3(新人):15%  extra:10%
    done_workers = (
        [core_w1] * done_splits[0] +
        [core_w2] * done_splits[1] +
        [core_w3] * done_splits[2] +
        [random.choice(over_pool) for _ in range(done_splits[3])]
    )
    random.shuffle(done_workers)
    done_days = _distribute(len(done_workers))
    for i, w in enumerate(done_workers):
        _one(TICKET_DONE, _fixed_ts(done_days[i]), w, _pick_solution())

    # ============ doing ============
    # w1: 20%  w2:45%  w3:25%  extra:10%
    doing_workers = (
        [core_w1] * doing_splits[0] +
        [core_w2] * doing_splits[1] +
        [core_w3] * doing_splits[2] +
        [random.choice(over_pool) for _ in range(doing_splits[3])]
    )
    random.shuffle(doing_workers)
    doing_days = _distribute(len(doing_workers))
    for i, w in enumerate(doing_workers):
        _one(TICKET_DOING, _fixed_ts(doing_days[i]), w, None)

    # ============ pending（全部未分配，进入管理员派单池） ============
    n_pend_total = sum(pend_per_core) + pend_unassigned
    pend_days = _distribute(n_pend_total, recent=3, far=10)
    for i in range(n_pend_total):
        _one(TICKET_PENDING, _fixed_ts(pend_days[i]), None, None)

    # ============ over（超期）：只派给 extra01/extra02，3 个测试用户永远不出现 over ============
    for i in range(n_over):
        _one(TICKET_OVER, _fixed_ts(80 + i * 15),
             over_pool[i % len(over_pool)] if over_pool else None,
             "备件采购延误，预计 24 小时内到货更换。")

    db.flush()


# ============================================================
# 4. 案例库（20 条，其中 1 条来自知识报告入库）
# ============================================================
_CASE_SPECS = [
    # (title, device_prefix_seq, tag, fault, cause, solution, level)
    ("CNC 加工中心主轴异响、振纹快速排查", ("MC", 1), "机械",
     "精切 45# 钢表面振纹 Ra>3.2，主轴 3000rpm 时异响明显",
     "主轴前轴承预紧力不足+刀柄拉钉磨损",
     "① 拉钉替换为 SK40 新件；② 拆开主轴端盖，前轴承外圈背帽按原厂扭矩 120N·m 重新预紧；③ 热机 40min 跑合后复测振纹 Ra=0.8。",
     "high"),
    ("离心泵异常振动+出口压力波动", ("P", 3), "机械",
     "出口压力 0.6~1.1MPa 波动，轴承端振动 8.5mm/s",
     "入口滤网堵塞 70%+ 联轴器橡胶块开裂 3 处",
     "① 拆洗入口 Y 型滤网并更换新滤网；② 更换联轴器弹性块并重新找正同轴度≤0.05mm；③ 空载/半载/满载三段试机均正常。",
     "mid"),
    ("低压配电柜温升超限处理", ("PD", 2), "电气",
     "夏季环境 35℃ 时柜内温度达 62℃，温度传感器告警",
     "柜顶散热风机失效+进线母排端子氧化",
     "① 更换 2 台柜顶风机并加装防尘滤网；② 母排端子拆除打磨后重刷导电膏，按力矩表重新紧固；③ 柜内加装 4 台轴流风机，温度下降至 48℃。",
     "mid"),
    ("变频器过载跳闸（G120）", ("VFD", 3), "电气",
     "F30001 过流，启动阶段即跳闸",
     "输出电缆 C 相绝缘下降（MΩ 级 0.8M 小于要求 1M），电机轴承磨损导致启动电流偏大",
     "① 摇表分 4 段排查确认电缆中段绝缘破口，更换；② 电机后轴承 SKF 6308-2RS 更换；③ 变频器 V/f 曲线重新优化启动段，启动电流稳定在 2.1Ie 以下。",
     "high"),
    ("液压动力站系统压力建不起来", ("HP", 1), "液压",
     "系统表压始终 <2MPa，远低于设定 10MPa",
     "变量泵斜盘卡住+比例溢流阀阀芯阻尼孔堵塞",
     "① 拆泵清洗斜盘滑靴，更换密封件；② 超声清洗溢流阀阻尼孔，阀芯研磨光滑；③ 重新系统排气+补油，表压稳定 10.2MPa。",
     "high"),
    ("压力变送器零点漂移（HART 校准法）", ("PT", 4), "仪表",
     "示值偏差 3.5%，与实验室标准表不符",
     "管道压力波动累积致传感器零点偏移，非硬件故障",
     "① HART 475 连接变送器端子，进入校准菜单；② 大气压下执行 3 次零点采集；③ 标准压力源 80%FS 高点校准；④ 重启后误差 <0.2%。",
     "low"),
    ("电磁流量计空管误报警屏蔽技巧", ("FT", 2), "仪表",
     "液位波动时频繁报 Empty Pipe，流量跳变",
     "电极表面结垢导致空管判断阈值过于敏感",
     "① 拆下清洗电极并抛光；② 菜单中将 Empty Pipe Threshold 从 90% 降为 75%；③ 启用空管保持 3s 防抖，误报警消除。",
     "low"),
    ("紧急停机按钮无响应故障", ("ES", 1), "安全",
     "按下急停，A 车间输送机仍然运行",
     "ESD 回路中继电器 K3 触点烧蚀粘连，PLC 输入仍为 1",
     "① 立即拉总闸停机；② 更换 K3 继电器（24V DC 10A）并做 3 次回路测试；③ 每日班前增加急停抽检环节，纳入 SOP。",
     "high"),
    ("安全阀起跳后密封泄漏处理", ("SV", 2), "安全",
     "起跳后回座仍然有微小泄漏，压力表缓慢下降",
     "密封面有细小颗粒物嵌入+弹簧预紧不足",
     "① 拆安全阀研磨密封面（凡尔砂+研磨膏分级）；② 调整预紧螺栓按校验台设定压力；③ 校验台整定合格后回装，气密 10min 无压降。",
     "mid"),
    ("皮带输送机皮带偏磨处理", ("CV", 5), "机械",
     "回程段皮带单侧磨损，边缘毛化",
     "尾轮轴线与头轮不平行+回程托辊架位移",
     "① 调整尾轮张紧丝杆重新找正；② 回程托辊架重新螺栓紧固+加防松垫片；③ 每 20m 安装 1 组自动纠偏托辊，运行 8h 不跑偏。",
     "mid"),
    ("PLC 通讯中断 Profibus DP 闪断", ("PLC", 4), "电气",
     "站点偶发丢失，BF 灯闪 1~3s 自动恢复",
     "总线终端电阻接触不良+第 5 站总线连接器氧化",
     "① 两端终端电阻重新焊接并确认拨码 ON；② 更换 5# 站连接器；③ 屏蔽层单端接地整改，连续 72 小时通讯 0 丢包。",
     "mid"),
    ("液压缸爬行抖动", ("HC", 1), "液压",
     "伸出阶段 50~200mm 段爬行明显，工件定位不准",
     "缸筒内拉毛+活塞杆密封件磨粒磨损",
     "① 镗缸+珩磨修复内孔；② 更换整套密封（格莱圈+斯特封）；③ 空载 30 次跑合后重载测试，定位重复精度 ≤0.02mm。",
     "high"),
    ("数控车床 X 轴丝杠反向间隙大", ("LC", 2), "机械",
     "G01 反向时丢步 0.08~0.12mm，加工尺寸分散",
     "丝杠螺母预紧松+伺服增益匹配偏低",
     "① 双螺母垫片法重新消隙，测出反向间隙 0.03mm 补偿入 1851 参数；② 伺服环增益 2 倍整定；③ 激光干涉仪复检，精度恢复出厂值。",
     "mid"),
    ("注塑机料筒温度超调", ("IM", 1), "机械",
     "3 段温度设定 220℃ 实际冲至 248℃，产品焦料",
     "固态继电器击穿常通+冷却水路水垢堵塞",
     "① 更换 SSR 三相固态+温控模块输出加保险；② 水路草酸清洗+加装过滤器；③ PID 参数重新自整定，温度稳定 ±2℃。",
     "high"),
    ("液压阀组响应慢动作延迟", ("VA", 3), "液压",
     "换向信号给到后执行器延迟 0.8~1.5s",
     "先导控制油堵塞+电磁铁剩磁",
     "① 阀组超声波清洗各阻尼孔；② 电磁铁换用低剩磁规格；③ 响应时间缩短至 ≤120ms。",
     "mid"),
    ("温度变送器接线端子氧化", ("TT", 2), "仪表",
     "指示值偶发跳变，用手按接线端子恢复正常",
     "室外桥架接线盒进水致铜端子氧化",
     "① 更换镀锡接线端子并缠绕自融胶带；② 接线盒密封胶圈重新安装；③ 重新做三线制 6 位线校验，跳变消除。",
     "low"),
    ("安全光幕常被切屑误触发", ("LC", 1), "安全",
     "加工铸铁件时光幕被飞出切屑间歇遮断，机台误停",
     "光幕安装距离过近+切屑角度正好穿过光幕光路",
     "① 光幕移至安全门外侧 300mm 处；② 增加 100ms 遮光防抖；③ 切屑防护罩加装橡胶帘，停机率下降 95%。",
     "low"),
    ("电机轴承异音带电判断", ("M", 1), "电气",
     "停机后声音消失，运行中嗡鸣明显",
     "电机轴电流导致轴承滚道电蚀",
     "① 电机负荷端加装绝缘端盖；② 变频器输出侧加装 dv/dt 滤波器；③ 轴接地碳刷重新压接，异音消除。",
     "high"),
    ("锅炉水位假液位排查", ("LT", 1), "仪表",
     "水位显示波动 200mm，现场磁翻板一致，但实际缺水",
     "平衡容器正压侧水封破坏+汽水共腾",
     "① 重注水封+加伴热避免汽化；② 炉水磷酸三钠加药量调整，排污 3 次后汽水共腾消除；③ 液位恢复稳定。",
     "mid"),
    ("比例方向阀中位漂移", ("VA", 5), "液压",
     "指令信号 0% 时执行器仍缓慢漂移",
     "阀芯对中弹簧疲劳+阀体内杂质卡滞",
     "① 清洗阀芯+更换弹簧；② 放大器零位重新校准；③ 中位泄漏量降至原厂规格 1/10 以下。",
     "mid"),
]


def _create_cases(db: Session, devices_by_code: dict[str, Device]) -> tuple[list[Case], Case]:
    cases: list[Case] = []
    for i, (title, (p, s), tag, fault, cause, sol, lvl) in enumerate(_CASE_SPECS):
        code = _short_id(p, s)
        dev = devices_by_code.get(code)
        case = Case(
            title=title,
            device=f"{dev.code} {dev.name}" if dev else f"{code} 通用设备",
            tag=tag,
            fault=fault,
            cause=cause,
            solution=sol,
            summary=sol[:80] + ("…" if len(sol) > 80 else ""),
            level=lvl,
            created_at=_ts_2026(max_days_ago=120),
        )
        db.add(case)
        cases.append(case)
    db.flush()
    # 最后一个 case 留给"员工贡献入库"，返回给报告关联用
    return cases, cases[-1]


# ============================================================
# 5. 作业指导（10 条，分 5 类）
# ============================================================
_GUIDE_SPECS = [
    ("CNC 主轴周维护 SOP",          "机械", "机械·主轴",
     30, "高速旋转部件，必须断电挂牌",
     [
         ("安全准备", "停机→断电→挂 LOTO 安全锁→主轴完全静止 ≥5min", "严禁主轴未停手触刀柄"),
         ("外观清理", "高压气枪吹净主轴锥孔及换刀臂粉尘，目视无切屑", "压缩空气气压 ≤0.4MPa"),
         ("拉钉检查", "抽出 SK40 拉钉检查头部磨损，磨损 >0.1mm 更换", "使用专用拉钉扳手紧固 90N·m"),
         ("润滑补脂", "主轴轴承注脂嘴补加润滑脂 2 泵，严禁过量", "过量润滑会导致温度升高 10℃+"),
         ("试机跑合", "摘除锁牌，S1/S2/S3 转速各跑 10min，温度稳定 ≤60℃ 交付", "温度异常立即停机排查"),
     ]),
    ("离心泵切换备用泵作业",        "机械", "机械·泵类",
     15, "防止断流致系统失压",
     [
         ("检查备用", "备用泵盘车灵活、入口阀全开、油位在上刻线", "倒灌系统需先排气"),
         ("启动备用", "按启动按钮，观察出口压力达到额定 90% 以上", "压力不起来立即停止再排气"),
         ("逐步切换", "缓开备用出口阀，同时缓关在用出口阀，系统压力波动 <5%", "快速切换会产生水锤"),
         ("停泵隔离", "在用泵完全关出口阀后按下停止，关闭入口阀", "冬季长期停泵要排净泵腔存水"),
         ("记录归档", "记录切换时间、压力、电流、异常情况", "纳入设备履历台账"),
     ]),
    ("变频器日常巡检规程",          "电气", "电气·变频",
     10, "高温/高湿环境严格执行",
     [
         ("环境确认", "确认变频室温度 10~40℃、湿度 <85%RH，无凝露", "超温自动报警阈值 50℃"),
         ("显示检查", "读取 HMI 运行电流、电压、母线直流电压，与记录值偏差 <10%", "母线电压突变 ≥30V 立即检查输入"),
         ("散热检查", "散热器出风温度 <60℃、风机无异响、滤网无积尘", "每月更换滤网"),
         ("端子检查", "停电后检查输入输出端子无变色、无异味，按力矩重紧", "力矩不够是变频器损坏首因"),
         ("记录归档", "三相电流不平度 <5% 为正常，否则排查电机电缆", ""),
     ]),
    ("HART 压力变送器三点校准",     "仪表", "仪表·压力",
     45, "必须使用经检定的标准压力源",
     [
         ("安全隔离", "关闭引压阀，打开平衡阀泄压，变送器断电", "严禁带压拆变送器"),
         ("接线准备", "HART 手操器 250Ω 串联，通讯地址确认 0 或 1", "手操器极性不能反"),
         ("零点校准", "通大气条件下，菜单中执行 Zero Trim 3 次取均值", "不要在校准台上猛加压"),
         ("中点校准", "标准压力源加 50%FS，确认示值误差 ≤±0.1%", "不稳就再等 30s"),
         ("高点校准", "加压 100%FS，执行 Span Trim，重紧过程接头", "完毕再回零点做回差检查"),
     ]),
    ("紧急停机系统月度功能测试",     "安全", "安全·ESD",
     20, "生产停机窗口执行，提前通知当班",
     [
         ("方案审批", "当班主管签字批准，记录窗口时间 15min", "未审批禁止测试"),
         ("通知相关", "广播通知现场操作人员远离运动部件", "鸣笛 3 声再开始"),
         ("逐一测试", "逐个按下急停按钮（含拉线急停），确认所有受控设备 0.3s 内断电", "超时立即停机排查回路"),
         ("复位恢复", "全部测试完成，复位 ESD 控制器，报警灯绿色闪烁", "禁止短接报警信号"),
         ("签字归档", "测试人、见证人、主管三方签字，保存测试记录 3 年", "未通过整改后 24h 内复测"),
     ]),
    ("液压站换油冲洗作业",          "液压", "液压·泵站",
     90, "废油必须分类回收，严禁直排",
     [
         ("排空旧油", "停泵降温 60℃ 以下，从油箱底部球阀放油至干净油桶", "注意油液飞溅防护"),
         ("油箱清理", "面粉团法粘除底部油泥杂质，用白布擦净内壁无可见污物", "严禁使用棉纱易掉毛材料"),
         ("循环冲洗", "加 1/3 冲洗油，拆除执行器油管短接，循环 30min 后排净", "泵吸口加 100μm 临时滤芯"),
         ("加注新油", "经滤油机 3μm 过滤注入新油至油标中线", "禁止不同品牌液压油混加"),
         ("跑合验收", "空载循环 1 小时，油温 40±5℃，清洁度 NAS8 级合格", "取样送检留存"),
     ]),
    ("配电柜红外测温巡检",          "电气", "电气·配电",
     12, "严禁打开柜门裸手触碰铜排",
     [
         ("仪器校准", "红外测温仪距目标 ≤500mm，发射率 0.85~0.95", "避开阳光直射反光"),
         ("进线母排", "测量 A/B/C/N 三相母排搭接处，温度差 ≤15K", "某相高 20K 必须停电检查"),
         ("出线端子", "逐一测各断路器上下端子，记录温升曲线", "和历史数据对比 >10K 重紧"),
         ("电容补偿", "测电容器外壳温度 ≤55℃、无鼓包漏液", "电容超温 60℃ 立即退出运行"),
         ("记录归档", "红外照片+温度台账，夏季每月增加一次特巡", ""),
     ]),
    ("电磁流量计零点校准",          "仪表", "仪表·流量",
     20, "管内必须满管且完全静止",
     [
         ("工艺准备", "关前后截止阀，保证满管静止 ≥10min", "不满管零点无意义"),
         ("电极检查", "HART 读电极回路电阻，三相平衡 <10%", "不平衡则拆下清洗电极"),
         ("零点写入", "执行 Zero Adjust，等 30s 确认稳定再保存", "保存后不要立即开阀"),
         ("工艺恢复", "缓开前后阀，观察 5min 流量与参考值对比", "偏差 <0.5% 合格"),
         ("记录归档", "零点值、电极电阻值、环境温度记录", ""),
     ]),
    ("PLC 控制器电池更换作业",      "电气", "电气·PLC",
     10, "失电会丢失程序，必须带电换",
     [
         ("主机通电", "PLC 必须处于通电状态 ≥5min，防止电容放电完成", "断电换电池 = 丢程序"),
         ("开盖定位", "打开 CPU 模块盖板，找到锂电池型号（通常 CR2032 / 3.6V 锂电池）", "确认型号完全一致"),
         ("快速更换", "按住卡扣取下旧电池，30 秒内插入新电池（正极朝上）", "超时可能丢程序"),
         ("验证检查", "CPU BAT 指示灯灭，进入监控模式看时钟和数据区保持", "电池灯亮则未接触好"),
         ("旧电池回收", "贴标签作危险废弃物回收，严禁投入生活垃圾桶", ""),
     ]),
    ("安全光幕功能检查",            "安全", "安全·光幕",
     8, "每班班前执行，必须双人确认",
     [
         ("外观检查", "发射/接收端无油污、支架牢固、电缆护套无破损", "损坏立即停用"),
         ("遮挡测试", "不透明测试棒逐段穿过光轴，每一段都能触发停机", "必须覆盖上下两端 10% 边界"),
         ("旁路禁用", "检查光幕旁路开关处于 OFF 且加铅封", "旁路启用禁止生产"),
         ("复位测试", "清除遮挡，按复位按钮机台才能再次启动", "自动复位属严重违规"),
         ("记录归档", "双人签字，不合格禁止开机", ""),
     ]),
]


def _create_guides(db: Session) -> tuple[list[Guide], Guide]:
    """从 knowledge/data/guides.json 读作业指导并写入数据库。"""
    guides_file = Path(__file__).resolve().parent.parent.parent / "knowledge" / "data" / "guides.json"
    with open(guides_file, "r", encoding="utf-8") as f:
        specs = json.load(f)

    guides: list[Guide] = []
    for spec in specs:
        steps_obj = [
            {"step": s.get("step", i + 1), "content": s.get("content", ""), "tip": s.get("tip", "")}
            for i, s in enumerate(spec.get("steps", []))
        ]
        checklist = spec.get("checklist", [])
        prep = spec.get("preparation", [])
        safety = spec.get("safety_control", [])
        accept = spec.get("acceptance_criteria", [])
        stop = spec.get("stop_conditions", [])
        g = Guide(
            title=spec.get("title", ""),
            device_type=spec.get("device_type", "机械"),
            tag=spec.get("tag"),
            steps_json=json.dumps(steps_obj, ensure_ascii=False),
            risk_note=spec.get("risk_note"),
            duration_min=spec.get("duration_min"),
            difficulty=spec.get("difficulty"),
            tools_json=json.dumps(spec.get("required_tools", []), ensure_ascii=False) if spec.get("required_tools") else None,
            applicable_devices=spec.get("applicable_devices"),
            scope=spec.get("scope"),
            maintenance_level=spec.get("maintenance_level"),
            checklist_json=json.dumps(checklist, ensure_ascii=False) if checklist else None,
            preparation_json=json.dumps(prep, ensure_ascii=False) if prep else None,
            safety_control_json=json.dumps(safety, ensure_ascii=False) if safety else None,
            acceptance_criteria_json=json.dumps(accept, ensure_ascii=False) if accept else None,
            stop_conditions_json=json.dumps(stop, ensure_ascii=False) if stop else None,
            created_at=_ts_2026(max_days_ago=180),
        )
        db.add(g)
        guides.append(g)
    db.flush()
    return guides, guides[-1]


# ============================================================
# 6. 知识报告（5 条：2 待审 + 1 入库案例 + 1 入库指南 + 1 驳回）
# ============================================================
def _create_reports(
    db: Session,
    users: dict[str, User],
    devices_by_code: dict[str, Device],
    sync_case: Case,
    sync_guide: Guide,
) -> None:
    now = datetime.now(timezone.utc)
    workers_core = [users.get(k) for k in ("worker1", "worker2", "worker3")]
    workers_core = [u for u in workers_core if u is not None]
    pool = workers_core or [u for u in users.values() if u.role == ROLE_WORKER]
    admin = users.get("admin") or [u for u in users.values() if u.role != ROLE_WORKER][0]

    def _mk(rid, worker, device_prefix_seq, title, q, cause, sol, src, tp,
           status, review_remark=None, synced=False, tag="机械", level="mid"):
        code = _short_id(*device_prefix_seq)
        dev = devices_by_code.get(code)
        sub = now - timedelta(days=random.randint(0, 5),
                              hours=random.randint(0, 20),
                              minutes=random.randint(0, 59))
        rev = sub + timedelta(hours=random.randint(1, 8),
                              minutes=random.randint(0, 59))
        r = KnowledgeReport(
            rid=rid,
            title=title,
            device=f"{dev.code} {dev.name}" if dev else code,
            type=tp,
            source=src,
            level=level,
            tag=tag,
            question=q,
            cause=cause,
            solution=sol,
            summary=sol[:80] + ("…" if len(sol) > 80 else ""),
            status=status,
            submitter_id=worker.id,
            submitter_username=worker.username,
            submitter_name=worker.fullname,
            submit_time=sub,
            reviewer_id=admin.id if review_remark or synced else None,
            reviewer_name=admin.fullname if review_remark or synced else None,
            review_remark=review_remark,
            review_time=rev if review_remark or synced else None,
            sync_time=rev if synced else None,
        )
        db.add(r)
        db.flush()
        if status == REPORT_SYNCED_CASE and sync_case:
            sync_case.source_report_id = r.id
            sync_case.contributor_name = worker.fullname
        if status == REPORT_SYNCED_GUIDE and sync_guide:
            sync_guide.source_report_id = r.id
            sync_guide.contributor_name = worker.fullname
        return r

    db.flush()


def _create_initial_notifications(db: Session, users: dict[str, User]) -> None:
    """
    seed 完报告后，写一批初始通知让顶栏铃铛立刻有数据：
      - 管理员：收到 3 条"新报告待审核"通知（w1/w2/w3 各 1 份 pending）
      - 3 个测试用户：各收到 1 条"已驳回" + 1 条"已通过"通知
    """
    from .models import (
        Notification, NOTIFY_TYPE_REPORT_SUBMITTED,
        NOTIFY_TYPE_REPORT_APPROVED, NOTIFY_TYPE_REPORT_REJECTED,
    )
    now = datetime.now(timezone.utc)
    admin_id = users["admin"].id

    pending_reports = (
        db.query(KnowledgeReport)
        .filter(KnowledgeReport.status == REPORT_PENDING)
        .order_by(KnowledgeReport.submit_time.desc())
        .all()
    )
    for r in pending_reports[:3]:
        db.add(Notification(
            user_id=admin_id, type=NOTIFY_TYPE_REPORT_SUBMITTED,
            title=f"📝 新实践报告待审核：{r.submitter_name} 提交了《{r.title}》",
            content=(r.summary or "")[:400],
            related_id=r.id, is_read=0,
            created_at=r.submit_time + timedelta(seconds=2),
        ))

    # 每个核心用户各 1 条驳回 1 条通过
    approved = db.query(KnowledgeReport).filter(KnowledgeReport.status.in_(
        [REPORT_APPROVED, REPORT_SYNCED_CASE, REPORT_SYNCED_GUIDE]
    )).all()
    rejected = db.query(KnowledgeReport).filter(KnowledgeReport.status == REPORT_REJECTED).all()
    def _latest_by(rows, submitter_id):
        sub = [r for r in rows if r.submitter_id == submitter_id]
        return max(sub, key=lambda r: r.submit_time) if sub else None

    core_names = ["worker1", "worker2", "worker3"]
    for name in core_names:
        u = users.get(name)
        if not u:
            continue
        # 通过类通知
        r_ok = _latest_by(approved, u.id)
        if r_ok:
            db.add(Notification(
                user_id=u.id, type=NOTIFY_TYPE_REPORT_APPROVED,
                title=f"✅ 您的实践报告《{r_ok.title}》审核通过",
                content=(r_ok.review_remark or "管理员已审核通过，稍后将同步入库。")[:400],
                related_id=r_ok.id, is_read=0,
                created_at=(r_ok.review_time or now) - timedelta(minutes=random.randint(1, 40)),
            ))
        # 驳回通知
        r_bad = _latest_by(rejected, u.id)
        if r_bad:
            db.add(Notification(
                user_id=u.id, type=NOTIFY_TYPE_REPORT_REJECTED,
                title=f"❌ 您的实践报告《{r_bad.title}》被驳回",
                content=(r_bad.review_remark or "")[:400],
                related_id=r_bad.id, is_read=0,
                created_at=(r_bad.review_time or now) - timedelta(minutes=random.randint(5, 120)),
            ))
    db.flush()


# ============================================================
# 主入口
# ============================================================
def seed_if_empty(db: Session) -> bool:
    """设备表为空时执行 seed（设备是工单/报告的根基），返回是否实际执行了插入"""
    from .models import Device
    if db.query(Device).count() > 0:
        return False
    users = _create_users(db)
    devices = _create_devices(db)
    devices_by_code = {d.code: d for d in devices}
    _create_tickets(db, users, devices)
    _cases, sync_case = _create_cases(db, devices_by_code)
    _guides, sync_guide = _create_guides(db)
    _create_reports(db, users, devices_by_code, sync_case, sync_guide)
    _create_initial_notifications(db, users)
    db.commit()
    return True
