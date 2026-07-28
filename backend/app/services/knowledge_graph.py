import json
import os
from pathlib import Path
from typing import Dict, List, Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "knowledge" / "data"

REPORTS_FILE = DATA_DIR / "reports.json"
CASES_FILE = DATA_DIR / "cases.json"
GRAPH_FILE = DATA_DIR / "knowledge_graph.json"


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default=None):
    if not path.exists():
        return default or {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default or {}


def _save_json(path: Path, data):
    _ensure_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_report(report_data: Dict):
    reports = _load_json(REPORTS_FILE, [])
    reports.append(report_data)
    _save_json(REPORTS_FILE, reports)
    return reports


def get_reports() -> List[Dict]:
    return _load_json(REPORTS_FILE, [])


def save_case(case_data: Dict):
    cases = _load_json(CASES_FILE, [])
    existing = next((c for c in cases if c.get("source_report_id") == case_data.get("source_report_id")), None)
    if existing:
        for k, v in case_data.items():
            existing[k] = v
    else:
        cases.append(case_data)
    _save_json(CASES_FILE, cases)
    # 增量追加：仅把本条案例追加到对应 tag 子图，不再全量重建
    add_case_to_graph(case_data)
    return cases


def get_cases() -> List[Dict]:
    return _load_json(CASES_FILE, [])


# 案例分类 tag 列表（与 Case.tag 对应）
CASE_TAGS = ["机械", "电气", "液压", "仪表", "安全", "综合"]

def _empty_graph() -> Dict:
    """返回空的按 tag 分图的图谱结构"""
    return {"all": {"nodes": [], "links": []}, **{t: {"nodes": [], "links": []} for t in CASE_TAGS}}


def _normalize_graph(raw) -> Dict:
    """兼容旧格式（扁平 {nodes,links}）→ 新格式（按 tag 分图）"""
    if not raw:
        return _empty_graph()
    if isinstance(raw, dict) and "all" in raw:
        return raw
    # 旧格式：整体归入 "all"，各 tag 子图为空（下次 rebuild 时补全）
    return {"all": raw if isinstance(raw, dict) else {"nodes": [], "links": []},
            **{t: {"nodes": [], "links": []} for t in CASE_TAGS}}


def _extract_case_ids(nodes: List[Dict]) -> set:
    """从节点列表提取所有案例类型节点的 case_id"""
    return {n.get("case_id") for n in nodes if n.get("type") == "案例" and n.get("case_id")}


def _build_one_case_nodes_links(case: Dict, existing_names: set) -> tuple:
    """为单条案例生成 (new_nodes, new_links)，existing_names 是当前子图已有的节点名集合"""
    new_nodes = []
    new_links = []
    case_id = case.get("case_id", "")
    device = case.get("device", "")
    fault = case.get("fault", "")
    reason = case.get("reason", "")
    solution = case.get("solution", "")
    title = case.get("title", "")

    def add_node(name: str, type: str):
        if name and name not in existing_names:
            existing_names.add(name)
            new_nodes.append({"name": name, "type": type, "case_id": case_id})

    def add_link(source: str, target: str, relation: str):
        if source and target and source in existing_names and target in existing_names:
            new_links.append({"source": source, "target": target, "relation": relation})

    add_node(title, "案例")
    if device:
        add_node(device, "设备")
        add_link(device, title, "关联案例")
    if fault:
        fault_short = fault[:20] if len(fault) > 20 else fault
        add_node(fault_short, "故障")
        if device:
            add_link(device, fault_short, "发生故障")
        add_link(fault_short, title, "对应案例")
    if reason:
        reason_short = reason[:20] if len(reason) > 20 else reason
        add_node(reason_short, "原因")
        if fault:
            fault_short = fault[:20] if len(fault) > 20 else fault
            add_link(fault_short, reason_short, "故障原因")
        add_link(reason_short, title, "分析案例")
    if solution:
        solution_short = solution[:20] if len(solution) > 20 else solution
        add_node(solution_short, "解决方案")
        if reason:
            reason_short = reason[:20] if len(reason) > 20 else reason
            add_link(reason_short, solution_short, "解决方案")
        add_link(solution_short, title, "解决案例")

    return new_nodes, new_links


def update_knowledge_graph(cases: List[Dict]):
    """全量重建：按 tag 分图，每个 tag 子图独立构建 + 一个 all 聚合图"""
    graph = _empty_graph()

    def build_subgraph(case_list: List[Dict]) -> Dict:
        nodes, links, node_names = [], [], set()
        for case in case_list:
            nn, nl = _build_one_case_nodes_links(case, node_names)
            nodes.extend(nn)
            links.extend(nl)
        return {"nodes": nodes, "links": links}

    # 按 tag 分组
    by_tag = {t: [] for t in CASE_TAGS}
    for case in cases:
        tag = case.get("tag", "综合")
        if tag not in by_tag:
            tag = "综合"
        by_tag[tag].append(case)

    # 各 tag 子图
    for tag in CASE_TAGS:
        graph[tag] = build_subgraph(by_tag[tag])

    # all = 全量合并（节点按 name 去重，边按 source+target+relation 去重）
    all_nodes, all_links, all_names = [], [], set()
    all_link_keys = set()
    for tag in CASE_TAGS:
        for n in graph[tag]["nodes"]:
            if n["name"] not in all_names:
                all_names.add(n["name"])
                all_nodes.append(n)
        for l in graph[tag]["links"]:
            key = f"{l['source']}|{l['target']}|{l['relation']}"
            if key not in all_link_keys:
                all_link_keys.add(key)
                all_links.append(l)
    graph["all"] = {"nodes": all_nodes, "links": all_links}

    _save_json(GRAPH_FILE, graph)
    return graph


def add_case_to_graph(case_data: Dict):
    """增量追加：把单条案例追加到对应 tag 子图 + all 聚合图（case_id 幂等去重）"""
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    tag = case_data.get("tag", "综合")
    if tag not in graph:
        tag = "综合"
    case_id = case_data.get("case_id", "")

    # 幂等检测：该 case_id 已在对应 tag 子图中则跳过
    existing_case_ids = _extract_case_ids(graph[tag]["nodes"])
    if case_id in existing_case_ids:
        return graph

    # 追加到对应 tag 子图
    existing_names = {n["name"] for n in graph[tag]["nodes"]}
    nn, nl = _build_one_case_nodes_links(case_data, existing_names)
    graph[tag]["nodes"].extend(nn)
    graph[tag]["links"].extend(nl)

    # 同步追加到 all 聚合图
    all_names = {n["name"] for n in graph["all"]["nodes"]}
    all_link_keys = {f"{l['source']}|{l['target']}|{l['relation']}" for l in graph["all"]["links"]}
    for n in nn:
        if n["name"] not in all_names:
            all_names.add(n["name"])
            graph["all"]["nodes"].append(n)
    for l in nl:
        key = f"{l['source']}|{l['target']}|{l['relation']}"
        if key not in all_link_keys:
            all_link_keys.add(key)
            graph["all"]["links"].append(l)

    _save_json(GRAPH_FILE, graph)
    return graph


def get_knowledge_graph(tag: str = "all") -> Dict:
    """获取图谱。tag='all' 返回聚合图，否则返回对应 tag 子图"""
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    if tag and tag != "all" and tag in graph:
        return graph[tag]
    return graph["all"]


def get_all_graph_stats() -> Dict:
    """返回各 tag 子图的案例数，供前端 tab 显示统计"""
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    stats = {}
    for tag, sub in graph.items():
        if isinstance(sub, dict) and "nodes" in sub:
            stats[tag] = len([n for n in sub["nodes"] if n.get("type") == "案例"])
        else:
            stats[tag] = 0
    return stats


def build_graph_from_db(cases_db: List):
    cases = []
    for c in cases_db:
        case_dict = {
            "case_id": f"CASE-{c.id:04d}",
            "source_report_id": c.source_report_id,
            "title": c.title,
            "device": c.device or "",
            "fault": c.fault or "",
            "reason": c.cause or "",
            "solution": c.solution or "",
            "experience": c.summary or "",
            "author": c.contributor_name or "",
            "create_time": str(c.created_at) if c.created_at else "",
            "tag": c.tag or "综合"
        }
        cases.append(case_dict)
    _save_json(CASES_FILE, cases)
    return update_knowledge_graph(cases)


# ============= 图谱维护：编辑 / 删除节点（增量同步） =============


def _get_tag_for_node(graph: Dict, node_name: str) -> str | None:
    """查找某个节点属于哪个 tag 子图。"""
    for tag in list(CASE_TAGS) + ["all"]:
        sub = graph.get(tag)
        if sub and isinstance(sub, dict):
            for n in sub.get("nodes", []):
                if n.get("name") == node_name:
                    return tag if tag != "all" else None
    return None


def update_graph_node(old_name: str, new_name: str, new_type: str | None = None) -> Dict:
    """编辑节点：重命名 + 可选改类型。同步更新所有子图和关联边的 source/target。"""
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    updated_count = 0

    def _rename_in_subgraph(sub: Dict):
        nonlocal updated_count
        if not sub or not isinstance(sub, dict):
            return
        # 更新节点名
        for n in sub.get("nodes", []):
            if n.get("name") == old_name:
                n["name"] = new_name
                if new_type:
                    n["type"] = new_type
                updated_count += 1
        # 更新关联边的 source/target
        for l in sub.get("links", []):
            if l.get("source") == old_name:
                l["source"] = new_name
            if l.get("target") == old_name:
                l["target"] = new_name

    for tag in list(CASE_TAGS) + ["all"]:
        _rename_in_subgraph(graph.get(tag))

    _save_json(GRAPH_FILE, graph)
    return {"updated_count": updated_count, "old_name": old_name, "new_name": new_name}


def delete_graph_node(name: str) -> Dict:
    """删除节点及其关联的所有边。支持增量同步。"""
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    deleted_nodes = 0
    deleted_links = 0

    def _delete_from_subgraph(sub: Dict):
        nonlocal deleted_nodes, deleted_links
        if not sub or not isinstance(sub, dict):
            return
        old_len_nodes = len(sub.get("nodes", []))
        sub["nodes"] = [n for n in sub.get("nodes", []) if n.get("name") != name]
        deleted_nodes += old_len_nodes - len(sub["nodes"])
        old_len_links = len(sub.get("links", []))
        sub["links"] = [l for l in sub.get("links", [])
                        if l.get("source") != name and l.get("target") != name]
        deleted_links += old_len_links - len(sub["links"])

    for tag in list(CASE_TAGS) + ["all"]:
        _delete_from_subgraph(graph.get(tag))

    _save_json(GRAPH_FILE, graph)
    return {"deleted_nodes": deleted_nodes, "deleted_links": deleted_links, "name": name}


def update_case_in_graph(case_data: Dict):
    """更新已有案例在图中的节点和关系（编辑案例后增量同步）。"""
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    tag = case_data.get("tag", "综合")
    if tag not in graph:
        tag = "综合"
    case_id = case_data.get("case_id", "")

    # 先删除该 case_id 的所有旧节点（从各子图）
    delete_graph_node_orphans(case_id)

    # 再用新数据重建该案例的节点和边
    existing_names = {n["name"] for n in graph[tag]["nodes"]}
    all_names = {n["name"] for n in graph["all"]["nodes"]}
    nn, nl = _build_one_case_nodes_links(case_data, existing_names)
    for n in nn:
        if n["name"] not in all_names:
            all_names.add(n["name"])
            graph["all"]["nodes"].append(n)
    for l in nl:
        key = f"{l['source']}|{l['target']}|{l['relation']}"
        if key not in {f"{x['source']}|{x['target']}|{x['relation']}" for x in graph["all"]["links"]}:
            graph["all"]["links"].append(l)

    # 追加到对应 tag 子图
    tag_names = {n["name"] for n in graph[tag]["nodes"]}
    tnn, tnl = _build_one_case_nodes_links(case_data, tag_names)
    graph[tag]["nodes"].extend(tnn)
    graph[tag]["links"].extend(tnl)

    _save_json(GRAPH_FILE, graph)
    return graph


def delete_graph_node_orphans(case_id: str):
    """删除图中有特定 case_id 的所有节点（清理旧数据）。"""
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    for tag in list(CASE_TAGS) + ["all"]:
        sub = graph.get(tag)
        if not sub or not isinstance(sub, dict):
            continue
        # 收集要删除的节点名
        orphan_names = {n["name"] for n in sub.get("nodes", []) if n.get("case_id") == case_id}
        sub["nodes"] = [n for n in sub.get("nodes", []) if n.get("name") not in orphan_names]
        sub["links"] = [l for l in sub.get("links", [])
                        if l.get("source") not in orphan_names and l.get("target") not in orphan_names]
    _save_json(GRAPH_FILE, graph)
    return graph


# ============= Graph-RAG：图谱实体增强检索上下文 =============


def traverse_related(
    search_text: str,
    tag: str = "all",
    max_depth: int = 2,
    max_results: int = 6,
) -> list[dict]:
    """从知识图谱中搜索匹配 entity 并 travers 关联路径。

    用于 Graph-RAG：给定文本（故障描述/设备名/案例标题），
    在图谱中找到匹配节点，沿着边遍历 1~2 跳获取关联实体路径。

    Returns:
        list[dict]: [{entity, type, path: [{entity, relation, depth}], full_path_text}]
    """
    graph = _normalize_graph(_load_json(GRAPH_FILE))
    sub = graph.get(tag) or graph.get("all")
    if not sub or not isinstance(sub, dict):
        return []

    nodes = sub.get("nodes", [])
    links = sub.get("links", [])

    # 1. 找到匹配节点（模糊匹配：搜索文本出现在节点名中）
    search_lower = search_text.lower()
    matching_nodes = []
    for n in nodes:
        name = str(n.get("name", ""))
        if search_lower in name.lower():
            matching_nodes.append(n)

    if not matching_nodes:
        # 退一步：按 search_text 拆词匹配（更宽松）
        tokens = [t for t in search_lower.split() if len(t) >= 2]
        for n in nodes:
            name_lower = str(n.get("name", "")).lower()
            for token in tokens:
                if token in name_lower:
                    matching_nodes.append(n)
                    break

    if not matching_nodes:
        return []

    # 2. 建立邻接表
    adj: dict[str, list[dict]] = {}
    for link in links:
        src = str(link.get("source", ""))
        tgt = str(link.get("target", ""))
        rel = str(link.get("relation", ""))

        adj.setdefault(src, []).append({"entity": tgt, "relation": rel, "direction": "out"})
        adj.setdefault(tgt, []).append({"entity": src, "relation": rel, "direction": "in"})

    # 3. BFS 遍历 max_depth 跳
    results: list[dict] = []
    seen_entities: set[str] = set()

    for mn in matching_nodes[:3]:  # 最多从 3 个起始节点开始
        entity_name = str(mn.get("name", ""))
        entity_type = str(mn.get("type", ""))
        if entity_name in seen_entities:
            continue
        seen_entities.add(entity_name)

        path_text_parts = [f"{entity_name}({entity_type})"]
        visited = {entity_name}
        queue: list[tuple[str, int, list[str]]] = [(entity_name, 0, [])]

        while queue:
            current, depth, path_rels = queue.pop(0)
            if depth >= max_depth:
                continue
            for neighbor in adj.get(current, []):
                nb_name = neighbor["entity"]
                nb_rel = neighbor["relation"]
                nb_dir = neighbor["direction"]
                if nb_name in visited:
                    continue
                visited.add(nb_name)
                rel_prefix = "→" if nb_dir == "out" else "←"
                new_rels = path_rels + [f"{rel_prefix}[{nb_rel}]→{nb_name}"]
                path_text_parts.append("  " * (depth + 1) + new_rels[-1])
                queue.append((nb_name, depth + 1, new_rels))

        full_path_text = "\n".join(path_text_parts)

        # 找到关联节点名（用于下游提示词注入）
        related_entities = []
        for neighbor in adj.get(entity_name, []):
            related_entities.append({
                "entity": neighbor["entity"],
                "relation": neighbor["relation"],
                "direction": neighbor["direction"],
            })

        results.append({
            "entity": entity_name,
            "type": entity_type,
            "related": related_entities[:6],
            "full_path_text": full_path_text,
        })

        if len(results) >= max_results:
            break

    return results


def format_graph_context(results: list[dict]) -> str:
    """将图谱遍历结果格式化为自然语言文本，供 RAG 提示词注入。"""
    if not results:
        return ""

    parts = ["""
【知识图谱关联信息 —— 实体关系参考】
以下是从设备检修知识图谱中检索到的相关实体及其关联关系，
可供交叉验证检索证据，辅助推理判断。
"""]
    for i, r in enumerate(results, 1):
        parts.append(f"\n关联路径 {i}: {r['entity']} ({r['type']})")
        if r["related"]:
            for rel in r["related"][:4]:
                arrow = "→" if rel["direction"] == "out" else "←"
                parts.append(f"  {arrow} {rel['relation']} → {rel['entity']}")
        if r.get("full_path_text"):
            parts.append(f"\n完整链路:\n{r['full_path_text']}")

    parts.append("\n（图谱信息仅供参考，回答时如使用请注明来源）\n")
    return "\n".join(parts)
