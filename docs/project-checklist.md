# 项目任务清单

本文按四阶段记录真实工程状态。`[x]` 只表示已经产生并验证的本地配置或文档；需要 GitHub、DeepSeek 或用户凭据的端到端任务在取得实际证据前保持未完成。

## Phase 1：GitHub Actions PR-Agent

- [x] 选择目标 GitHub 仓库。
- [x] 在实现分支添加固定 SHA、最小权限的 PR-Agent workflow。
- [x] 在实现分支添加 DeepSeek 共享配置，并禁用备用模型。
- [x] 静态验证 YAML/TOML、触发器、Fork/Bot guard、超时和 synchronize review 行为。
- [x] 补充数据外发、提示注入边界和安全验证 PR 文档。
- [x] 发布、人工审核并合并启用 PR 到 `main`。
- [x] 配置 Repository Secret `DEEPSEEK_API_KEY`。
- [x] 从更新后的 `main` 创建不含敏感数据的短生命周期验证 PR。
- [x] 验证 Action 首次自动 review 与 synchronize review。
- [x] 确认 Action 日志无凭据泄露。

## Phase 2：本地 PR-Agent CLI

- [x] 使用 Python 3.12 创建本地虚拟环境。
- [x] 安装并验证固定版本的本地 PR-Agent CLI。
- [x] 记录无 `py` 启动器、受限缓存和 LiteLLM warning 的处理方法。
- [x] 创建并在当前 PowerShell 会话中使用最小权限 PAT 与 DeepSeek Key。
- [x] 使用默认分支 `main` 的可信配置审查验证 PR，并发布第二条 review。
- [x] 关闭且不合并验证 PR，清理凭据、验证分支和临时探针。

## Phase 3：静态安全扫描与结果归一化

- [x] 安装锁定版本并完成一次真实 Semgrep 扫描验证。
- [x] 运行 Bandit 扫描 Python 代码。
- [x] 运行 npm audit 扫描 Node.js 依赖。
- [x] 实现 Semgrep 原始 JSON 保存与离线归一化。
- [x] 设计统一 finding 数据结构，并统一风险等级、文件位置、规则 ID 和证据字段。

## Phase 4：Agent 分析、报告与自动化

- [x] 创建初始安全审查 Prompt。
- [ ] 将统一 finding 和相关代码片段传入分析流程。
- [ ] 区分确认问题、可疑模式和误报。
- [ ] 生成漏洞原因、影响、修复建议和 CWE/OWASP 参考。
- [ ] 生成 Markdown 报告、扫描摘要、风险统计和发现项表格。
- [ ] 保存完整示例报告。
- [ ] 添加安全扫描 GitHub Action 并保存结果产物。
- [ ] 在 PR 评论中引用报告摘要。
- [ ] 定义风险阈值与合并提示/阻断策略。

## 文档与发布

- [x] README 提供当前状态和权威入口。
- [x] 部署文档覆盖 Phase 1/2、数据边界、验证和安全清理。
- [x] 新手指南、前置知识和路线图使用统一四阶段术语。
- [x] 设计与实施记录说明系统边界和验收依赖。
- [x] 完成 Phase 1/2 的可复现端到端 Demo，并记录非敏感证据。

## 后续增强

- [ ] 增加 OWASP/CWE 知识库目录。
- [ ] 引入 RAG 检索增强。
- [ ] 支持 Word/PDF 报告导出。
- [ ] 支持多语言仓库。
- [ ] 增加误报过滤策略。
- [ ] 增加 Web 可视化界面。
