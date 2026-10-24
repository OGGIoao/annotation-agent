# Annotation Rover 小项目规格

## 1. 一句话定义

Annotation Rover 是一个教学用的小型受控 Agent：它处理一张简化练习页，提出题目标注候选，经过确定性校验，生成动作计划，在模拟画布上执行并返回可审计回执。

## 2. 它刻意不做什么

第一版不做：

- 真实标注平台登录或提交；
- 真实用户和真实题目图片；
- OCR 模型部署；
- 自动扫码、听力和手写识别；
- 多 Agent 自由协作；
- 生产级数据库、队列或分布式部署；
- 任何不可解释的“模型说了算”。

## 3. 最小输入

第一版用 JSON 页面 fixture 代替图片：

```json
{
  "page_id": "demo-001",
  "width": 1200,
  "height": 1600,
  "blocks": [
    {
      "id": "text-1",
      "text": "1. 计算 2 + 3 = ____",
      "bbox": [100, 120, 900, 240]
    }
  ]
}
```

后续 L4 再增加图像和 OCR 块。先用 JSON 是为了把“Agent 工作流”与“视觉模型误差”分开学习。

## 4. 最小输出

```json
{
  "status": "approved",
  "questions": [],
  "answer_boxes": [],
  "relations": [],
  "action_plan": [],
  "receipt": null,
  "warnings": [],
  "trace": []
}
```

## 5. 角色分工

### Rover Orchestrator

负责流程状态，不负责凭空判断业务事实。

### Candidate Model

负责提出候选题框、答案框和属性。第一阶段由 `FakeModel` 模拟，后续可替换为真实模型。

### Validator

负责坐标、关系、字段和规则。它是确定性质量门，不调用模型。

### Planner

把通过校验的结果转换成声明式动作。

### FakeExecutor

在内存画布中执行动作，模拟平台的创建框、绑定关系和保存。

### Observer

检查预期状态是否出现，并生成 `ExecutionReceipt`。

## 6. 学习版状态机

```text
RECEIVED
  → CANDIDATE_READY
  → VALIDATED
      ├─ APPROVED
      ├─ NEEDS_REVIEW
      └─ REJECTED
  → PLAN_READY
  → EXECUTING
  → OBSERVING
      ├─ CONFIRMED
      ├─ DIFFERENCE
      └─ UNKNOWN
```

状态机是教学对象，不代表主项目最终状态枚举已经冻结。

## 7. 逐站演进

| 版本 | Rover 增加的能力 | 对应学习 |
|---|---|---|
| L0 | 接受 fixture 并返回结果 | 环境、测试、输入输出 |
| L1 | 拒绝非法框和关系 | 契约与校验 |
| L2 | 通过/复核/失败分支 | LangGraph 工作流 |
| L3 | FakeModel 输出结构化候选 | 模型边界 |
| L4 | 处理文字块和坐标 | 视觉证据与预览 |
| L5 | 生成并执行动作计划 | Tool Calling 与安全 |
| L6 | 暂停、人工决定、恢复 | Human-in-the-loop |
| L7 | 输出错误和质量报告 | Agent 评测 |

## 8. 与主项目的迁移边界

可以迁移的思想：

- 先契约后模型；
- 结构和关系先于语义属性；
- 模型候选必须过校验；
- `AnnotationResult → ActionPlan → ExecutionReceipt`；
- 人工复核和可恢复状态；
- 固定 fixture 和回归测试。

不能直接迁移的内容：

- 教学版简化题型；
- FakeModel 的准确率；
- FakeExecutor 对平台行为的假设；
- 用 JSON 块代替真实 OCR 的结论；
- 为了演示而简化的状态和规则。

## 9. 完成定义

Annotation Rover 不以“能演示”作为完成。L7 完成时必须：

- 有一套可重复运行的 fixture；
- 有正常、失败、复核三类测试；
- 能在不调用外部模型的情况下运行主流程；
- 能替换 `FakeModel` 和 `FakeExecutor` 而不改动领域契约；
- 有一份评测报告；
- 有每站复盘；
- 能向主项目提交一份“可迁移/不可迁移”清单。
