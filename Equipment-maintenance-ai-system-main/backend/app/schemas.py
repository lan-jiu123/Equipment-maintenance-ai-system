"""
Pydantic 入参/出参 DTO
- 阶段 A：基础登录/用户/Token + 统一响应
- 阶段 B：设备/工单/报告/案例/指南/用户管理 + 通用分页
"""

from __future__ import annotations
from typing import Generic, TypeVar, Optional, Any, List
from datetime import datetime

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator
    _PYDANTIC_V2 = True
except Exception:  # pydantic v1 兼容
    from pydantic import BaseModel, Field, validator as field_validator  # type: ignore
    _PYDANTIC_V2 = False
    ConfigDict = dict  # type: ignore


T = TypeVar("T")


# ============ 统一响应结构 ============
class ApiResp(BaseModel, Generic[T]):
    """所有 /api/* 的统一响应壳：{ code, msg, data }"""
    code: int = Field(default=200, description="200=成功，其他=失败")
    msg: str = Field(default="", description="错误信息 / 成功提示")
    data: Optional[T] = Field(default=None, description="业务数据")

    if _PYDANTIC_V2:
        model_config = ConfigDict(json_encoders={
            datetime: lambda v: v.timestamp() if isinstance(v, datetime) else v
        })


def ok(data: Any = None, msg: str = "success") -> ApiResp[Any]:
    """快速构造成功响应"""
    return ApiResp(code=200, msg=msg, data=data)


def fail(msg: str, code: int = 400, data: Any = None) -> ApiResp[Any]:
    """快速构造失败响应"""
    return ApiResp(code=code, msg=msg, data=data)


# ============ 通用分页 ============
class PageReq(BaseModel):
    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    size: int = Field(default=10, ge=1, le=200, description="每页条数（最多 200）")
    keyword: Optional[str] = Field(default=None, description="关键词模糊搜索")

    if _PYDANTIC_V2:
        model_config = ConfigDict(str_strip_whitespace=True)
    else:
        class Config:
            anystr_strip_whitespace = True


class PageResp(BaseModel, Generic[T]):
    total: int = Field(..., description="总条数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页条数")
    pages: int = Field(..., description="总页数")
    items: List[T] = Field(default_factory=list, description="当前页数据")


def page_wrap(page: int, size: int, total: int, items: List[Any]) -> PageResp[Any]:
    pages = (total + size - 1) // size if size > 0 else 0
    return PageResp(total=total, page=page, size=size, pages=pages, items=items)


# ============ 登录 ============
class LoginReq(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, description="用户名/工号")
    password: str = Field(..., min_length=1, max_length=128, description="密码")
    role: Optional[str] = Field(default=None, description="角色：manager / worker")

    if _PYDANTIC_V2:
        model_config = ConfigDict(str_strip_whitespace=True)
    else:
        class Config:
            anystr_strip_whitespace = True


class UserInfo(BaseModel):
    """返回给前端的用户信息（不含密码，password_hash 永不返回）"""
    id: int
    username: str
    fullname: str
    role: str
    role_label: str
    avatar_preset: Optional[str] = None
    avatar: Optional[str] = None  # 预留字段，未来扩展
    created_at: Optional[datetime] = None

    # profile 扩展字段（一期加 8 列）；前端 Profile.vue / 派单弹窗 / 用户管理 共用
    emp_no: Optional[str] = None
    dept: Optional[str] = None
    position: Optional[str] = None
    join_date: Optional[str] = None
    join_date_ts: Optional[int] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    tel: Optional[str] = None
    office: Optional[str] = None


class LoginResp(BaseModel):
    """登录成功返回：token + 用户信息"""
    token: str
    token_type: str = "bearer"
    expires_hours: int
    user: UserInfo


# ============ 1. 设备 ============
class DeviceCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=64, description="设备编号，如 MC-001")
    name: str = Field(..., min_length=1, max_length=128, description="设备名称")
    tag: str = Field(default="机械", description="大类：机械/电气/液压/仪表/安全")
    location: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="normal", description="normal/repairing/down")


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    tag: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, description="normal/repairing/down")


class DeviceInfo(BaseModel):
    id: int
    code: str
    name: str
    tag: str
    location: Optional[str] = None
    status: str
    status_label: str
    health: int = 100
    last_repair_at: Optional[datetime] = None
    created_at_ts: Optional[int] = None
    # 故障停机时返回的故障上报信息
    fault_desc: Optional[str] = None
    fault_reporter_name: Optional[str] = None
    fault_time_ts: Optional[int] = None
    fault_attachments: Optional[list] = None


# ============ 2. 工单 ============
class TicketCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    level: str = Field(default="mid", description="low/mid/high")
    problem: str = Field(..., min_length=1)
    assignee_id: Optional[int] = Field(default=None, description="指定派单员，不填则待派单")


class TicketAssign(BaseModel):
    assignee_id: int = Field(..., description="指派的维修员 ID")
    level: Optional[str] = Field(default=None, description="优先级：low/mid/high，不传则保持原值")


class TicketComplete(BaseModel):
    solution: str = Field(..., min_length=5, description="维修解决方案")


class TicketInfo(BaseModel):
    id: int
    code: Optional[str] = None
    title: str
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    level: str
    level_label: str
    status: str
    status_label: str
    submitter_name: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_id: Optional[int] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    submit_time_ts: Optional[int] = None
    finish_time_ts: Optional[int] = None


# ============ 3. 知识报告 ============
class ReportCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    device: Optional[str] = None
    type: str = Field(default="case", description="case / guide")
    source: str = Field(default="manual", description="search / ticket / manual")
    level: Optional[str] = Field(default="mid")
    tag: Optional[str] = Field(default=None)
    question: str = Field(..., min_length=5)
    cause: Optional[str] = None
    solution: str = Field(..., min_length=5)
    repair_process: Optional[str] = Field(default=None, description="维修过程")
    technical_measures: Optional[str] = Field(default=None, description="使用方法/技术措施")
    repair_result: Optional[str] = Field(default=None, description="维修结果")
    summary: Optional[str] = None
    ticket_id: Optional[str] = None


class ReportReview(BaseModel):
    action: str = Field(..., description="approve / reject / sync_case / sync_guide")
    remark: Optional[str] = Field(default=None, max_length=1000, description="审核意见（驳回必填）")


class ReportInfo(BaseModel):
    id: int
    rid: str
    title: str
    device: Optional[str] = None
    type: str
    source: str
    level: Optional[str] = None
    tag: Optional[str] = None
    question: Optional[str] = None
    cause: Optional[str] = None
    solution: Optional[str] = None
    repair_process: Optional[str] = None
    technical_measures: Optional[str] = None
    repair_result: Optional[str] = None
    summary: Optional[str] = None
    status: str
    status_label: str
    submitter_id: int
    submitter_name: str
    submit_time_ts: Optional[int] = None
    reviewer_name: Optional[str] = None
    review_remark: Optional[str] = None
    review_time_ts: Optional[int] = None
    sync_time_ts: Optional[int] = None
    attachments: Optional[list] = None


# ============ 4. 案例 ============
class CaseInfo(BaseModel):
    id: int
    title: str
    device: Optional[str] = None
    tag: str
    fault: Optional[str] = None
    cause: Optional[str] = None
    solution: Optional[str] = None
    summary: Optional[str] = None
    level: Optional[str] = None
    contributor_name: Optional[str] = None
    is_employee_contribution: bool
    created_at_ts: Optional[int] = None


# ============ 5. 作业指导 ============
class GuideStep(BaseModel):
    step: int
    content: str
    tip: Optional[str] = None


class GuideInfo(BaseModel):
    id: int
    title: str
    device_type: str
    tag: Optional[str] = None
    steps: List[GuideStep] = Field(default_factory=list)
    steps_json: Optional[str] = None
    risk_note: Optional[str] = None
    duration_min: Optional[int] = None
    difficulty: Optional[int] = None
    tools: List[str] = Field(default_factory=list)
    applicable_devices: Optional[str] = None
    contributor_name: Optional[str] = None
    is_employee_contribution: bool
    created_at_ts: Optional[int] = None


# ============ 6. 用户管理 ============
class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    fullname: str = Field(..., min_length=1, max_length=128)
    role: str = Field(default="worker", description="sysadmin / manager / worker")
    avatar_preset: Optional[str] = Field(default=None)


class UserUpdate(BaseModel):
    fullname: Optional[str] = Field(default=None, max_length=128)
    role: Optional[str] = Field(default=None)
    avatar_preset: Optional[str] = Field(default=None)

    # profile 扩展（admin PUT /users/:id 同步）
    emp_no: Optional[str] = Field(default=None, max_length=32)
    dept: Optional[str] = Field(default=None, max_length=64)
    position: Optional[str] = Field(default=None, max_length=64)
    join_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    mobile: Optional[str] = Field(default=None, max_length=32)
    email: Optional[str] = Field(default=None, max_length=128)
    tel: Optional[str] = Field(default=None, max_length=32)
    office: Optional[str] = Field(default=None, max_length=128)


class UserProfileUpdate(BaseModel):
    """当前登录用户修改自己的 profile（PUT /api/me）"""
    fullname: Optional[str] = Field(default=None, max_length=128)
    emp_no: Optional[str] = Field(default=None, max_length=32)
    dept: Optional[str] = Field(default=None, max_length=64)
    position: Optional[str] = Field(default=None, max_length=64)
    join_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    mobile: Optional[str] = Field(default=None, max_length=32)
    email: Optional[str] = Field(default=None, max_length=128)
    tel: Optional[str] = Field(default=None, max_length=32)
    office: Optional[str] = Field(default=None, max_length=128)
    # 不强制校验格式：前端给提示、后端只做 strip


class UserPwdChange(BaseModel):
    old_password: str = Field(default="", max_length=128, description="旧密码（修改自己密码必填；管理员重置可为空")
    new_password: str = Field(default="123456", min_length=6, max_length=128, description="新密码，默认重置为 123456")


class UserFullInfo(BaseModel):
    id: int
    username: str
    fullname: str
    role: str
    role_label: str
    avatar_preset: Optional[str] = None
    created_at_ts: Optional[int] = None
    ticket_stats: dict = Field(default_factory=dict)


# ============ 8. 消息通知 ============
class NotificationInfo(BaseModel):
    id: int
    type: str
    title: str
    content: Optional[str] = None
    related_id: Optional[int] = None
    is_read: bool
    created_at_ts: Optional[int] = None


class NotificationMarkReadReq(BaseModel):
    ids: Optional[list[int]] = Field(default=None, description="要标记为已读的通知ID；为空则全部标记为已读")
