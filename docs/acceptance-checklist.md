# 发布验收清单

本文是进入试运行期前的 **P0 验收清单**，也是 [故障 Runbook](runbook.md) 的前置检查。目标是用非敏感数据证明「证据优先、可降级、默认不阻断」的安全审查闭环能端到端跑通，再放真实 PR。

`[ ]` 表示待验证；每项验证通过后勾选并留存证据（命令输出、报告、CI run 链接），**不依赖口头确认**。

## 1. 环境与版本

- [x] Python 3.12 虚拟环境 `.venv` 就绪。
- [x] `pip install -r requirements-dev.txt` 成功，`semgrep` 1.163.0 与 `bandit` 1.9.4 可执行。
- [x] Node 20 就绪，`npm install --ignore-scripts` 成功（DOCX 渲染）。
- [x] 版本号与 [Runbook §5.2](runbook.md#52-版本升级清单升级时逐项核对) 清单一致。

## 2. 扫描闭环

- [x] `scanner.run_semgrep` 对 [演示样例](../examples/demo/README.md) 产出 `artifacts/findings.json`（至少含 `exec-detected`）。
- [x] `scanner.run_bandit` 产出 `artifacts/bandit-findings.json`（至少含 B101/B102/B602）。
- [x] `scanner.run_npm_audit` 产出 `artifacts/npm-audit-findings.json`（lodash 公告，或对无 lockfile 目标正确跳过）。
- [x] 归一化 finding 符合 schema 1.0（含 `id`/`tool`/`rule_id`/`severity`/`path`/`code`/`metadata`）。

## 3. 分析闭环

- [x] 确定性分析对每条 finding 给出 `confirmed` / `suspicious` / `possible_false_positive`。
- [x] 每条 finding 带 `title`/`cause`/`impact`/`remediation`/`references`。
- [x] `--repo-root` 上下文读取拒绝绝对路径、`..`、符号链接逃逸与敏感文件（`.env`/`*.pem`/`*.key` 等），越界只跳过该条证据。
- [x] `--diff` 正确标注 `changed` / `unchanged` / `unknown`。
- [x] `--triage-store` 正确标注 `new` / `existing` / `unknown`。

## 4. 报告闭环

- [x] JSON 与 Markdown 报告生成成功。
- [x] `--format all` 额外生成 xlsx、docx、pdf。
- [x] `manifest.json` 含文件名 + 字节数 + SHA-256，可校验完整性。
- [x] 任一文件写入失败时原子回滚，不留下半套新报告。

## 5. 门控 DeepSeek

- [ ] 默认后端为 `deterministic`，不调用模型、不访问网络。
- [ ] `--backend deepseek` 且未设置 `DEEPSEEK_API_KEY` 时返回干净配置错误（非堆栈/密钥泄漏）。
- [ ] 有 key 时仅 `changed + new + error + confirmed + code 非空 + 完整未截断证据` 的 finding 外发，单批 ≤ 10。
- [ ] 网络/HTTP/JSON/契约错误降级为确定性分析，`analysis.json` 的 `backend` 字段如实反映。
- [ ] 日志、报告、产物、评论中均无 `DEEPSEEK_API_KEY`。

## 6. CI 闭环

- [ ] `security-scan.yml` 在同仓库、非 Bot 的 PR 上跑绿（`review`/`scan`/`test` 三检查通过）。
- [ ] PR 摘要成功发布，且不含源码片段或凭据。
- [ ] 上传产物步骤配置 `retention-days: 30`（见 workflow 上传步骤）。
- [ ] `test.yml` 完整单测通过。
- [ ] Fork PR 与 Bot 触发被跳过，未使用 `pull_request_target`。

## 7. 安全边界

- [ ] Git 历史、workflow、`.pr_agent.toml`、日志中无 API Key 或 PAT。
- [x] 原始扫描产物（`*-result.json`）与含 evidence 的报告按敏感数据处置（见 [保留策略](retention-policy.md)）。
- [ ] 验证 PR 已关闭且未合并；验证分支、临时探针、环境变量与不再需要的 PAT 已清理。

## 8. 验收证据留存

- [x] [非敏感演示样例](../examples/demo/README.md) 可复现，命令与预期结果一致。
- [x] 留存一份非敏感 demo 报告（`examples/security-report.md` 或本次 run 产物链接）作为验收证据。

---

**验收结论**：全部勾选后，将本清单与证据一并记录，作为进入试运行期的 P0 验收记录。

## 已留存的本地 Demo 证据（2026-08-24）

- 执行基线：`origin/main` 的 `2c1e293`；Python 3.12.13、Node 20.20.1、npm 10.8.2、Semgrep 1.163.0、Bandit 1.9.4。
- 三路扫描结果：Semgrep 命中 `exec-detected` 与 `subprocess-shell-true`；Bandit 命中 B101、B102、B602（另有 B404/B105）；npm audit 将 lodash 高危公告归一化为 `error`。共 8 条 finding。
- 确定性分析：`backend=deterministic`，8 条分析项（`confirmed=6`、`possible_false_positive=2`），每项均带上下文证据。
- 五格式报告：`security-report.json`、`.md`、`.xlsx`、`.docx`、`.pdf` 已生成；`manifest.json` 记录对应 SHA-256。报告清单中的 Markdown 哈希为 `81f6189dcc674985af661274ecba5758d057ae434d82d81335b61aab1b9606ca`。
- 结构性行为验证：`tests.test_context`、`tests.test_diff`、`tests.test_triage`、`tests.test_reporting_cli` 共 40 项通过；1 项 Windows 符号链接测试因平台不支持跳过。
- 报告样例：[`examples/security-report.md`](../examples/security-report.md) 为仓库内保留的非敏感报告样例。本次本地 `examples/demo/artifacts/` 仅作验证，按保留策略在提交前删除，不提交。

第 5 节、第 6 节和第 7 节中与受控 PR、Secret、CI、探针清理相关的条目，仍待任务 2 的真实 PR 验证完成后再勾选。
