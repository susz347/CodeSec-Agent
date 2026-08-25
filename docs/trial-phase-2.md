# 试运行期 · 第二阶段运营规范

**状态：** 自 2026-08-25 起执行；本文件是试运行期的权威运营规范。P0 的已完成验收记录保持在[发布验收清单](acceptance-checklist.md)，故障处置仍以[故障 Runbook](runbook.md)为准；本期逐 PR 的非敏感记录写入[第二阶段日志](trial-phase-2-log.md)。

## 1. 目标与范围冻结

本期用 2–4 周真实 PR 的扫描、分析和人工处置数据，判断现有系统的准确率与运营负担是否可接受；先累积证据，再决定是否提出后续变更。扫描和 PR 摘要维持**默认提示、绝不因发现本身阻断合并**的行为。

以下能力在本期冻结：RAG、数值风险评分、Web UI、扫描规则扩展，以及 merge gate（CI 阻断）。不得借“试运行”修改扫描规则、放宽 Fork/Bot guard、采用 `pull_request_target`，或把 workflow 改为按 finding 失败。

所有变更继续在 `codex/*` 分支上经 PR 进入 `main`；不得直接推送 `main`。原始扫描产物、含 evidence 的报告及任何密钥，继续按[保留策略](retention-policy.md)处理，不能提交到本日志、issue 或聊天。

## 2. 每个真实 PR 的运营节奏

### 2.1 计数口径

“真实 PR”指同仓库、非 Bot、为实际产品或维护工作创建的 PR，且由 `security-scan.yml` 成功产生一次 PR 触发的扫描结果。P0 demo、受控探针、临时验证分支、仅 `workflow_dispatch` 的 run，以及因重跑同一提交产生的 run，均不计入 PR 数。

扫描完成后，triage owner 先看新增（`baseline_status=new`）且变更相关（`diff_status=changed`）的 `confirmed`、`suspicious` 和 `error` finding；`existing` 或 `unknown` 项仍可处置，但要在日志中如实说明。门控 DeepSeek 的 `backend` 仅记录为 `deepseek-gated` 或 `deterministic`；不得记录请求内容、错误响应或 key。

### 2.2 人工处置与存储

每一个终态人工处置必须保留：fingerprint、人工判定、机器标签、reviewer、时间和一句话依据。终态人工判定仅可为 `true_positive`、`false_positive`、`accepted_risk`、`needs_fix`。真实 PR 必须填写实际 reviewer 名称，不得使用 `codex-trial` 等演示身份。

使用既有 CLI 写入版本化存储（示例值必须替换为真实值）：

```powershell
.\.venv\Scripts\python.exe -m agent.triage_cli disposition `
  --store .codesec\triage.json `
  --fingerprint <fingerprint> `
  --resolution <true_positive|false_positive|accepted_risk|needs_fix> `
  --reviewer <human-reviewer> `
  --machine-label <confirmed|suspicious|possible_false_positive> `
  --note "<one-sentence, non-sensitive reason>"
```

`.codesec/triage.json`只保存基线和处置记录；不存源码、报告、耗时或遗漏。耗时、PR 聚合数据和去标识化的漏报记录写入[第二阶段日志](trial-phase-2-log.md)。`baseline` 命令会重建 store；试运行期间不得用它覆盖已有处置，除非先备份并通过单独 PR 审核该基线变更。

### 2.3 周期与检查点

- 每个真实 PR：扫描完成后登记一行 PR 记录；有人工结论时更新 triage store 和日志。
- 每周：更新一次聚合指标和规则覆盖表，核对是否出现只收集误报的偏差。
- 第 2 周：只做数据质量检查，不调规则；若 confirmed 风险样本不足，登记为覆盖缺口。
- 第 4 周或同时满足 §4 的退出条件时：完成 P2 复盘。四周后样本仍不足时，结论为“保留（继续试运行）”，并明确下一检查日期；不得静默降低阈值或以“待观察”代替决策。

## 3. 校准样本与两条度量轴

### 3.1 样本平衡与漏报

不得只处置明显误报（例如 Bandit 的子进程导入）。除这类样本外，必须主动覆盖真实或确认类 finding：在真实 PR 自然出现时，优先完成 Semgrep `exec-detected`、`use-defused-xml` 等高风险规则的人工处置。不得为了凑样本向真实 PR 注入漏洞。

P2 复盘前，至少应有 5 条机器标签为 `confirmed` 的终态人工处置，覆盖至少 2 个 Semgrep 安全规则 ID，且至少 1 条人工判定为 `true_positive` 或 `needs_fix`。若真实 PR 未自然出现 `exec-detected` 或 `use-defused-xml`，日志必须明确标出该覆盖缺口；该规则只能作“保留（样本不足，不微调）”结论。

发现“真实风险但扫描未命中”时，写入日志的“漏报种子”表：只记去标识化的风险类别、来源、发现周和处置状态，不记源码、路径、片段或原始报告。它是未来 P4 扫描规则扩展的候选语料；本期只记录，不实现规则。

### 3.2 准确率

准确率按工具和规则分层，且同运营负担分开汇报：

| 指标 | 算法 | 初始可接受目标 |
| --- | --- | --- |
| 机器/人工一致率 | 在可比较的终态记录中，`confirmed → true_positive / needs_fix / accepted_risk` 与 `possible_false_positive → false_positive` 计为一致；`suspicious` 单列，不进入分母。`一致数 ÷ 可比较数`。 | 全局样本 ≥10 时 ≥80%。 |
| 规则 FP 率 | 同一 tool/rule 的 `false_positive ÷ 全部终态人工处置`。 | 仅样本 ≥3 的规则可用于调整判断。 |
| confirmed 覆盖 | §3.1 所定义的 confirmed 终态处置数、规则数和正向人工结论。 | 5 条、2 个 Semgrep 规则、至少 1 条 `true_positive` 或 `needs_fix`。 |

`accepted_risk` 表示 finding 仍有效、但业务接受风险，故它不计入 FP。任何样本少于 3 条的规则都不做“调整”或“排除”判断。

### 3.3 运营负担

| 指标 | 算法 | 初始可接受目标 |
| --- | --- | --- |
| 每 PR finding 数 | 本周 finding 总数 ÷ 本周真实 PR 数。 | 只记录趋势，不单独作为放开能力的依据。 |
| 每 PR 人工复核数 | 本周需要人工判断的 finding 数 ÷ 本周真实 PR 数。 | ≤5；超出时先分析来源，不立即改规则。 |
| 处置时长 | 从 PR 扫描完成到终态人工处置的小时数；报告中位数与均值。 | 中位数 ≤2 个工作日。 |
| 门控后端与降级 | 每周 `deepseek-gated`、`deterministic` 和无候选 PR 数。 | 只监测可用性与成本，不以降级为失败。 |

这些是可审计的初始运营目标。若需调整某一阈值，必须通过 PR 修改本规范，并写明调整前后值、理由和生效日期。准确率和运营负担两轴都达到相应目标，才可讨论是否重新开启冻结能力；仅一轴达标则继续试运行。

## 4. P2 复盘退出标准与结论格式

满足以下全部条件，才可开始“数据充分”的 P2 复盘：

1. 至少 15 个真实 PR；
2. 至少 30 条终态人工 disposition；
3. 任一准备微调的规则至少有 3 条终态人工 disposition；
4. 已完成 §3.1 的 confirmed 覆盖，或将未自然出现的规则明确写为覆盖缺口并作“保留（样本不足）”结论；
5. 同时计算 §3.2 和 §3.3 的全部指标。

复盘对每个候选微调点都必须填写下表，结论只能是**保留、调整或排除**。样本不足对应“保留（样本不足，不调整）”，不是“待观察”。结论要附数量、比例和至少一句数据依据。

| tool / rule / 运营点 | 样本与人工判定 | 准确率数据 | 运营负担数据 | 结论（保留 / 调整 / 排除） | 数据依据与 owner |
| --- | --- | --- | --- | --- | --- |
| 示例：`bandit:B404` | `n=...` | `FP=...%` | `...` | `保留（样本不足，不调整）` | `...` |

即使退出条件达到，也不在同一 PR 中实现扫描规则、提示词或门控调整；先以独立提案说明影响、回滚方式和验证计划。

## 5. 冻结能力的重新讨论触发条件

满足条件仅表示可以创建提案；是否实施仍须独立评审，且不可在本期绕过 §1 的冻结范围。

| 冻结能力 | 可重新讨论的最小证据 |
| --- | --- |
| Merge gate | 一个明确 tool/rule 至少 10 条终态人工处置、FP 率 <10%、无未解决的 `needs_fix` 处置，并已有经过人工审核的 override / allowlist 逃生口和至少 5 个真实 PR 的非阻断影子运行记录。 |
| RAG | 至少 15 条 `confirmed` / `true_positive` / `needs_fix` 相关记录，覆盖 3 个以上规则或漏洞类别；人工依据表明现有本地 CWE/OWASP 参考不足，且无敏感源码进入检索的设计方案。 |
| 数值风险评分 | 退出条件全部满足；每个拟纳入评分的工具/规则至少 3 条处置；连续两周可复算指标，且准确率与运营负担均达到 §3 的目标。 |
| Web UI | 至少 2 名实际运营者、10 个真实 PR 的手工日志证据，显示查找、汇总或处置记录是主要瓶颈（中位处置时长超过目标或每周手工汇总超过 30 分钟）。 |
| 扫描规则扩展 | 同一未覆盖漏洞家族或语言至少 3 条去标识化漏报种子，且 P2 复盘确认现有扫描无等效规则；后续仅作为 P4 独立提案。 |

## 6. 交接与证据边界

换人时，先读本规范、Runbook 和最新日志；再用 `agent.triage_cli stats --store .codesec\triage.json` 核对可提交的处置统计。不要把原始 artifacts、含 evidence 的报告、PR diff、源码路径或密钥复制进交接材料。保留和删除责任始终按[产物保留与归档策略](retention-policy.md)执行。
