<div align="center">

<img src="docs/assets/hero-main.png" alt="Multi-Round Journey：从易经起卦到可审计因果路径" width="100%">

# Multi-Round Journey

**因果论逐步推导助手 · 固定终点，开放路径**

[![Version](https://img.shields.io/badge/version-2.0.0-7c3aed)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](scripts/journey_engine.py)
[![Tests](https://github.com/LyonLyu0229/multi-round-journey/actions/workflows/test.yml/badge.svg)](https://github.com/LyonLyu0229/multi-round-journey/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-MIT-0f172a)](LICENSE)

一个以生辰排盘和易经起卦为入口、以可审计因果链为骨架的 Codex Skill。它不会在开场就替你决定完整路线，而是围绕唯一目标，逐轮把选择转化为新状态、缺口与下一组真实分支。

[三分钟上手](#三分钟上手) · [工作方式](#它如何工作) · [实用案例](#可以用来做什么) · [确定性引擎](#确定性计算引擎) · [完整案例](examples/game-journey.md) · [贡献指南](CONTRIBUTING.md)

</div>

> [!IMPORTANT]
> 本项目是规划与决策辅助工具。卦象用于传统象征解释和分支设计，不构成科学预测、收益承诺、医疗/法律/投资意见，也不能替代现实验证。

## 为什么做这个 Skill

常见的“规划助手”有两个问题：一是过早给出整套答案，忽略用户尚未做出的决定；二是把计划完成误写成现实成功。Multi-Round Journey 将两者分开：

- **终点固定，路径开放**：目标契约保持稳定，路线由每轮选择逐步确定。
- **每选一次，状态就变一次**：正式选择之后必须重算卦象、更新因果状态和目标缺口。
- **规划闭合 ≠ 现实达标**：`planning_status` 与 `actual_goal_status` 独立记录。
- **可回放、可审计**：路径编码、冻结选项、行动来源与依赖关系都能追溯。
- **默认不越界执行**：提供路径或账号不代表授权检查工程、发布、购买或代操作。

## 它如何工作

<img src="docs/assets/journey-branches.png" alt="目标固定、路径逐轮分支并持续重算" width="100%">

```mermaid
flowchart LR
    A[出生信息与项目现状] --> B[确定性排盘与初始卦]
    B --> C[锁定唯一目标契约]
    C --> D[展示当前分支]
    D --> E[用户作出正式选择]
    E --> F[重算本卦・动爻・变卦]
    F --> G[行动 → 直接变化 → 后续影响 → 新状态]
    G --> H[更新条件覆盖、冲突与验证点]
    H --> I{逻辑闭合?}
    I -- 否 --> D
    I -- 是 --> J[汇编已选路径与现实验证方案]
```

每轮固定完成六件事：选择确认、卦象重算、因果状态更新、目标缺口检查、下一轮分支生成、路径摘要。详见 [`SKILL.md`](SKILL.md)。

## 三分钟上手

### 1. 安装 Skill

将本仓库克隆或下载到你的 Codex Skills 目录：

```powershell
git clone https://github.com/LyonLyu0229/multi-round-journey.git "$env:USERPROFILE\.codex\skills\multi-round-journey"
```

重启或刷新 Codex 后，通过 `$multi-round-journey` 调用。

```text
使用 $multi-round-journey，从生辰起卦开始，锁定我的项目目标，
逐轮推导选择与结果，最终汇成完整工作流程。
```
### 2. 准备最少信息

首次使用不必写长篇需求，只要提供：

- **项目现状**：现在做到哪里，已经有什么资源。
- **唯一目标**：最终想达到什么，怎样才算完成。
- **现实边界**：时间、预算、每周投入、不能接受的事情。
- **起卦信息**：公历或农历出生日期、时间或时间范围、出生城市和时区。

可直接复制下面这段：

```text
使用 $multi-round-journey，只做规划，不替我执行项目。
我的项目是：[项目与当前状态]
唯一目标是：[目标与验收标准]
时间/预算/每周投入：[现实边界]
出生信息：[公历或农历、年月日、时间、城市、时区]
请先确认目标契约，再给我第一轮分支；我每选择一次，你都重算卦象、
更新因果状态和目标缺口，不要一开始就替我决定整条路线。
```

### 3. 像做选择题一样推进

```text
你：我选择 D＋E，可以组合。

Skill：确认选择 → 重算本卦/动爻/变卦 → 说明这个选择造成的直接变化
→ 更新尚未解决的条件 → 给出下一轮 5—10 个真实分支。

你：这一轮改选 B。

Skill：保留旧路径用于审计，从 B 建立新分支并重新推导，不偷偷继承旧路线。
```

> 想先看一份完整演示？阅读 [快速案例集](examples/quick-start.md) 或 [旅行游戏多轮案例](examples/game-journey.md)。

### 4. 运行测试

仓库已经内置所需的固定版本日历与时区数据，可直接离线测试：

```powershell
python -X utf8 -B -m unittest discover -s tests -q
```

预期结果：`Ran 28 tests`、`OK`。

## 可以用来做什么

| 场景 | 你提供 | 它逐轮解决 | 最终得到 |
|---|---|---|---|
| 独立游戏上线 | 当前 Demo、预算、上线目标 | 样板、玩法、商店页、测试、宣发之间的先后与资源冲突 | 可回放的制作与验证流程 |
| 内容账号增长 | 定位、已有内容、目标受众 | 选题、形式、频率、渠道与数据复盘节点 | 内容实验路线和未达标分支 |
| 商业/旅行项目 | 资源、时间窗口、收入或体验目标 | 方案组合、成本边界、依赖条件和风险检查点 | 分阶段行动计划与现实验证表 |

这些案例中的“完成”是**规划结构闭合**，不是销量、收入或增长已经发生。完整的输入、对话和输出示意见 [examples/quick-start.md](examples/quick-start.md)。

## 确定性计算引擎

[`scripts/journey_engine.py`](scripts/journey_engine.py) 负责三类只读计算：

| 命令 | 用途 | 输入 |
|---|---|---|
| `chart` | 公历/农历排盘、出生数与初始卦 | JSON |
| `hex` | 根据出生数和累计有效路径重算卦象 | 命令行参数 |
| `audit` | 检查目标、节点、行动、依赖和外部验证是否结构闭合 | 账本 JSON |

排盘示例：

```powershell
python -X utf8 -B scripts/journey_engine.py chart --json `
  '{"calendar":"solar","year":1990,"month":1,"day":1,"time":"12:00:00","birthplace":"Shanghai","timezone":"Asia/Shanghai"}'
```

路径重算示例：

```powershell
python -X utf8 -B scripts/journey_engine.py hex --base 28 --hour 7 --path '[[4,5],[2]]'
```

`[[4,5]]` 表示同一轮的兼容组合，`[[4],[5]]` 表示先后两轮选择；两者编码不同、推导状态也不同。

## 设计边界

<img src="docs/assets/audit-reality.png" alt="计划闭合与现实验证分离" width="100%">

| 本项目会做 | 本项目不会做 |
|---|---|
| 逐轮生成差异明确的分支 | 用同义词凑足选项数量 |
| 公开计算口径和必要摘要 | 让语言模型凭感觉“猜卦” |
| 区分事实、计划和待验证项 | 把计划写成已经发生的结果 |
| 为外部指标设置检查点和未达标分支 | 承诺销量、收入或成功概率 |
| 在目标不变时允许回退与改选 | 偷偷降低、替换或遗漏子目标 |

## 仓库结构

```text
multi-round-journey/
├─ SKILL.md                    # Skill 入口与核心契约
├─ agents/openai.yaml          # 展示名、简介与默认提示词
├─ scripts/
│  ├─ journey_engine.py        # 确定性排盘、路径卦象与账本审计
│  └─ vendor/                  # 固定版本日历和时区依赖
├─ references/                 # 算法、因果逻辑、账本与交付模板
├─ examples/
│  ├─ quick-start.md           # 三个简单使用案例
│  └─ game-journey.md          # 完整多轮案例
└─ tests/test_engine.py        # 28 项回归测试
```

## 算法与审计要点

- 支持公历、农历、闰月、节气边界、历史 DST、重复/不存在的本地时间与不确定出生时段。
- 使用 IANA 时区；不会擅自进行真太阳时修正。
- 使用固定文王卦序映射，并按自下而上的动爻翻转得到变卦。
- 账本追踪冻结选项、有效路径、行动来源、条件覆盖、依赖环、资源冲突和外部验证。
- 结构检查通过后仍返回 `actual_goal_status: unverified`，直到现实证据真正存在。

更详细的口径见 [`references/algorithm-prediction.md`](references/algorithm-prediction.md) 与 [`references/journey-state.md`](references/journey-state.md)。

## 版本与路线

当前版本为 **v2.0.0**。变更记录见 [`CHANGELOG.md`](CHANGELOG.md)。欢迎提交更多边界样例、脱敏旅程案例、账本语义检查和文档改进。

## 开源与致谢

项目主体以 [MIT License](LICENSE) 发布。仓库内固定版本依赖保持各自许可证，详见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。


