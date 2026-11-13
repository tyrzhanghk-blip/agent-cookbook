# 案例19：Agent Skills —— 领域知识按需加载

## 学什么
前面案例的知识都写在 instructions 里（案例1 还讲了动态注入），但当领域知识越积越多
（退款政策、物流 SOP、VIP 规范、合规红线……），全量塞进 instructions 有三个问题：

1. **浪费 token**：每轮对话都带着全部 SOP，哪怕这次只问"卖不卖手机"
2. **稀释注意力**：模型在一堆无关文档里找重点，回答质量下降
3. **难以维护**：业务方改一条政策，得动 Agent 代码、重新部署

解法就是 **Skill 机制**（Claude Code 的 Skills、Cursor 的 Rules 都是同一思想）：

```
skills/
├── refund_policy/SKILL.md        # 每个领域一个目录
├── logistics_escalation/SKILL.md
└── vip_service/SKILL.md
```

每个 SKILL.md 带 frontmatter（name + description），Agent 只内置两个工具：
- `list_skills()`：列出技能索引（name + 一句话描述）——**便宜**，模型先看这个
- `read_skill(name)`：加载某个技能的完整 SOP ——**贵**，只在需要时发生

instructions 里只写"路由规则"（遇到什么问题读什么技能），不写知识本身。

## 与案例1（动态 instructions）的区别
案例1 的动态注入是"代码决定给模型看什么"（服务端逻辑）；Skill 是"模型自己决定
读什么"（Agent 用工具按需拉取）。前者适合确定性强的场景，后者适合"无法预知
这次会用到哪些知识"的开放对话。

## 怎么运行
```bash
uv run python cases/case19_agent_skills/main.py
```

## 预期效果
- 第1轮（卖手机吗）：不调用任何技能工具
- 第2轮（8000元退款）：list_skills -> read_skill(refund_policy)，并按 SOP 回答——
  注意 8000 > 5000，按技能文档不能承诺到账时间，应回复"升级至专属通道"
- 第3轮（VIP 权益）：read_skill(vip_service)
- 第4轮（签收未收到）：read_skill(logistics_escalation)，按 P1 流程处理

每一步工具调用会打印 `[工具] list_skills` / `[工具] read_skill(...)`，能清楚看到
"技能只在需要时才被加载"。

## 插件版：openai-agents-skills 扩展
除了 `main.py`（手写版，理解机制），本案例还有 `plugin.py`——用社区扩展
[`openai-agents-skills`](https://github.com/damianoneill/openai-agents-skills) 实现同样的效果：

| | 手写版 main.py | 插件版 plugin.py |
|---|---|---|
| 加载时机 | Agent 调 `read_skill` 工具**拉取**（消耗一次工具调用轮次） | `SkillHooks` 在每次模型调用前**注入**命中技能 |
| 路由决策 | 模型自己看 `list_skills` 索引决定读哪个 | `LLMSkillRouter` 用一次轻量模型调用决定注入哪些 |
| 技能名约束 | 无 | 只允许小写字母/数字/连字符（下划线会被静默拒绝） |
| 依赖 | 仅 SDK | 额外安装 `openai-agents-skills` |

两者共用 `skills/` 目录（`<name>/SKILL.md` 格式一致）。

### 插件版踩过的坑
1. **技能名不能带下划线**：`refund_policy` 会被静默判定无效（仅 stderr 提示），技能名要用 `refund-policy` 这种连字符风格
2. **`LLMSkillRouter(model=...)` 要传 Model 实例**：传模型名字符串会静默失败（路由器直接返回空，模型只能看到技能清单看不到 SOP 正文，表现为回答里说"未加载到文档"）——构造 `OpenAIChatCompletionsModel` 时还必须显式传 `openai_client`（它不会用 `set_default_openai_client` 设置的全局默认）
3. **asyncio.run 里不能调 `Runner.run_sync`**：会报 "cannot be called when an event loop is already running"，要改 `await Runner.run(...)`

## 扩展练习
- 把 skills 目录的内容换成自己业务领域的 SOP，立刻就是一个知识路由客服
- 加"技能缓存"：同一会话读过就不再读（对比 token 消耗）
- 让 read_skill 支持关键词模糊匹配，或按 description 做 embedding 检索（案例：RAG 的雏形）