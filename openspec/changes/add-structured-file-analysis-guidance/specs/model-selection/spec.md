# model-selection Specification

## Purpose

定义基于任务复杂度的智能模型选择机制，使系统能够在高复杂度任务中使用更强大的模型，在简单任务中使用高效模型，实现性能与成本的平衡。

本规范为未来实现提供设计框架，第一版作为可选功能（通过配置启用/禁用)。

## Requirements

### Requirement: 模型选择策略配置

系统 SHALL 支持配置化的模型选择策略,允许运维人员根据任务复杂度、成本预算和性能需求灵活调整模型分配规则。

#### Scenario: 默认配置禁用模型选择

- **GIVEN** 系统首次部署或未配置模型选择
- **WHEN** 加载配置文件 `config/model_strategy.yaml`
- **THEN** `model_selection.enabled` SHALL 默认为 `false`
- **AND** 所有任务 SHALL 使用默认模型（如 `claude-sonnet-3.5`）
- **AND** 系统行为与未引入模型选择功能前完全一致

#### Scenario: 配置复杂度-模型映射

- **GIVEN** 运维人员决定启用模型选择
- **WHEN** 编辑 `config/model_strategy.yaml`
- **THEN** 配置文件 SHALL 支持以下结构：
  ```yaml
  model_selection:
    enabled: true
    complexity_thresholds:
      simple: 0-2
      medium: 3-5
      complex: 6-10
    model_mapping:
      simple: "claude-sonnet-3.5"
      medium: "claude-sonnet-3.5"
      complex: "claude-opus-4"
    cost_aware:
      max_daily_opus_calls: 100  # 成本控制
      fallback_model: "claude-sonnet-3.5"
  ```
- **AND** 系统 SHALL 在启动时验证配置有效性（模型名称、阈值范围）

#### Scenario: 配置验证和错误处理

- **GIVEN** 配置文件包含无效的模型名称或阈值
- **WHEN** 系统加载配置
- **THEN** 系统 SHALL 记录警告日志："配置文件无效，回退到默认设置"
- **AND** 系统 SHALL 禁用模型选择功能
- **AND** 系统 SHALL NOT 因配置错误而崩溃

---

### Requirement: 基于复杂度的模型动态选择

当模型选择功能启用时，系统 SHALL 根据任务复杂度评分（来自 `file-analysis` 能力）自动选择合适的模型执行任务。

#### Scenario: 简单任务使用快速模型

- **GIVEN** 文件复杂度评分为 2 分（简单 CSV）
- **AND** 模型选择功能已启用
- **WHEN** AI 准备执行文件分析任务
- **THEN** 系统 SHALL 选择 `claude-sonnet-3.5` 模型
- **AND** 系统 SHALL 记录日志："任务复杂度: 2, 选择模型: claude-sonnet-3.5"

#### Scenario: 复杂任务使用高级模型

- **GIVEN** 文件复杂度评分为 8 分（多层表头 + 跨列结构）
- **AND** 模型选择功能已启用
- **AND** 配置文件映射 `complex` 级别到 `claude-opus-4`
- **WHEN** AI 准备执行文件分析任务
- **THEN** 系统 SHALL 选择 `claude-opus-4` 模型
- **AND** 系统 SHALL 记录日志："任务复杂度: 8, 选择模型: claude-opus-4"
- **AND** AI 使用高级模型执行阶段 2（结构识别）和阶段 4（策略制定）

#### Scenario: 模型不可用时的回退

- **GIVEN** 配置要求使用 `claude-opus-4`
- **AND** 该模型当前不可用（API 错误或配额耗尽）
- **WHEN** 系统尝试调用模型
- **THEN** 系统 SHALL 回退到 `fallback_model`（`claude-sonnet-3.5`）
- **AND** 系统 SHALL 记录警告日志："Opus-4 不可用，回退到 Sonnet-3.5"
- **AND** 系统 SHALL 向用户说明："因模型限制，使用标准模型处理复杂任务"

---

### Requirement: 分阶段模型选择

对于复杂任务，系统 SHALL 支持在不同分析阶段使用不同模型，实现精细化的成本控制。

#### Scenario: 关键阶段使用高级模型

- **GIVEN** 任务复杂度为 7 分
- **AND** 配置启用分阶段模型选择：
  ```yaml
  staged_model_selection:
    enabled: true
    stage_mapping:
      stage_1_inspection: "claude-sonnet-3.5"  # 文件初检
      stage_2_recognition: "claude-opus-4"     # 结构识别（关键）
      stage_3_diagnosis: "claude-sonnet-3.5"   # 问题诊断
      stage_4_planning: "claude-opus-4"        # 策略制定（关键）
      stage_5_execution: "claude-sonnet-3.5"   # 执行验证
  ```
- **WHEN** AI 执行 5 阶段流程
- **THEN** 阶段 2 和 4 SHALL 使用 `claude-opus-4`
- **AND** 其他阶段 SHALL 使用 `claude-sonnet-3.5`
- **AND** 系统 SHALL 记录每个阶段的模型选择决策

#### Scenario: 全流程使用统一模型（简化版）

- **GIVEN** 配置未启用分阶段模型选择（`staged_model_selection.enabled: false`）
- **WHEN** AI 执行任务
- **THEN** 所有阶段 SHALL 使用基于复杂度的统一模型（如全部用 `opus-4`）
- **AND** 配置更简单，适合初期部署

---

### Requirement: 成本控制与配额管理

系统 SHALL 支持配额限制，防止高级模型过度使用导致成本失控。

#### Scenario: 每日 Opus 调用次数限制

- **GIVEN** 配置 `max_daily_opus_calls: 100`
- **AND** 当天已使用 100 次 Opus 调用
- **WHEN** 新任务复杂度为 8 分（通常使用 Opus）
- **THEN** 系统 SHALL 使用 `fallback_model`（Sonnet）代替 Opus
- **AND** 系统 SHALL 记录日志："已达每日 Opus 配额，回退到 Sonnet"
- **AND** 系统 SHALL 向用户说明："因成本控制，使用标准模型处理"

#### Scenario: 配额重置

- **GIVEN** 当天 Opus 调用次数已达上限
- **WHEN** 跨过午夜（UTC 00:00）
- **THEN** 系统 SHALL 重置计数器为 0
- **AND** 新的一天可继续使用 Opus 模型

#### Scenario: 用户优先级覆盖配额

- **GIVEN** 高优先级用户（如付费订阅）
- **AND** 全局配额已耗尽
- **WHEN** 该用户提交复杂任务
- **THEN** 系统 MAY 为该用户保留专用配额
- **AND** 系统 SHALL 记录优先级覆盖日志

---

### Requirement: 模型性能监控与日志

系统 SHALL 记录模型选择决策和性能指标，用于后续优化和成本分析。

#### Scenario: 记录模型选择决策

- **GIVEN** 系统选择了模型执行任务
- **WHEN** 任务完成
- **THEN** 系统 SHALL 记录日志包含：
  - 任务 ID
  - 文件复杂度评分
  - 选择的模型名称
  - 复杂度等级（simple/medium/complex）
  - 是否为回退选择（fallback: true/false）
  - 时间戳
- **AND** 日志 SHALL 以结构化格式（JSON）记录便于分析

#### Scenario: 性能指标收集

- **GIVEN** 任务使用了高级模型
- **WHEN** 任务完成
- **THEN** 系统 SHALL 记录：
  - 执行时间（毫秒）
  - Token 消耗（输入/输出）
  - 任务成功/失败状态
  - 复杂度评分与实际结果是否匹配
- **AND** 数据 SHALL 存储到时序数据库或日志系统

#### Scenario: 复杂度评分准确性反馈

- **GIVEN** 任务复杂度评分为 3 分（中等）
- **AND** 任务执行失败，需要升级到高级模型重试
- **WHEN** 重试成功
- **THEN** 系统 SHALL 记录："复杂度低估，实际应为 6+ 分"
- **AND** 数据 SHALL 用于优化复杂度评分算法

---

### Requirement: 用户透明度与控制

用户 SHALL 能够了解系统使用的模型，并在需要时手动指定模型偏好。

#### Scenario: 向用户报告模型选择

- **GIVEN** 系统为复杂任务选择了 `claude-opus-4`
- **WHEN** 向用户说明分析流程
- **THEN** AI SHALL 输出："🤖 复杂度较高（8 分），将使用高级模型（Opus-4）进行深度分析"
- **AND** 用户了解为何任务可能耗时更长

#### Scenario: 用户手动指定模型偏好

- **GIVEN** 用户在请求中说明："请用最好的模型分析这个文件"
- **WHEN** 系统处理请求
- **THEN** 系统 SHALL 忽略复杂度评分
- **AND** 系统 SHALL 直接使用最高级别模型（如 `opus-4`）
- **AND** 系统 SHALL 记录："用户手动指定高级模型"

#### Scenario: 用户关闭模型选择

- **GIVEN** 用户在设置中选择"始终使用标准模型"
- **WHEN** 系统处理任务
- **THEN** 系统 SHALL 忽略模型选择配置
- **AND** 系统 SHALL 始终使用 `claude-sonnet-3.5`
- **AND** 系统 SHALL 记录用户偏好

---

### Requirement: LangGraph 集成（技术实现）

系统 SHALL 设计模型选择逻辑与 LangGraph 工作流集成，支持条件子图和模型切换。

#### Scenario: 条件子图模型切换

- **GIVEN** LangGraph 支持条件分支和子图配置
- **WHEN** 任务复杂度 ≥6
- **THEN** 工作流 SHALL 路由到"高级分析子图"
- **AND** 该子图 SHALL 配置使用 `claude-opus-4`
- **AND** 其他子图继续使用默认模型

#### Scenario: 单一工作流内模型切换

- **GIVEN** LangGraph 节点支持动态配置 LLM
- **WHEN** 执行到阶段 2（结构识别）节点
- **THEN** 系统 SHALL 动态设置该节点的模型为 `opus-4`
- **AND** 后续节点恢复使用默认模型

#### Scenario: LangGraph 不支持动态模型时的降级方案

- **GIVEN** LangGraph 当前版本不支持动态模型切换
- **WHEN** 系统启动
- **THEN** 系统 SHALL 在 prompt 中添加元指令："如果任务复杂度 ≥6，建议使用更严格的验证步骤"
- **AND** 系统 SHALL 记录日志："模型选择功能受限于 LangGraph 版本"
- **AND** 配置文件 SHALL 包含 `langgraph_compatible: false` 标志

---

### Requirement: 向后兼容性与渐进式启用

模型选择功能 SHALL 作为可选增强，不影响现有系统行为，支持渐进式启用和回滚。

#### Scenario: 默认禁用不影响现有功能

- **GIVEN** 系统升级包含模型选择功能
- **AND** 配置文件未显式启用该功能
- **WHEN** 用户提交任务
- **THEN** 系统行为 SHALL 与升级前完全一致
- **AND** 所有任务使用默认模型
- **AND** 日志无模型选择相关记录

#### Scenario: 灰度发布支持

- **GIVEN** 运维人员希望逐步测试模型选择功能
- **WHEN** 配置灰度规则：
  ```yaml
  model_selection:
    enabled: true
    rollout_percentage: 10  # 仅 10% 任务启用
  ```
- **THEN** 系统 SHALL 随机选择 10% 的任务启用模型选择
- **AND** 其他 90% 任务继续使用默认模型
- **AND** 系统 SHALL 记录 A/B 测试数据

#### Scenario: 快速回滚机制

- **GIVEN** 模型选择功能上线后发现问题
- **WHEN** 运维人员设置 `model_selection.enabled: false`
- **THEN** 系统 SHALL 立即停止使用模型选择逻辑
- **AND** 所有正在执行的任务完成后切换
- **AND** 新任务立即使用默认模型

---

### Requirement: 测试与验证

模型选择功能 SHALL 包含全面的测试，确保正确性和稳定性。

#### Scenario: 单元测试覆盖

- **GIVEN** 开发完成模型选择逻辑
- **WHEN** 运行单元测试
- **THEN** 测试 SHALL 覆盖：
  - 复杂度评分 → 模型映射逻辑
  - 配额限制和回退逻辑
  - 配置文件解析和验证
  - 日志记录功能
- **AND** 测试覆盖率 SHALL ≥80%

#### Scenario: 集成测试验证

- **GIVEN** 系统启用模型选择
- **WHEN** 运行集成测试
- **THEN** 测试 SHALL 验证：
  - 简单任务（评分 ≤2）使用快速模型且成功
  - 复杂任务（评分 ≥6）使用高级模型且成功
  - 配额耗尽时正确回退
  - 日志记录完整和准确
- **AND** 测试 SHALL 使用真实文件（lego.xlsx、telco.csv）

#### Scenario: 性能回归测试

- **GIVEN** 引入模型选择功能
- **WHEN** 对比升级前后性能
- **THEN** 简单任务（低复杂度）处理时间 SHALL NOT 增加 >5%
- **AND** 复杂任务（高复杂度）成功率 SHALL 提升 ≥20%
- **AND** 整体成本（Token 消耗）SHALL 在可控范围内
