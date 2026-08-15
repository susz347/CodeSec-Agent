# Semgrep Phase 3 设计

## 目标

实现 CodeSec-Agent Phase 3 的首个可验证切片：使用 Semgrep 对指定目录执行本地静态安全扫描，保存原始 JSON，并将结果转换为稳定、工具无关的 finding JSON。首版只支持 Semgrep；Bandit 与 npm audit 在本切片完成真实验证后以独立适配器接入。

## 范围

### 包含

- 使用固定版本的 Semgrep CLI 扫描指定目录。
- 使用显式 `p/security-audit` 规则集。
- 将完整 Semgrep JSON 写入可指定的产物目录。
- 从 Semgrep JSON 生成统一 finding JSON。
- 记录扫描元数据：工具、工具版本、规则来源、目标目录和执行时间。
- 提供离线 fixture 测试，以及一次真实 CLI 端到端验证。
- 更新路线图、任务清单和操作文档，使其反映 Semgrep-only 的首版范围。

### 不包含

- Bandit、npm audit、SCA、密钥扫描或任何第二扫描器。
- GitHub Actions、PR 评论、合并阻断、DeepSeek 调用或报告生成。
- CWE/OWASP 知识库、误报自动判定或自动修复。
- 将扫描产物提交到 Git；产物只能保存在被忽略的目录。

## 已确认的设计决策

1. 采用“扫描执行器 + 单独归一化器”。执行器不解释 finding，归一化器不启动外部进程。
2. 规则集显式使用 `p/security-audit`，不依赖 CLI 默认行为。该规则集的解析依赖网络，因此单元测试完全使用版本控制的离线 JSON fixture。
3. Semgrep CLI 版本固定为 `1.163.0`；升级必须通过 fixture 与真实扫描复验。
4. 扫描发现是成功结果，不是程序错误。配置不可用、Semgrep 无法启动、非预期退出码、缺少原始 JSON 或 JSON 无法解析才是失败。
5. 归一化器只依赖 Semgrep JSON 的稳定核心字段：`results`、`errors`、`paths`，以及每个结果中的规则、路径、起止位置、消息、严重级别和元数据。不得以官方标注为 experimental 的字段为必需输入。

## 架构

```text
目标目录
  -> scanner.run_semgrep
  -> Semgrep CLI --config p/security-audit --json
  -> artifacts/semgrep-result.json
  -> scanner.normalize_semgrep
  -> artifacts/findings.json
```

### 模块职责

| 模块 | 职责 | 不负责 |
| --- | --- | --- |
| `scanner/run_semgrep.py` | 验证命令参数、创建产物目录、调用 CLI、保存原始 JSON、生成扫描元数据 | finding 字段映射、风险推理、报告 |
| `scanner/normalize_semgrep.py` | 验证 JSON 顶层结构、映射结果、写出统一 finding 文档 | 启动 Semgrep、联网、修改原始 JSON |
| `scanner/models.py` | 定义 finding 与扫描文档的数据模型、序列化和严重级别映射 | 文件系统或子进程操作 |
| `tests/fixtures/semgrep/` | 保存无敏感数据的 Semgrep JSON fixture | 存放真实仓库扫描产物 |

## 数据契约

`artifacts/findings.json` 是包含扫描元数据与 `findings` 数组的 JSON 文档。顶层字段为：

```json
{
  "schema_version": "1.0",
  "scan": {
    "tool": "semgrep",
    "tool_version": "1.163.0",
    "ruleset": "p/security-audit",
    "target": ".",
    "started_at": "2026-08-15T00:00:00Z"
  },
  "findings": []
}
```

每个 finding 的字段为：

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `id` | string | 对同一 `tool`、`rule_id`、`path`、`start_line` 和 `start_column` 组合稳定计算的标识符。 |
| `tool` | string | 固定为 `semgrep`。 |
| `rule_id` | string | Semgrep `check_id`。 |
| `severity` | string | `error`、`warning`、`info` 或 `unknown`。 |
| `path` | string | 相对于扫描目标的文件路径。 |
| `start_line` / `end_line` | integer | 对应 Semgrep 位置；缺失位置是不可归一化错误。 |
| `start_column` / `end_column` | integer | 对应 Semgrep 位置；缺失时为 `null`。 |
| `message` | string | Semgrep `extra.message`。 |
| `code` | string or null | Semgrep `extra.lines`；不自行读取源文件。 |
| `metadata` | object | 仅保留可用的 `cwe`、`owasp`、`category`、`technology` 和 `references`。 |
| `raw_reference` | string | 原始 `results` 数组中的 JSON Pointer，例如 `/results/0`。 |

严重级别大小写归一化为小写；无法识别的值映射为 `unknown`，同时保留原始值于 `metadata.semgrep_severity`。

## 运行行为

运行器接收目标目录和产物目录。它调用等价于下列命令的 Semgrep CLI：

```text
semgrep scan --config p/security-audit --json --output artifacts/semgrep-result.json .
```

运行器必须捕获标准错误用于错误信息，但不得把它写入产物或将其当作扫描结果。它允许 Semgrep 的“已发现问题”退出结果，只要原始 JSON 存在且可解析；其他非零退出结果必须包含命令、退出码和不含敏感信息的错误摘要。真实扫描发生前，命令必须先通过离线 fixture 测试验证。

扫描元数据从运行器本身生成，不从 Semgrep experimental 字段推断。输出目录默认 `artifacts/`，并由 `.gitignore` 排除。每次运行覆盖同名产物，避免把旧 finding 与新扫描混合；比较历史结果属于后续工作。

## 错误处理

- 缺少 Semgrep 可执行文件：报出安装/激活指导，不创建不完整 finding 文档。
- 规则下载、网络或配置失败：保留已写出的原始 JSON（若存在），以非零状态结束；不生成或覆盖 `findings.json`。
- 原始 JSON 不是对象，或缺少 `results`、`errors`、`paths`：归一化失败并指明缺失字段。
- 单条 finding 缺少规则 ID、路径、起止行或消息：归一化失败并指向其 JSON Pointer，避免悄悄丢失安全证据。
- 缺少可选列、代码片段或安全元数据：输出 `null` 或空对象，不视为失败。

## 测试与验收

### 离线测试

fixture 覆盖以下情况：

1. 无发现但包含合法 `results`、`errors` 和 `paths`。
2. 含完整位置、代码与 CWE 元数据的单一 finding。
3. 多个 finding，包含不区分大小写的已知严重级别与未知严重级别。
4. 缺少可选列、代码或元数据。
5. 无效 JSON、缺少顶层字段、缺少必填 finding 字段。

测试断言输出文件内容、稳定 ID、严重级别映射、JSON Pointer 与失败信息；所有测试离线运行，不调用 Semgrep Registry。

### 真实端到端验证

1. 安装计划锁定的 Semgrep CLI 版本。
2. 对本仓库运行一次扫描；不把真实扫描产物提交到 Git。
3. 确认 `semgrep-result.json` 与 `findings.json` 同时生成且可解析。
4. 记录 finding 数量、工具版本与规则集名称；不在日志或产物中写入任何凭据。
5. 确认 Git 工作树仅包含预期的源代码、fixture、测试和文档变更。

## 后续扩展边界

Bandit 与 npm audit 分别以 `normalize_bandit.py` 与 `normalize_npm_audit.py` 接入，并只能输出本设计定义的 finding 契约。新适配器不得改变 `schema_version` 为 1.0 的语义；如需要不兼容字段变更，必须新增 schema 版本和迁移策略。

## 依据

- [Semgrep 本地 CLI 文档](https://docs.semgrep.dev/category/local-and-cli-scans) 将本地扫描与 JSON/SARIF 字段作为支持入口。
- [Semgrep 官方 JSON schema](https://github.com/semgrep/semgrep-interfaces/blob/main/semgrep_output_v1.jsonschema) 将 `results`、`errors`、`paths` 定义为 CLI JSON 的必需字段，并明确要求外部使用者不要依赖 experimental 字段。
