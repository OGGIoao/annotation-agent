# 标注 Agent 最终设计总图

## 1. 三个平面

```mermaid
flowchart TB
    USER[任务配置 / 人工审核]
    PLATFORM[外部标注平台]

    subgraph CONTROL[控制与审计平面]
        API[FastAPI]
        GRAPH[LangGraph 状态调度]
        CHECKPOINT[(检查点)]
        ACTIONLOG[(动作日志)]
        REVIEW[人工复核]
    end

    subgraph INTELLIGENCE[标注智能平面]
        PARSE[页面解析]
        VLM[多模态理解]
        DOMAIN[整包题目关系图]
        RULES[规则与证据]
        VALIDATE[契约与业务校验]
        RESULT[AnnotationResult]
    end

    subgraph EXECUTION[平台执行平面]
        PLAN[ActionPlan]
        GUARD[执行安全门禁]
        BROWSER[单一浏览器执行器]
        RECEIPT[ExecutionReceipt]
        OBSERVE[保存观察]
    end

    USER --> API --> GRAPH
    PLATFORM <--> BROWSER
    GRAPH --> PARSE --> VLM --> DOMAIN
    RULES --> VALIDATE
    DOMAIN --> VALIDATE
    VALIDATE -->|通过| RESULT --> PLAN --> GUARD --> BROWSER --> RECEIPT --> OBSERVE
    VALIDATE -->|不能裁定| REVIEW --> VALIDATE
    OBSERVE -->|确认| GRAPH
    OBSERVE -->|差异/未知| GRAPH
    GRAPH <--> CHECKPOINT
    GRAPH --> ACTIONLOG
    RECEIPT --> ACTIONLOG
```

## 2. 主链路

```text
任务进入
→ 页面与身份确认
→ 页面解析
→ 题目结构理解
→ 题目关系图
→ 规则和契约校验
→ AnnotationResult
→ ActionPlan
→ 执行安全门禁
→ 浏览器执行
→ 保存观察
→ ExecutionReceipt
→ 状态推进、人工复核或重新采集
```

## 3. 当前实现边界

- 先做离线标注引擎；
- 再做 FakeExecutor；
- 再接测试平台；
- 最后考虑生产提交；
- 模型只生成候选；
- 程序负责坐标、关系、规则和契约；
- 人工处理低置信度和冲突。

完整说明见：[`ARCHITECTURE-DESIGN.md`](ARCHITECTURE-DESIGN.md)。
