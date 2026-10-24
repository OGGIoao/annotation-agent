# 标注 Agent 流程图集

> 这不是新增系统，而是把总设计拆成几个容易理解、容易实现和容易排错的流程图。
>
> 总体详细说明见 [`ARCHITECTURE-DESIGN.md`](ARCHITECTURE-DESIGN.md)。

## 1. 总体端到端流程

```mermaid
flowchart LR
    A[任务进入]
    B[页面与身份确认]
    C[LangGraph 状态调度]
    D[页面解析]
    E[题目结构理解]
    F[题目关系与答案匹配]
    G[规则与契约校验]
    H{是否通过}
    I[AnnotationResult]
    J[ActionPlan]
    K[浏览器执行]
    L[保存观察]
    M{结果确认}
    N[人工复核]

    A --> B --> C --> D --> E --> F --> G --> H
    H -->|通过| I --> J --> K --> L --> M
    H -->|不能裁定| N --> G
    M -->|确认| C
    M -->|差异或未知| B
```

### 这张图回答什么

回答系统从任务进入到最终确认的完整路径。它不展开每个技术细节，只说明系统的主干。

## 2. 标注智能流程

```mermaid
flowchart TD
    A[原始页面 / 已有标注 / 答案页]
    B[OCR 与版面解析]
    C[文字块、坐标、栏位、表格、公式]
    D[题号和作答区域候选]
    E[多模态模型理解]
    F[题目边界、公共题干、子题、题型]
    G[答案来源与回填答案候选]
    H[整包题目关系图]
    I[版本化规则与证据]
    J[规则决策]
    K[Pydantic 契约校验]
    L[业务规则校验]
    M[AnnotationResult]

    A --> B --> C --> D --> E
    E --> F
    E --> G
    F --> H
    G --> H
    H --> J
    I --> J --> K --> L --> M
```

### 模型和程序的分工

```text
模型：提出“这可能是什么”
程序：检查“这个结果是否合法”
规则：决定“业务上应该怎么做”
```

## 3. 规则校验流程

```mermaid
flowchart TD
    A[模型候选结果]
    B[字段和类型校验]
    C{结构是否合法}
    D[坐标校验]
    E[关系校验]
    F[业务规则校验]
    G{是否存在冲突}
    H[输出错误码和证据]
    I[局部修正]
    J[人工复核]
    K[通过并生成 AnnotationResult]

    A --> B --> C
    C -->|否| H
    C -->|是| D --> E --> F --> G
    G -->|否| K
    G -->|可局部修正| I --> B
    G -->|不能裁定| J --> B
```

### 质量门禁的原则

- 结构不合法，不能进入业务判断；
- 坐标不合法，不能生成动作；
- 关系冲突，不能静默通过；
- 低置信度，进入人工复核；
- 修正后必须重新校验。

## 4. 平台执行流程

```mermaid
flowchart LR
    A[AnnotationResult]
    B[整包完成检查]
    C[生成最小差异 ActionPlan]
    D[执行前置条件检查]
    E{允许执行}
    F[单一浏览器执行器]
    G[观察页面变化]
    H[确认保存结果]
    I[ExecutionReceipt]
    J[停止并人工复核]

    A --> B --> C --> D --> E
    E -->|是| F --> G --> H --> I
    E -->|否| J
    H -->|失败 / 未知| J
```

### 执行器的限制

浏览器执行器不能：

- 自己猜测题型；
- 自己修改业务规则；
- 自由跳转未授权页面；
- 无限重试；
- 在没有保存确认时报告成功。

## 5. 人工复核流程

```mermaid
flowchart TD
    A[自动流程发现问题]
    B{问题类型}
    C[题目边界不确定]
    D[答案匹配不确定]
    E[关系冲突]
    F[规则冲突]
    G[平台状态未知]
    H[人工修改并记录原因]
    I[重新校验]
    J{校验通过}
    K[继续自动流程]
    L[保留待处理状态]

    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G
    C --> H
    D --> H
    E --> H
    F --> H
    G --> H
    H --> I --> J
    J -->|是| K
    J -->|否| L
```

## 6. 开发实现顺序

```mermaid
flowchart LR
    A[数据契约]
    B[确定性校验]
    C[人工构造案例]
    D[OCR/版面解析]
    E[多模态理解]
    F[规则编排]
    G[FakeExecutor]
    H[测试平台]
    I[生产评估]

    A --> B --> C --> D --> E --> F --> G --> H --> I
```

不要跳过前面的阶段。特别是：

```text
没有 AnnotationResult，就不能设计可靠的 ActionPlan；
没有 ActionPlan，就不能安全接浏览器；
没有 FakeExecutor，就不应直接操作测试平台；
没有测试平台验证，就不应考虑生产提交。
```

## 7. 一张图看懂系统边界

```mermaid
flowchart LR
    subgraph OURS[我们需要构建]
        A[页面理解]
        B[题目结构]
        C[答案关系]
        D[规则校验]
        E[AnnotationResult]
        F[ActionPlan]
    end

    subgraph PLATFORM[平台侧]
        G[页面展示]
        H[框和关系操作]
        I[保存与提交]
    end

    A --> B --> C --> D --> E --> F --> G --> H --> I
```

核心边界：

```text
题目标注智能：我们负责
平台页面和最终保存：通过适配器受控调用
```
