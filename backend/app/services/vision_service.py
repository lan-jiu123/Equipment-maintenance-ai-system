"""轻量级多模态图片分析服务，兼容阿里云百炼 OpenAI 接口。"""

from __future__ import annotations

import base64
import json
import re
from typing import Any

import requests

from ..config import settings
from .llm_service import LLMConfigError, LLMQuotaError, LLMServiceError


JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

# 图片模型输出不稳定时使用的确定性检修词表。长词优先，避免"轴承内圈"退化成"轴承"。
COMPONENT_TERMS = (
    "轴承内圈", "轴承外圈", "轴承套圈", "滚动体", "保持架", "轴承座",
    "密封环", "密封圈", "轴套", "滚道", "轴瓦", "轴承",
)
FAULT_TERMS = (
    "润滑失效", "润滑不足", "干摩擦", "粘着磨损", "磨粒磨损", "擦伤",
    "剥落", "点蚀", "凹坑", "磨损", "腐蚀", "锈蚀", "积碳", "结垢",
    "裂纹", "断裂", "压痕", "塑性变形", "电蚀", "过热", "污染",
)

DOMAIN_MAP = {
    "电气": [
        "电气", "电", "连接器", "插头", "插座", "电缆", "电线", "触点",
        "积碳", "烧蚀", "短路", "断路", "触电", "绝缘", "导体", "保险丝",
        "开关", "继电器", "接触器", "电机", "绕组", "电刷", "换向器",
    ],
    "机械": [
        "机械", "轴承", "齿轮", "轴", "联轴器", "皮带", "链条", "润滑",
        "磨损", "振动", "旋转", "滚动", "滑动", "传动", "减速机", "变速箱",
        "离合器", "制动器", "飞轮", "曲轴", "连杆", "凸轮", "气门",
    ],
    "液压": [
        "液压", "油缸", "液压缸", "阀", "液压油", "泄漏", "压力", "密封",
        "软管", "管路", "油泵", "马达", "节流阀", "溢流阀", "换向阀",
        "油缸", "活塞", "活塞杆", "液压缸",
    ],
    "仪表": [
        "仪表", "传感器", "压力表", "温度表", "流量计", "变送器", "控制器",
        "PLC", "显示", "表盘", "指针", "数显", "压力传感器", "温度传感器",
        "液位计", "转速表", "功率表", "电压表", "电流表",
    ],
    "安全": [
        "安全", "防护", "急停", "联锁", "防护罩", "安全阀", "灭火器",
        "报警", "警示", "防护栏", "防护门", "安全阀", "爆破片",
        "防雷", "接地", "防静电", "消防", "逃生",
    ],
}

DOMAIN_NAMES = list(DOMAIN_MAP.keys())

VISION_SYSTEM_PROMPT = """你是设备检修图片分析助手。只描述图片中可以观察到的内容，
不得把推测写成事实。识别设备类别、子类型、具体部件类型、部件名称、铭牌、型号、参数、
告警码、裂纹、锈蚀、漏油、烧蚀、磨损等现象。严格返回 JSON，不要使用 Markdown 代码块：
{
  "equipment": "具体设备型号或编号，无法判断则为空字符串",
  "equipment_category": "设备大类，从以下选择：动力设备、流体设备、加工制造设备、检测与仪表设备、安全设备、其他",
  "component_type": "部件类型，从以下选择：传感器接口、连接器、端子组件、轴承组件、齿轮组件、密封件、阀件、线缆组件、结构件、其他",
  "component": "具体部件名称，如：车速传感器连接器、轴承内圈、液压缸活塞杆，无法判断则为空字符串",
  "is_overview": "布尔值，是否为整机/远景图而非局部特写",
  "visible_facts": ["图片中直接可见的事实描述，即使是整机也要描述整体特征"],
  "ocr_text": ["可见文字、型号、参数或告警码"],
  "suspected_faults": ["疑似故障现象，使用专业术语；若看不清具体故障，列出设备常见故障类型"],
  "search_keywords": ["用于维修知识库检索的精准术语，最多8个"],
  "confidence": 0.0,
  "needs_human_review": true,
  "review_reason": "需要人工复核的原因"
}
要求：
1. equipment_category 必须从给定选项中选择一个最匹配的类别，即使无法识别具体型号。
   - 动力设备：电机、发动机、泵、压缩机等动力源
   - 流体设备：管道、阀门、液压缸、流量计等流体处理设备
   - 加工制造设备：机床、机械臂、输送带、减速机等加工设备
   - 检测与仪表设备：传感器、仪表、控制器、检测器等信号设备
   - 安全设备：防护罩、急停、安全阀、灭火器等安全设备
2. component_type 必须从给定选项中选择。
3. 整机/远景图处理规则：
   - 如果是整机图片，is_overview 设为 true
   - equipment_category 仍需判断（如工程机械属于动力设备或流体设备）
   - visible_facts 描述整体外观特征（颜色、结构特点、设备类型）
   - suspected_faults 列出该类设备常见的故障类型（如液压系统泄漏、发动机异响）
   - search_keywords 使用设备类别+常见故障的组合
4. search_keywords 必须精准，优先使用具体部件名和具体故障现象。
5. 避免使用"无法确定"、"未知"等词，可以留空。
6. confidence 必须为 0 到 1 的数字。整机/远景图 confidence 一般不超过 0.5。"""


def _parse_json(text: str) -> dict[str, Any]:
    match = JSON_RE.search(text or "")
    if not match:
        raise LLMServiceError("视觉模型未返回有效 JSON")
    try:
        value = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise LLMServiceError("视觉模型返回的 JSON 无法解析") from exc
    if not isinstance(value, dict):
        raise LLMServiceError("视觉模型返回结构异常")
    return value


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:20]


def infer_fault_domain(analysis: dict, user_note: str = "") -> str:
    category_to_domain = {
        "动力设备": "机械",
        "流体设备": "液压",
        "加工制造设备": "机械",
        "检测与仪表设备": "仪表",
        "安全设备": "安全",
    }
    category = str(analysis.get("equipment_category", "")).strip()
    if category in category_to_domain:
        domain = category_to_domain[category]
        ct = str(analysis.get("component_type", "")).strip()
        if domain == "机械" and ct in ("连接器", "传感器接口", "端子组件", "线缆组件"):
            return "电气"
        if domain == "仪表" and ct in ("连接器", "端子组件", "线缆组件"):
            return "电气"
        return domain

    component_type = str(analysis.get("component_type", "")).strip()
    ct_to_domain = {
        "传感器接口": "仪表",
        "连接器": "电气",
        "端子组件": "电气",
        "轴承组件": "机械",
        "齿轮组件": "机械",
        "密封件": "液压",
        "阀件": "液压",
        "线缆组件": "电气",
    }
    if component_type in ct_to_domain:
        return ct_to_domain[component_type]

    source_text = "；".join(
        str(value)
        for value in (
            analysis.get("equipment", ""),
            analysis.get("equipment_category", ""),
            analysis.get("component_type", ""),
            analysis.get("component", ""),
            *analysis.get("visible_facts", []),
            *analysis.get("suspected_faults", []),
            *analysis.get("search_keywords", []),
            user_note,
        )
        if str(value).strip()
    ).lower()

    domain_scores: dict[str, int] = {}
    for domain, keywords in DOMAIN_MAP.items():
        score = 0
        for kw in keywords:
            if kw.lower() in source_text:
                score += 1
        if score > 0:
            domain_scores[domain] = score

    if not domain_scores:
        return ""

    return max(domain_scores, key=domain_scores.get)


def analyze_image(
    image_bytes: bytes,
    mime_type: str,
    user_note: str = "",
    filename: str = "",
) -> tuple[dict, str]:
    api_key = settings.QWEN_API_KEY or settings.LONGCAT_API_KEY
    base_url = (settings.QWEN_API_URL or settings.LONGCAT_API_URL).rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    model = settings.QWEN_VISION_MODEL
    if not api_key or not model:
        raise LLMConfigError("未配置 QWEN_API_KEY 或 QWEN_VISION_MODEL")

    image_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    note = user_note.strip() or "请分析这张设备检修现场图片。"
    if filename:
        import os
        fname = os.path.splitext(os.path.basename(filename))[0]
        if fname and fname != filename:
            note = f"{note}\n\n[图片文件名参考：{fname}，仅供辅助判断]"
    payload = {
        "model": model,
        "temperature": 0.1,
        "stream": False,
        "messages": [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": note},
                ],
            },
        ],
    }
    response = requests.post(
        f"{base_url}/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=int(settings.LLM_TIMEOUT or 180),
    )
    if response.status_code != 200:
        if response.status_code == 402:
            raise LLMQuotaError("视觉模型账户额度不足")
        if response.status_code in (400, 401, 403, 404):
            raise LLMConfigError(f"视觉模型配置或鉴权失败（HTTP {response.status_code}）")
        raise LLMServiceError(f"视觉模型服务异常（HTTP {response.status_code}）")
    try:
        raw = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMServiceError("视觉模型响应结构异常") from exc

    result = _parse_json(raw)
    confidence = result.get("confidence", 0)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.0
    normalized = {
        "equipment": str(result.get("equipment") or "").strip(),
        "equipment_category": str(result.get("equipment_category") or "").strip(),
        "component_type": str(result.get("component_type") or "").strip(),
        "component": str(result.get("component") or "").strip(),
        "is_overview": bool(result.get("is_overview", False)),
        "visible_facts": _clean_list(result.get("visible_facts")),
        "ocr_text": _clean_list(result.get("ocr_text")),
        "suspected_faults": _clean_list(result.get("suspected_faults")),
        "search_keywords": _clean_list(result.get("search_keywords"))[:8],
        "confidence": confidence,
        "needs_human_review": bool(result.get("needs_human_review", True)),
        "review_reason": str(result.get("review_reason") or "图片诊断需由专业人员复核").strip(),
    }
    normalized["fault_domain"] = infer_fault_domain(normalized, user_note)
    if not normalized["equipment_category"] and normalized["fault_domain"]:
        normalized["equipment_category"] = normalized["fault_domain"] + "设备"
    if not normalized["component_type"] and normalized["component"]:
        normalized["component_type"] = _infer_component_type_from_component(normalized["component"])

    confidence = normalized["confidence"]
    has_keywords = bool(normalized["search_keywords"])
    has_faults = bool(normalized["suspected_faults"])
    has_facts = bool(normalized["visible_facts"])
    has_category = bool(normalized["equipment_category"])

    if confidence < 0.2 and not has_keywords and not has_faults and not has_facts:
        normalized["visible_facts"] = normalized["visible_facts"] or ["图片信息不足，建议拍摄局部特写"]
        normalized["suspected_faults"] = normalized["suspected_faults"] or []
        normalized["search_keywords"] = normalized["search_keywords"] or []
        normalized["review_reason"] = "图片分辨率或构图不足以识别具体部件和故障，建议拍摄局部特写"
        normalized["needs_human_review"] = True

    if normalized["is_overview"] and not has_keywords:
        cat = normalized["equipment_category"]
        domain = normalized["fault_domain"]
        overview_kw = []
        if domain:
            overview_kw.append(domain + "设备")
        if cat:
            overview_kw.append(cat)
        if domain == "液压":
            overview_kw.extend(["液压系统", "液压油泄漏", "液压缸", "液压阀"])
        elif domain == "机械":
            overview_kw.extend(["动力传动", "轴承磨损", "齿轮故障", "润滑系统"])
        elif domain == "电气":
            overview_kw.extend(["电气系统", "线路故障", "连接器", "绝缘检测"])
        elif domain == "仪表":
            overview_kw.extend(["传感器", "检测系统", "信号异常", "控制器"])
        elif domain == "安全":
            overview_kw.extend(["安全防护", "急停系统", "联锁装置"])
        normalized["search_keywords"] = overview_kw[:8]

    return normalized, "qwen-vision-requests"


def _infer_component_type_from_component(component: str) -> str:
    ct_map = {
        "传感器接口": ["传感器", "探头", "检测头"],
        "连接器": ["连接器", "接头", "插头", "插座", "接插件"],
        "端子组件": ["端子", "接线柱", "接线端"],
        "轴承组件": ["轴承", "轴瓦", "轴套"],
        "齿轮组件": ["齿轮", "链轮", "同步轮"],
        "密封件": ["密封", "密封圈", "油封", "填料"],
        "阀件": ["阀", "阀门", "阀芯"],
        "线缆组件": ["线缆", "电缆", "线束", "电线"],
        "结构件": ["支架", "底座", "壳体", "外壳", "罩"],
    }
    comp_lower = component.lower()
    for ct, keywords in ct_map.items():
        if any(kw.lower() in comp_lower for kw in keywords):
            return ct
    return ""


def build_retrieval_query(analysis: dict, user_note: str = "") -> str:
    """构造精准检索式：部件类型 + 具体部件 + 设备类别 + 故障现象 + 关键词。"""
    component_type = str(analysis.get("component_type", "")).strip()
    component = str(analysis.get("component", "")).strip()
    equipment_category = str(analysis.get("equipment_category", "")).strip()
    fault_domain = str(analysis.get("fault_domain", "")).strip()
    equipment = str(analysis.get("equipment", "")).strip()
    if equipment in {"无法确定", "未知", "不确定", "无法识别"}:
        equipment = ""

    fault_terms = _clean_list(analysis.get("suspected_faults", []))
    search_kw = _clean_list(analysis.get("search_keywords", []))

    ct_domain_terms = {
        "传感器接口": ["传感器", "检测", "探头"],
        "连接器": ["连接器", "接头", "接插件"],
        "端子组件": ["端子", "接线"],
        "轴承组件": ["轴承", "轴瓦"],
        "齿轮组件": ["齿轮", "传动"],
        "密封件": ["密封", "泄漏"],
        "阀件": ["阀", "阀门"],
        "线缆组件": ["线缆", "电缆", "线束"],
    }
    component_specific_terms = ct_domain_terms.get(component_type, []) if component_type else []

    parts = []
    if component_type:
        parts.append(component_type)
    if component:
        parts.append(component)
    if component_specific_terms:
        parts.extend(component_specific_terms[:2])
    if equipment_category:
        parts.append(equipment_category)
    if fault_domain and fault_domain not in (equipment_category or ""):
        parts.append(fault_domain)
    if equipment and equipment != component:
        parts.append(equipment)

    specific_faults = [t for t in fault_terms if len(t) >= 3]
    generic_faults = [t for t in fault_terms if len(t) < 3]
    parts.extend(specific_faults[:4])
    parts.extend(generic_faults[:3])

    domain_match_terms = [component_type, component, equipment_category] + component_specific_terms
    domain_specific_kw = [kw for kw in search_kw if any(
        term and term in kw for term in domain_match_terms
    )]
    other_kw = [kw for kw in search_kw if kw not in domain_specific_kw]
    parts.extend(domain_specific_kw[:4])
    parts.extend(other_kw[:3])

    ocr_values = [
        v for v in analysis.get("ocr_text", [])
        if len(str(v).strip()) <= 40 and str(v).strip()
    ]
    parts.extend(ocr_values[:3])

    cleaned: list[str] = []
    seen: set[str] = set()
    for part in parts:
        value = str(part).strip().strip("；，。")
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return "；".join(cleaned[:14])[:400]
