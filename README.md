# annotation-agent

题目智能标注 Agent 的第一版工程仓库。

## 当前范围

第一阶段先实现离线标注引擎：

1. 页面输入和 OCR/版面解析适配；
2. 题目框、答案框和题目关系的数据契约；
3. 数学基础题型规则；
4. LangGraph 流程状态；
5. 程序化规则校验；
6. 固定金标准评测；
7. 标注结果可视化。

暂不直接操作生产标注平台，也不自动提交任务。

## 开发环境

```bash
uv sync
uv run pytest
```

项目固定使用 Python 3.12，版本见 `.python-version`。

## 目录规划

```text
annotation-agent/
├── app/
│   ├── api/                 # FastAPI 路由
│   ├── graph/               # LangGraph 状态、节点和边
│   ├── contracts/           # Pydantic 数据契约
│   ├── parsing/             # OCR、版面和坐标变换
│   ├── vision/              # 多模态模型适配器
│   ├── domain/              # 题目树、框和关系领域模型
│   ├── rules/               # 规则匹配和校验器
│   ├── storage/             # SQLite/本地文件，后续扩展 PostgreSQL/对象存储
│   └── observability/       # 日志、指标和追踪
├── rules/                   # YAML 规则资产
├── sample-data/             # 不进 Git 的真实样本
│   ├── raw-pages/
│   ├── answer-pages/
│   └── existing-labels/
├── gold-data/               # 可公开或脱敏的金标准样本
├── tests/
│   ├── unit/
│   ├── rule_cases/
│   └── evaluation/
├── scripts/
├── artifacts/               # 本地运行产物，不进 Git
├── docs/                    # 仓库内工程文档
├── pyproject.toml
└── README.md
```

## 依赖分阶段加入

当前已安装基础依赖：

- FastAPI
- LangGraph
- Pydantic v2
- pytest
- httpx
- python-dotenv

下一阶段再加入并验证：

- PaddleOCR / PP-StructureV3
- Pillow 等图像处理依赖
- PostgreSQL 驱动
- 对象存储客户端
- Redis / Celery

不要在没有真实样本和兼容性验证前一次性加入全部基础设施。

## 数据和密钥

- 真实页面、答案页和现有标注放在 `sample-data/`，默认不提交；
- API Key 只放在本地 `.env`；
- 不提交 `.env`、图片、模型响应和运行产物；
- 脱敏金标准可以放入 `gold-data/`；
- 平台适配层与内部 `AnnotationResult` 分离。

## 第一阶段验收

输入真实页面后，系统应能：

- 输出合法的结构化标注结果；
- 将题目框和答案框画回原图；
- 校验坐标、题号和关系；
- 记录规则、OCR、模型和代码版本；
- 对失败或低置信度任务给出人工复核原因；

## 开发原则

1. 模型只产生候选，程序负责坐标、关系、规则和最终契约；
2. 所有模型输出必须经过 Pydantic 和业务规则校验；
3. 新增题型先写固定规则案例，再写实现；
4. 平台自动化通过独立适配层，不直接污染领域模型；
5. 没有金标准就不宣称准确率达标；
6. 每次修改后运行 `uv run pytest` 和 `git diff --check`。