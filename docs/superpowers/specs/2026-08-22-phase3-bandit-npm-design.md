# Phase 3 Bandit 与 npm audit 设计

## 目标

在已验证的 Semgrep-first 切片上完成 Phase 3：接入 Bandit 与 npm audit。两个工具各自保存原始 JSON、独立归一化与执行；二者都输出已有的 schema `1.0` finding 文档，不改变 Semgrep 的既有语义。

## 范围

### 包含

- 固定 Bandit `1.9.4`，使用递归扫描和 JSON formatter。
- 在存在 `package-lock.json` 的 Node 目标上运行 `npm audit --json --package-lock-only --ignore-scripts`。
- 为每个工具保存原始 JSON 与归一化 finding JSON。
- 为模型扩展显式 `tool` 与 `ruleset` 参数，同时保持 Semgrep 输出的字段与 ID 不变。
- 对每个工具提供离线 fixture 单元测试、子进程 mock 测试和一次真实 CLI 验证。
- 更新部署文档、清单和路线图，标记 Phase 3 完成。

### 不包含

- 更改 `schema_version`、合并不同扫描器的 findings、风险评分、LLM 分析、报告、Action 或 PR 评论。
- 自动执行 `npm install`、`npm audit fix`，或运行任意 npm lifecycle script。
- 自动忽略、修复或降级发现。

## 架构

```text
Python target -> run_bandit -> artifacts/bandit-result.json -> normalize_bandit -> artifacts/bandit-findings.json
Node target   -> run_npm_audit -> artifacts/npm-audit-result.json -> normalize_npm_audit -> artifacts/npm-audit-findings.json
```

运行器只拥有子进程和文件系统；归一化器必须是纯 JSON 函数；`scanner.models` 继续是唯一的稳定输出契约。

## 统一契约调整

`Finding.create` 增加关键字参数 `tool`（Semgrep 调用显式传入 `"semgrep"`）。ID 仍是前 16 位 SHA-256，但输入改为：

```text
tool|rule_id|path|start_line|start_column
```

因此既有 Semgrep ID 的输入和值保持不变。`ScanDocument.create` 增加可选关键字参数 `tool` 与 `ruleset`，默认值仍为 Semgrep 的 `"semgrep"` 与 `"p/security-audit"`，所以现有调用与输出不变。

所有适配器只输出 `error`、`warning`、`info`、`unknown`。工具原始严重级别保存在 `metadata.<tool>_severity`；`metadata` 仅允许 `cwe`、`owasp`、`category`、`technology`、`references` 和该工具的原始严重级别键。

## Bandit 适配器

### 输入与映射

Bandit JSON 顶层必须包含 `results` 与 `errors`。每个结果必须有 `test_id`、`filename`、`line_number`、`issue_text` 和 `issue_severity`；缺失时抛出 `BanditFormatError` 并给出 `/results/<index>/...` JSON Pointer。

| Finding 字段 | Bandit 字段或规则 |
| --- | --- |
| `tool` | `bandit` |
| `rule_id` | `test_id` |
| `path` | 相对扫描目标的 `filename` |
| `start_line` | `line_number` |
| `end_line` | `line_range` 的最大行；无此字段时等于 `line_number` |
| columns | `null` |
| `message` | `issue_text` |
| `code` | `code` 或 `null` |
| severity | `HIGH -> error`，`MEDIUM -> warning`，`LOW -> info`，其他为 `unknown` |
| metadata | `references: [more_info]`（若有），`bandit_severity` |
| `raw_reference` | `/results/<index>` |

运行器命令等价于：

```text
bandit -r <target> -f json -o artifacts/bandit-result.json
```

退出码 `0`（无发现）和 `1`（有发现）只要原始 JSON 可解析即为成功；其他退出码、缺少原始文件或无效 JSON 为失败。工具版本固定写为 `1.9.4`，规则集为 `bandit-default`。

## npm audit 适配器

### 输入与映射

npm audit JSON 顶层必须包含 `vulnerabilities` 与 `metadata`。每个 vulnerability 条目必须有键名、`name`、`severity`、`range` 和 `via`；缺失时抛出 `NpmAuditFormatError` 并给出 JSON Pointer。`via` 中的对象可提供 `url` 和 `cwe`；字符串 advisory ID 只保留为证据文本，不伪造 URL。

每个 vulnerability 键产生一个 finding：

| Finding 字段 | npm audit 字段或规则 |
| --- | --- |
| `tool` | `npm-audit` |
| `rule_id` | `npm-audit/<vulnerability key>` |
| `path` | `package-lock.json` |
| lines / columns | `1` / `null`，因为 audit 不提供源码位置 |
| `message` | advisory 标题或包名与受影响 range 的安全说明 |
| `code` | `null` |
| severity | `critical`、`high -> error`；`moderate -> warning`；`low`、`info -> info`；其他为 `unknown` |
| metadata | `category: dependency`、去重后的 `cwe` 与 `references`、`npm_audit_severity` |
| `raw_reference` | `/vulnerabilities/<JSON Pointer escaped key>` |

运行器从目标目录运行：

```text
npm audit --json --package-lock-only --ignore-scripts
```

它捕获 UTF-8 stdout 并写入 `artifacts/npm-audit-result.json`。退出码 `0` 与 `1` 都是扫描成功；其他退出码是失败。若目标没有 `package-lock.json`，抛出 `NpmAuditNotApplicable`，不写产物，也不把缺少 Node 项目伪装成无漏洞。`npm --version` 的输出记录为工具版本；规则集为 `npm-advisory-database`。

## 测试与真实验证

离线 fixture 覆盖每个适配器的空结果、完整 finding、未知严重级别、缺失顶层字段、缺失必填 finding 字段、JSON Pointer 与元数据过滤。运行器 mock 测试覆盖精确命令、发现退出码、不可接受退出码、缺失或无效原始 JSON、产物写入与 npm 缺少 lockfile。

真实 Bandit 验证扫描本仓库 Python 代码。真实 npm 验证扫描版本控制的最小 fixture Node 项目；fixture 只有 `package.json` 和 `package-lock.json`，不含 `node_modules`，命令使用 `--package-lock-only --ignore-scripts`，不会安装依赖或执行脚本。验收时运行所有离线测试、检查每个原始/归一化文档均可解析、检查四份产物被 Git 忽略，并记录每种 finding 数量。

## 依据

- [Bandit JSON formatter](https://bandit.readthedocs.io/en/latest/formatters/) 提供 JSON 输出；其示例结果包含 `test_id`、位置、严重级别和文本字段。
- [npm audit 文档](https://docs.npmjs.com/cli/audit/) 规定 `npm audit --json` 的 JSON 输出与“有漏洞时非零”的退出语义，并说明 `--package-lock-only` 与 `--ignore-scripts` 配置。
- [Bandit 源码库](https://github.com/PyCQA/bandit) 是其公开实现与 issue 入口。
