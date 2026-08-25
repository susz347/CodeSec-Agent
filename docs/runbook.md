# 故障 Runbook（运维主文档）

本文是 CodeSec-Agent 的**唯一运维主文档**：出现异常时按本文定位、降级、重跑与收尾。目标是换人接手也能稳定运行，不依赖个人对命令、配置或异常处置的记忆。

进入处置前先完成 [发布验收清单](acceptance-checklist.md)（前置检查）；处置收尾时按 [产物保留与归档策略](retention-policy.md) 执行删除/归档（收尾步骤）。

试运行期的真实 PR triage、量化复盘和冻结能力重启条件以[第二阶段运营规范](trial-phase-2.md)为准；逐 PR 的非敏感汇总记录写入[第二阶段运营日志](trial-phase-2-log.md)。

部署与运行细节见 [部署与运行步骤](deployment-steps.md)；开发状态见 [路线图](roadmap.md) 与 [任务清单](project-checklist.md)。

---

## 1. 系统拓扑与数据流

三个 GitHub Actions workflow（均在 `.github/workflows/`）：

| Workflow | 触发 | 作用 | 失败是否阻断合并 |
| --- | --- | --- | --- |
| `pr-agent.yml` | PR opened/reopened/ready_for_review/synchronize | PR-Agent 自动 review，调用 DeepSeek | review 失败只影响该评论，不阻断合并 |
| `security-scan.yml` | PR 或 `workflow_dispatch` | 扫描 → 分析 → 五格式报告 → 上传产物 → PR 摘要 | 见 §1.1 |
| `test.yml` | PR 或 `workflow_dispatch` | 完整单测 `python -m unittest discover -v` | 单测失败会红（需修复） |

### 1.1 security-scan.yml 步骤顺序

`Checkout → Python → Node → Install deps → Build PR diff → Run Semgrep → Run Bandit → Run npm audit → Analyze → Render reports → Upload reports → Post PR summary`，单 job 超时 15 分钟。

**关键边界**：扫描发现本身**永不 fail 作业**（Semgrep/Bandit/npm audit 的发现退出码 1 被正常处理）；但 **`Render reports` 与 `Upload reports` 步骤失败会使 job 变红**。这是与「扫描不阻断」的区别点。

### 1.2 两条 DeepSeek 消费路径（务必区分）

| 路径 | 位置 | 失败行为 |
| --- | --- | --- |
| PR-Agent 自动 review | `pr-agent.yml` | DeepSeek 401/429/超时会**直接导致该 review 失败**，无降级 |
| 门控 DeepSeek 分析 | `security-scan.yml` + `agent/security_reviewer.py` | 传输/HTTP/JSON/契约错误**自动降级到确定性分析**，`analysis.json` 的 `backend` 字段变为 `deterministic`，不 fail 作业 |

因此排查 DeepSeek 错误时，先判断报错来自哪条路径。

---

## 2. 安全边界（不可违反）

1. **密钥只进 Secret 或进程环境**：`DEEPSEEK_API_KEY` 只存在于 GitHub Repository Secret，或用户自己的 PowerShell 进程环境；绝不写入文件、Git 历史、日志、聊天或截图。`GITHUB_TOKEN` 由 GitHub Actions 自动提供，不自行创建。
2. **敏感产物按敏感数据处理**：
   - 原始扫描产物 `artifacts/bandit-result.json`、`artifacts/semgrep-result.json`、`artifacts/npm-audit-result.json`（未上传 CI，但本地会生成）。
   - `artifacts/analysis.json` 与**增强版报告**（含 `--analysis` 生成的五格式报告）内含 `evidence`（局部源码行 + sha256）。
   - 处置时这些文件与含源码的报告同属敏感数据，归档/删除按 §6 执行，不得随意粘贴到聊天或 issue。
3. **不绕过 Fork/Bot guard**：`security-scan.yml` 与 `pr-agent.yml` 均跳过 Bot 触发与 Fork PR，这是刻意的安全边界。**禁止**改用 `pull_request_target` 或放宽 guard 来「让扫描跑起来」。
4. `artifacts/`、`.venv/` 已被 `.gitignore` 排除，不得提交。

---

## 3. 触发与症状 → 处置

### 3.1 扫描失败（Semgrep / Bandit / npm audit）

**症状**：CI 的 `Run Semgrep` / `Run Bandit` / `Run npm audit` 步骤红；或本地命令返回非零退出码。

**定位**：读取该步骤日志，匹配下面的错误原文。

| 错误原文（片段） | 含义 | 处置 |
| --- | --- | --- |
| `Semgrep executable was not found. Install requirements-dev.txt first.` | 未装 Semgrep | `pip install -r requirements-dev.txt` |
| `Bandit executable was not found. Install requirements-dev.txt first.` | 未装 Bandit | 同上 |
| `Semgrep command failed with exit code N` | Semgrep 运行失败（规则集拉取/目标异常） | 看日志中的 Semgrep 错误输出；首次运行需联网拉 `p/security-audit` |
| `Bandit command failed with exit code N` | Bandit 运行失败 | 看日志中的 Bandit 错误输出 |
| `Bandit did not create bandit-result.json` / `Semgrep did not create semgrep-result.json` | 扫描器未产出原始结果 | 检查扫描器日志，确认目标路径与权限 |
| `npm audit requires a target-local package-lock.json` | 目标无 `package-lock.json` | 这是**预期跳过**，不是故障；仅当仓库确有 npm 依赖时才需补充 lockfile |
| `npm executable was not found.` / `npm --version failed.` | 未装 npm 或 npm 异常 | 确认 Node 20 环境与 npm 可用 |
| `npm audit failed with exit code N` | npm audit 本身失败 | 看日志中的 npm 错误输出 |
| `... could not be normalized: ...` | 原始 JSON 解析/归一化失败 | 检查扫描器版本是否与代码中 pinned 版本一致（§5.2） |

**重跑**：CI 用 Actions → Security Scan → `Run workflow`（`workflow_dispatch`）；本地用 §4.2 命令。

### 3.2 DeepSeek 超时 / 401 / 429

先判断来自哪条路径（§1.2）。

**门控 DeepSeek 分析（security-scan.yml）**：
- 症状：`analysis.json` 的 `backend` 字段为 `deterministic`（而不是 `deepseek-gated`），或日志中该步骤未报错但结果全走确定性。
- 这是**预期降级**，不是故障。401/429/超时会被 `LlmReviewer` 捕获并回退确定性分析，扫描不 fail。
- 若想确认原因：本地显式跑一次 `--backend deepseek`（§4.1），直接观察 `LlmTransportError` 细节。

| 错误 | 含义 | 处置 |
| --- | --- | --- |
| 401 | Key 无效/已撤销/未正确注入 | 轮换密钥（§5.1），不要在日志打印 Key |
| 429 | 触发限流 | 等待限流窗口，避免短时间反复触发 |
| 超时（20s） | 网络/服务端慢 | 检查出网与 DNS；确认是否代理拦截 |

**PR-Agent（pr-agent.yml）**：
- 症状：`review` job 红，日志含 LiteLLM 报错。
- 401/429 会直接导致 review 失败。处置同上（轮换密钥 / 等待限流），随后在 PR 上重触发 `/review` 或重新推送提交。

### 3.3 报告生成失败（Render reports）

**症状**：CI 的 `Render reports` 步骤红；或本地 `reporting.cli` 返回非零。

**定位**：匹配下面的错误原文。

| 错误原文（片段） | 含义 | 处置 |
| --- | --- | --- |
| `xlsx rendering dependencies are missing; run: python -m pip install -r requirements-dev.txt` | 缺 openpyxl | `pip install -r requirements-dev.txt` |
| `pdf rendering dependencies are missing; ...` | 缺 pypdf/reportlab | 同上 |
| `docx rendering dependencies are missing; ...` | 缺 DOCX 依赖 | 同上（python 侧） |
| `DOCX rendering requires Node.js and npm install --ignore-scripts.` | 未装 Node | 安装 Node 20 |
| `DOCX rendering dependencies are missing; run: npm install --ignore-scripts` | 缺 npm 依赖 | `npm install --ignore-scripts` |
| `DOCX rendering failed: ...` | Node 渲染脚本报错 | 看 detail；常见为沙箱 Node 文件权限问题（见下） |
| `DOCX renderer returned an invalid document.` | Node 输出非 `.docx`（非 `PK` 头） | 检查 Node 脚本与输入 |
| PDF 字体相关 | 缺 CJK 字体 | 缺省查找 Microsoft YaHei / Noto Sans CJK / DejaVu Sans；用进程级 `CODESEC_REPORT_FONT` 指定 TTF/TTC |

**已知环境问题**：Windows 沙箱（如 Codex 受限环境）中 DOCX 渲染可能因 Node 文件权限失败。属环境限制而非代码缺陷；可在标准 Linux runner（CI）验证通过。

**降级**：报告渲染失败不影响扫描结论本身。可临时只生成 JSON/Markdown（去掉 `--format all`，见 §4.1），这两者无第三方依赖。

### 3.4 artifact 异常

**症状**：`Upload reports` 步骤异常；产物缺失；manifest 校验不通过。

- `Upload reports` 使用 `if-no-files-found: ignore`，无报告文件时不报错。
- `manifest.json` 含文件名 + 字节数 + SHA-256，用于校验完整性；对不上说明产物被篡改或半套写入，应重跑。
- 上传产物清单：`findings.json`、`bandit-findings.json`、`npm-audit-findings.json`、`analysis.json`、`security-report.{json,md,xlsx,docx,pdf}`、`manifest.json`（**原始** `*-result.json` 与 `pr.diff` 不上传）。
- **保留**：`Upload reports` 步骤已配置 `retention-days: 30`（见 `.github/workflows/security-scan.yml` 上传步骤），产物 30 天后自动过期，属实际 workflow 配置而非口头策略。

---

## 4. 通用处置动作

### 4.1 降级到确定性分析

任何 DeepSeek 或报告增强异常，都可降级为纯确定性离线分析（不调用模型、不访问网络）：

```powershell
.\.venv\Scripts\python.exe -m agent.cli `
  --input artifacts\findings.json `
  --input artifacts\bandit-findings.json `
  --input artifacts\npm-audit-findings.json `
  --repo-root . `
  --diff artifacts\pr.diff `
  --triage-store .codesec\triage.json `
  --output-dir artifacts
```

（去掉 `--backend deepseek` 即确定性后端。）

只生成 JSON/Markdown 报告（避开 xlsx/docx/pdf 依赖）：

```powershell
.\.venv\Scripts\python.exe -m reporting.cli `
  --input artifacts\findings.json `
  --input artifacts\bandit-findings.json `
  --input artifacts\npm-audit-findings.json `
  --analysis artifacts\analysis.json `
  --output-dir artifacts
```

（不传 `--format` 默认只出 JSON/Markdown。）

### 4.2 本地重跑扫描

```powershell
.\.venv\Scripts\python.exe -m scanner.run_semgrep --target . --artifacts artifacts
.\.venv\Scripts\python.exe -m scanner.run_bandit --target . --artifacts artifacts
.\.venv\Scripts\python.exe -m scanner.run_npm_audit --target . --artifacts artifacts
```

### 4.3 CI 重跑

- 单步骤重试：Actions → 对应 run → `Re-run failed jobs`。
- 全量重跑：Actions → Security Scan → `Run workflow`（`workflow_dispatch`）。
- **注意**：手动触发不构建 PR diff，故 `diff_status` 全为 `unknown`，且不发布 PR 摘要。需要 diff 语义时用 PR 触发的 run。

### 4.4 删除 / 归档产物

- 产物随 run 自动过期（30 天，§3.4）。需要立即删除：`gh run delete <run-id> --repo susz347/CodeSec-Agent`。
- 需要长期留存再归档：先下载 `gh run download <run-id> --repo susz347/CodeSec-Agent --name security-scan-reports`，再按 [保留策略](retention-policy.md) 归档。
- 本地 `artifacts/`：确认无留存需要后直接删除，不提交。

---

## 5. 密钥轮换与升级路径

### 5.1 DeepSeek Key 轮换

`DEEPSEEK_API_KEY` 被 `pr-agent.yml` 与 `security-scan.yml` 两处共用。轮换步骤：

1. 在 DeepSeek 控制台生成新 Key。
2. 更新仓库 Secret：`Settings → Secrets and variables → Actions → DEEPSEEK_API_KEY → Update`。只粘贴值，不截图、不写文件。
3. 用一次同仓库、非 Bot 的受控 PR 验证两条路径均正常：PR-Agent 发布 review，且至少一条满足 `changed + new + error + confirmed` 的 finding 让门控分析 `backend` 为 `deepseek-gated`。`workflow_dispatch` 不生成 PR diff，不能验证这两项。
4. 在 DeepSeek 控制台撤销旧 Key。
5. 复查日志与评论，确认无 Key 泄露。

### 5.2 版本升级清单（升级时逐项核对）

| 组件 | 位置 | 当前固定版本 |
| --- | --- | --- |
| Semgrep | `scanner/run_semgrep.py` `SEMGREP_VERSION` | `1.163.0` |
| Bandit | `scanner/run_bandit.py` `BANDIT_VERSION` | `1.9.4` |
| npm audit | 系统 npm（`NPM_EXECUTABLE` 可覆盖） | 随 Node 20 |
| PR-Agent Action | `pr-agent.yml` 固定 SHA | `570f67e...`（v0.41.0） |
| 本地 PR-Agent | `deployment-steps.md` 固定 PyPI | `pr-agent==0.39.0` |
| DeepSeek 模型（门控） | `agent/llm.py` `DEFAULT_DEEPSEEK_MODEL` | `deepseek-v4-flash` |
| DeepSeek 模型（PR-Agent） | `.pr_agent.toml` | `deepseek/deepseek-v4-flash` |
| Python | `test.yml` / `security-scan.yml` | `3.12` |
| Node | 同上 | `20` |
| Python 依赖 | `requirements-dev.txt` / `requirements-reporting.txt` | 见文件 |
| npm 依赖 | `package.json` / `package-lock.json` | 见文件 |

升级规则：
- Action 与本地 PR-Agent 当前版本不一致（v0.41.0 vs 0.39.0）是**已知且刻意**的，不要自行把任一端改成浮动版本。
- 升级扫描器或模型后，必须重跑一次真实扫描验证归一化与门控行为，并更新对应版本号与本文档。

---

## 6. 收尾：产物保留与归档

处置结束后按 [产物保留与归档策略](retention-policy.md)执行：明确 `retention-days: 30` 到期后的归档/删除责任人，覆盖原始产物、含 evidence 的报告与本地 `artifacts/`，避免敏感数据长期残留。
