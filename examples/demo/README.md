# 非敏感演示样例（P0 验收证据）

本目录是一份**可复现、非敏感**的演示样例，用于证明「扫描 → 分析 → 报告 → 门控降级」闭环能端到端跑通，并留存 P0 验收证据。

## 非敏感声明

- `example.py` 只有刻意构造的静态分析坏模式（`exec`、`assert`、`subprocess shell=True`、占位「密码」字符串），**不含真实密钥、客户数据、生产代码或漏洞利用步骤**。
- `package.json` / `package-lock.json` 只声明一个有已知公告的旧版 `lodash@4.17.20`，用于触发 npm audit；**不安装、不执行**任何依赖脚本。
- 本目录产物可安全提交到仓库并作为验收证据，绝不包含真实凭据。

## 文件

| 文件 | 作用 |
| --- | --- |
| `example.py` | 触发 Semgrep（exec、subprocess shell）与 Bandit（B101 assert、B102 exec、B602 shell）的合成样例 |
| `package.json` / `package-lock.json` | 触发 npm audit 的合成依赖声明（lodash 4.17.20，含原型污染公告） |

## 复现步骤

前置：仓库根目录有 Python 3.12 `.venv`、已 `pip install -r requirements-dev.txt`、已 `npm install --ignore-scripts`（见 [部署步骤](../../docs/deployment-steps.md)）。

在**仓库根目录**执行三路扫描（npm audit 以演示目录为目标以读取这里的 lockfile）：

```powershell
.\.venv\Scripts\python.exe -m scanner.run_semgrep --target examples\demo --artifacts examples\demo\artifacts
.\.venv\Scripts\python.exe -m scanner.run_bandit --target examples\demo --artifacts examples\demo\artifacts
.\.venv\Scripts\python.exe -m scanner.run_npm_audit --target examples\demo --artifacts examples\demo\artifacts
```

确定性分析 + 上下文证据 + 五格式报告：

```powershell
.\.venv\Scripts\python.exe -m agent.cli `
  --input examples\demo\artifacts\findings.json `
  --input examples\demo\artifacts\bandit-findings.json `
  --input examples\demo\artifacts\npm-audit-findings.json `
  --repo-root . `
  --output-dir examples\demo\artifacts

.\.venv\Scripts\python.exe -m reporting.cli `
  --input examples\demo\artifacts\findings.json `
  --input examples\demo\artifacts\bandit-findings.json `
  --input examples\demo\artifacts\npm-audit-findings.json `
  --analysis examples\demo\artifacts\analysis.json `
  --output-dir examples\demo\artifacts `
  --format all
```

## 预期结果

- `artifacts/findings.json`：Semgrep 至少报 `exec-detected` 与 subprocess shell 类 finding。
- `artifacts/bandit-findings.json`：Bandit 至少报 B101、B102、B602。
- `artifacts/npm-audit-findings.json`：npm audit 报 `npm-audit/lodash` 原型污染（severity 归一化为 `error`）。
- `artifacts/analysis.json`：每条 finding 带 `confirmed`/`suspicious`/`possible_false_positive` 分类与成因/影响/修复建议；`backend` 为 `deterministic`。
- `artifacts/security-report.{json,md,xlsx,docx,pdf}` 与 `artifacts/manifest.json`（含 SHA-256）齐全。

## 清理

演示完成后删除本地 `examples/demo/artifacts/`（已被 `.gitignore` 排除，不应提交）。门控 DeepSeek 的验收用真实受控仓库单独验证，不在本样例中注入任何密钥。
