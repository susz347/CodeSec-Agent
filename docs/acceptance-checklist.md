# 发布验收清单

本文是进入试运行期前的 **P0 验收清单**，也是 [故障 Runbook](runbook.md) 的前置检查。目标是用非敏感数据证明「证据优先、可降级、默认不阻断」的安全审查闭环能端到端跑通，再放真实 PR。

`[ ]` 表示待验证；每项验证通过后勾选并留存证据（命令输出、报告、CI run 链接），**不依赖口头确认**。

## 1. 环境与版本

- [ ] Python 3.12 虚拟环境 `.venv` 就绪。
- [ ] `pip install -r requirements-dev.txt` 成功，`semgrep` 1.163.0 与 `bandit` 1.9.4 可执行。
- [ ] Node 20 就绪，`npm install --ignore-scripts` 成功（DOCX 渲染）。
- [ ] 版本号与 [Runbook §5.2](runbook.md#52-版本升级清单升级时逐项核对) 清单一致。

## 2. 扫描闭环

- [ ] `scanner.run_semgrep` 对 [演示样例](../examples/demo/README.md) 产出 `artifacts/findings.json`（至少含 `exec-used`）。
- [ ] `scanner.run_bandit` 产出 `artifacts/bandit-findings.json`（至少含 B101/B102/B602）。
- [ ] `scanner.run_npm_audit` 产出 `artifacts/npm-audit-findings.json`（lodash 公告，或对无 lockfile 目标正确跳过）。
- [ ] 归一化 finding 符合 schema 1.0（含 `id`/`tool`/`rule_id`/`severity`/`path`/`code`/`metadata`）。

## 3. 分析闭环

- [ ] 确定性分析对每条 finding 给出 `confirmed` / `suspicious` / `possible_false_positive`。
- [ ] 每条 finding 带 `title`/`cause`/`impact`/`remediation`/`references`。
- [ ] `--repo-root` 上下文读取拒绝绝对路径、`..`、符号链接逃逸与敏感文件（`.env`/`*.pem`/`*.key` 等），越界只跳过该条证据。
- [ ] `--diff` 正确标注 `changed` / `unchanged` / `unknown`。
- [ ] `--triage-store` 正确标注 `new` / `existing` / `unknown`。

## 4. 报告闭环

- [ ] JSON 与 Markdown 报告生成成功。
- [ ] `--format all` 额外生成 xlsx、docx、pdf。
- [ ] `manifest.json` 含文件名 + 字节数 + SHA-256，可校验完整性。
- [ ] 任一文件写入失败时原子回滚，不留下半套新报告。

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
- [ ] 原始扫描产物（`*-result.json`）与含 evidence 的报告按敏感数据处置（见 [保留策略](retention-policy.md)）。
- [ ] 验证 PR 已关闭且未合并；验证分支、临时探针、环境变量与不再需要的 PAT 已清理。

## 8. 验收证据留存

- [ ] [非敏感演示样例](../examples/demo/README.md) 可复现，命令与预期结果一致。
- [ ] 留存一份非敏感 demo 报告（`examples/security-report.md` 或本次 run 产物链接）作为验收证据。

---

**验收结论**：全部勾选后，将本清单与证据一并记录，作为进入试运行期的 P0 验收记录。
