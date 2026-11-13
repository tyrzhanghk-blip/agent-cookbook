# 案例18：批量数据转换管道（Transform Pipeline）

## 学什么
Agent 在真实生产里最常见的形态不是聊天机器人，而是**数据转换引擎**（ETL 里的 T）：
把一批非结构化的杂乱文本，批量转换成严格 schema 的结构化记录。

本案例把 20 条模拟客服工单（口语化、缺字段、中英混杂、甚至纯灌水）转换成规范的
`TicketRecord`：分类、情感、订单号、紧急度、诉求摘要。

管道流程：

```
sample_data.json -> 逐条转换(Agent+output_type) -> pydantic校验
                  -> 失败重试1次 -> 仍失败则隔离 -> transformed.json + failed.json + 汇总报告
```

## 与前面案例的关系
| 能力 | 来自 | 在这里的用法 |
|---|---|---|
| 结构化输出 | 案例3 | `output_type=TicketRecord`，单条任务简单，单 Agent 即可稳定工作 |
| 重试 | 案例14 | 外层兜底重试 1 次（SDK 对 schema 校验失败也会自动重试） |
| 校验 | 案例15 | pydantic 管字段合法，另有语义规则（"无效内容"识别） |
| Agent 即函数 | —— | 每条记录就是一次纯函数调用：文本进、结构化出，无对话状态 |

## 工程重点：批量场景的"质量不齐"
- **部分成功策略**：一条坏数据不能卡死整批——失败记录隔离到 `failed.json`（人工待办），
  成功的照常产出。最后必须有完整的账：成功率、分类分布、失败清单。
- **无意义内容**：像"哈哈哈"这种，与其让模型硬编字段，不如在 schema 里给它
  合法的出口（summary=「无效内容」），把"识别垃圾"和"转换失败"区分开。
- **不编造**：instructions 里明确"原文提到订单号才填"——批量转换里编造字段的
  危害远大于缺失。

## 踩过的坑：枚举值要用模型能精确输出的写法
最初 Category 的枚举值是中文带斜杠（如 `"退换货/退款"`），结果 20 条全部被分类成
「其他」且每条耗时 6 分钟——因为模型输出很难和这种值逐字匹配，pydantic 校验失败后
SDK 内部反复重试，模型被错误信息越带越偏。修复：枚举值改成简单英文
（logistics/refund/...），含义写进 instructions，展示时映射回中文。教训：
**output_type 里要求模型"逐字复述"的字段，取值越简单越好**。

另一个小坑：`model_dump()` 默认保留 enum 对象，统计时会打印 `Category.other`
而不是中文——要用 `model_dump(mode="json")`。

## 怎么运行
```bash
uv run python cases/case18_data_transform/main.py        # 全量 20 条
uv run python cases/case18_data_transform/main.py 5      # 只处理前 5 条（调试用）
```

## 预期输出
每条工单一行进度（分类/情感/紧急度），最后是汇总报告：总数/成功/失败/耗时、
分类分布、负面占比、高紧急工单清单、失败明细。
产物 `transformed.json` 和 `failed.json` 落在本案例目录（已 gitignore）。

## 扩展练习
- 把逐条 `run_sync` 改成 `asyncio.gather` 并发转换，对比耗时（注意案例16的 event loop 教训）
- 给管道加"抽样人工复核"：随机抽 3 条转换结果打印原文对照，估算质量
- 把 `failed.json` 接到案例12的人工审批流程里