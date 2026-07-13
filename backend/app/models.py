"""
ORM 模型（SQLAlchemy 2.0 声明式）
- 时间戳全部存 UTC，避免比赛时区不一致
- 常用字段加索引，搜素快
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ============= 用户表 =============
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    fullname = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="worker")  # sysadmin/manager/worker
    avatar_preset = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # profile 扩展列（个人档案 / 个人信息编辑落库，一期加 8 列）
    emp_no = Column(String(32), nullable=True)
    dept = Column(String(64), nullable=True)
    position = Column(String(64), nullable=True)
    join_date = Column(String(10), nullable=True)   # YYYY-MM-DD，也可用 Date
    mobile = Column(String(32), nullable=True)
    email = Column(String(128), nullable=True)
    tel = Column(String(32), nullable=True)
    office = Column(String(128), nullable=True)

    # 反向关联，方便查询
    submitted_tickets = relationship(
        "Ticket", back_populates="submitter", foreign_keys="Ticket.submitter_id"
    )
    assigned_tickets = relationship(
        "Ticket", back_populates="assignee", foreign_keys="Ticket.assignee_id"
    )
    reports = relationship("KnowledgeReport", back_populates="submitter",
                           foreign_keys="KnowledgeReport.submitter_id")
    reviewed_reports = relationship("KnowledgeReport", back_populates="reviewer",
                                    foreign_keys="KnowledgeReport.reviewer_id")
    notifications = relationship("Notification", back_populates="user",
                                 foreign_keys="Notification.user_id", cascade="all, delete-orphan")


# ============= 设备表 =============
DEVICE_STATUS_NORMAL = "normal"
DEVICE_STATUS_REPAIRING = "repairing"
DEVICE_STATUS_DOWN = "down"


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True)  # 设备编号，如 MC-205
    name = Column(String(128), nullable=False)
    tag = Column(String(32), nullable=False, default="机械")  # 机械/电气/液压/仪表/安全
    location = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default=DEVICE_STATUS_NORMAL, index=True)
    last_repair_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_devices_tag_status", "tag", "status"),
    )


# ============= 工单表 =============
TICKET_PENDING = "pending"   # 待派单
TICKET_DOING = "doing"       # 进行中
TICKET_DONE = "done"         # 已完成
TICKET_OVER = "over"         # 超时


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=True, index=True)  # TK-20260711-001
    title = Column(String(255), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    device_name = Column(String(255), nullable=True)
    level = Column(String(16), nullable=False, default="mid")  # low/mid/high
    status = Column(String(32), nullable=False, default=TICKET_PENDING, index=True)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=True)
    submit_time = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    finish_time = Column(DateTime(timezone=True), nullable=True)
    extra = Column(Text, nullable=True)  # JSON 扩展字段，不用频繁改表

    submitter = relationship("User", back_populates="submitted_tickets",
                             foreign_keys=[submitter_id])
    assignee = relationship("User", back_populates="assigned_tickets",
                            foreign_keys=[assignee_id])


# ============= 知识报告表 =============
REPORT_PENDING = "pending"
REPORT_APPROVED = "approved"
REPORT_REJECTED = "rejected"
REPORT_SYNCED_CASE = "synced_case"
REPORT_SYNCED_GUIDE = "synced_guide"

REPORT_SOURCE_SEARCH = "search"
REPORT_SOURCE_TICKET = "ticket"
REPORT_SOURCE_MANUAL = "manual"

TYPE_CASE = "case"
TYPE_GUIDE = "guide"


class KnowledgeReport(Base):
    __tablename__ = "knowledge_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rid = Column(String(32), unique=True, nullable=False, index=True)  # KR-XXXXXX
    title = Column(String(255), nullable=False)
    device = Column(String(255), nullable=True)
    type = Column(String(16), nullable=False, default=TYPE_CASE)   # case / guide
    source = Column(String(32), nullable=False, default=REPORT_SOURCE_MANUAL)
    level = Column(String(16), nullable=True)
    tag = Column(String(32), nullable=True)
    question = Column(Text, nullable=False)
    cause = Column(Text, nullable=True)
    solution = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    ticket_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default=REPORT_PENDING, index=True)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitter_username = Column(String(64), nullable=True)  # 冗余保存 submitter 的 username，便于精确统计
    submitter_name = Column(String(128), nullable=False)
    submit_time = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_name = Column(String(128), nullable=True)
    review_remark = Column(Text, nullable=True)
    review_time = Column(DateTime(timezone=True), nullable=True)
    sync_time = Column(DateTime(timezone=True), nullable=True)

    submitter = relationship("User", back_populates="reports", foreign_keys=[submitter_id])
    reviewer = relationship("User", back_populates="reviewed_reports", foreign_keys=[reviewer_id])

    synced_case = relationship(
        "Case", back_populates="source_report",
        foreign_keys="Case.source_report_id", uselist=False
    )
    synced_guide = relationship(
        "Guide", back_populates="source_report",
        foreign_keys="Guide.source_report_id", uselist=False
    )


# ============= 案例库表 =============
class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    device = Column(String(255), nullable=True)
    tag = Column(String(32), nullable=False, default="综合", index=True)
    fault = Column(Text, nullable=False)
    cause = Column(Text, nullable=True)
    solution = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    level = Column(String(16), nullable=True)
    source_report_id = Column(Integer, ForeignKey("knowledge_reports.id"), nullable=True)
    contributor_name = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    source_report = relationship("KnowledgeReport", back_populates="synced_case",
                                 foreign_keys=[source_report_id])


# ============= 作业指导表 =============
class Guide(Base):
    __tablename__ = "guides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    device_type = Column(String(32), nullable=False, default="机械", index=True)
    tag = Column(String(32), nullable=True)
    steps_json = Column(Text, nullable=False)  # 存 JSON，避免建子表：[{"step":1,"content":"","tip":""},...]
    risk_note = Column(Text, nullable=True)
    duration_min = Column(Integer, nullable=True)
    source_report_id = Column(Integer, ForeignKey("knowledge_reports.id"), nullable=True)
    contributor_name = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    source_report = relationship("KnowledgeReport", back_populates="synced_guide",
                                 foreign_keys=[source_report_id])


# ============= 消息通知表 =============
NOTIFY_TYPE_REPORT_SUBMITTED = "report_submitted"   # 员工提交了实践报告（给管理员）
NOTIFY_TYPE_REPORT_APPROVED = "report_approved"     # 管理员审核通过（给提交人）
NOTIFY_TYPE_REPORT_REJECTED = "report_rejected"     # 管理员驳回（给提交人）
NOTIFY_TYPE_REPORT_SYNCED = "report_synced"         # 管理员同步入库（给提交人）
NOTIFY_TYPE_TICKET_ASSIGNED = "ticket_assigned"     # 新工单派给我（给维修工）
NOTIFY_TYPE_SYSTEM = "system"                       # 系统通知


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(32), nullable=False, default=NOTIFY_TYPE_SYSTEM, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    related_id = Column(Integer, nullable=True)   # 关联的业务ID：如 report_id / ticket_id
    is_read = Column(Integer, nullable=False, default=0, index=True)   # 0=未读 1=已读
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])
