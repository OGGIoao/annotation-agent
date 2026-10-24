# Annotation Agent 贡献指南

## 提交前检查

```bash
uv run pytest
uv run python -m compileall app
 git diff --check
```

## 提交规范

使用清晰、单一目的的提交：

```text
feat: add annotation contract models
fix: validate cross-page relation
chore: update rule fixtures
```

## 分支建议

```text
main                    # 稳定主线
feat/contracts          # 数据契约
feat/rules-math         # 数学规则
feat/ocr-adapter        # OCR 适配
feat/graph              # 流程编排
feat/evaluation         # 评测
```

涉及规则、数据契约和平台 payload 的修改，优先走 Pull Request，不要直接在主线堆叠未验证代码。
