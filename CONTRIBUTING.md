# Contributing — frugalgpt-router（Community Edition）

感谢你考虑为本仓库贡献。本仓库是 FrugalGPT 范式的社区演示实现，欢迎以下类型的贡献：

- Bug 修复与边界用例补强
- 规则路由的新关键词/阈值改进（需附测试）
- 文档改进（README、示例、复现材料）
- 新平台的适配（非商业能力）

## 开发环境

- Python ≥ 3.9，**仅标准库**（运行期无第三方依赖；请勿引入）
- 冒烟测试：

```bash
python tests/test_smoke.py
```

## 提交规范

1. 说明动机与影响（一句即可）。
2. 规则变更必须带测试：在 `tests/test_smoke.py` 中补充用例，并说明新行为对已有分档的影响。
3. 保持零依赖：不要向 `pyproject.toml` 的 `dependencies` 添加运行期依赖。
4. 文档改动保持面向开发者（安装 / API / 配置 / 复现），不写入内部决策或商业信息。

## 许可注意事项

本仓库以 **FrugalGPT Community License 1.0** 发布（源码可见，非 OSI 开源）。提交贡献即表示你同意
该许可条款（见 `LICENSE` 第 4 节）。商业能力（学习式路由、语义路由、漂移监控等）不属于本仓库范围，
请勿以本仓库名义发布此类实现。

## 报告问题

Bug 与安全问题分别走 GitHub Issues 与 `SECURITY.md` 的私密通道。
