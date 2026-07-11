# RAG 评测资料说明

## 基准文档

- 展示名称：摩托车发动机维修手册
- 本地文件：`data/raw/manuals/motorcycle_engine_manual.pdf`
- 原始文件：赛题提供的《摩托车发动机维修手册.pdf》
- 文件大小：17,615,124 字节
- PDF 页数：41 页
- 页面尺寸：A3
- SHA-256：`AAD3C07269B2469E8E0D01357D2808FE6A3245501C82B557F61B700B7CAADB43`
- 文档类型：文本型 PDF，可直接提取中文文字；图片和装配图仍需保留页面位置
- 页码规则：文档页脚 `No. n / 41` 与 PDF 物理页码一致，因此评测集统一使用 PDF 页码

原始 PDF 位于 `data/raw/`，已通过 `.gitignore` 排除，不应提交到公开仓库。团队成员应从赛题资料获得同一文件，并使用 SHA-256 核验版本。

## 评测集

`rag_questions_excel.csv` 是第一版人工基准集，共 28 题，采用带 BOM 的 UTF-8 编码，可直接使用 Excel 打开，覆盖：

- 精确参数
- 检修步骤
- 故障判断
- 安全与注意事项
- 部件检查
- 跨段落综合
- 知识库无答案拒答

其中 `expected_answer_points` 是答案评分要点，`evidence_excerpt` 是人工核验用的短证据。系统正式回答时应根据 `document_title + section_title + pdf_page_start` 返回来源，不允许由大模型自行编造页码。

## 使用规则

1. 入库前核对 PDF SHA-256。
2. 每次修改解析、分块、Embedding 或检索算法后运行同一评测集。
3. 先测检索命中，再测回答要点覆盖率和引用准确率。
4. `answerable=no` 的问题应明确提示知识库证据不足。
5. 新增问题必须由另一名队员对照原文复核后，将 `review_status` 改为 `approved`。

## 建议指标

- Top-5 章节命中率
- Top-5 页码命中率
- 答案要点覆盖率
- 引用准确率
- 无答案问题正确拒答率
- 平均检索时间与端到端响应时间
