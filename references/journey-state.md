# 账本与恢复协议

## 保存边界
默认账本保存在对话，以紧凑摘要持续维护；不自动创建项目文件。用户明确要求保存时才写入指定位置。出生数据只用于当前规划，不写入可复用 Skill 或共享示例。
脚本读取 JSON / 标准输入，不自动写文件，不调用工程或外部应用。

## 账本结构
- goal: id、版本、用户目标原文、联合条件关系、成功指标与口径、约束。
- birth: 原始输入、规范化时间候选、排盘口径与计算版本；隐私信息不必每轮重印。
- conditions: id、目标关联、kind(controlled/resource/external)、必要性理由。
- facts: 已有事实及来源，与计划产出分开。
- nodes: id、parent、展示时固定的 options、selected、组合兼容关系、状态前后差异、条件影响、卦象输入输出、解释、action_ids（本次决策当时登记的行动ID）。
- active_path: 从根开始的节点 ID，归档分支另存。
- actions: id、source_node、covers(条件ID列表)、depends_on(行动ID列表)、任务/交付物/验收/资源；不能由终局临时发明。
- unresolved_decisions、resource_conflicts、assumptions。
- external_checks: condition_id、metric、checkpoint、fallback。
- planning_status 与 actual_goal_status 独立；未有现实证据时 actual_goal_status 为 unverified。

JSON 机器审核接口见 scripts/journey_engine.py 的 audit；它检查结构性缺口，不能证明文字中的行动确实足以达标，仍需语义审核。

## 恢复
优先恢复目标版本、出生口径、有效路径及各节点选项映射，再从脚本重放卦象，检查最新缺口。
没有账本或算法记录就标注不能精确重放，向用户补问缺失节点，不重建“看似合理”的历史。
不要重复已回答的问题。历史旧版 MD5 结果不能混入新版起卦：注明迁移版本；旧选项未固定数码时需确认映射后重放，不声称可无损恢复。

## 回退与修订
保留旧节点及后代，标为 archived；从改选父节点建立新节点 ID。
active_path 切换至新分支，不删除历史、不沿用旧后代的有效性。
出生纠正会重算同一路径全部卦象，但事实与已选行动不自动撤销；重新审查受解释影响的决定。
目标变更必须用户明确同意，升目标版本并重算目标条件。卦象基础不含目标文字，改目标文字不会随机换卦。

## 终局机器审核输入
示意字段：
goal={id, criteria:[{id,kind}]}；
nodes=[{id,parent,selected:[1],options:[1,2,3,4,5],
hexagram:{...脚本结果...},state_before:{...},state_after:{...},
interpretation:"具体影响", gaps:[...],next_options:[...],action_ids:[...]}]；
active_path=[...]；
actions=[{id,source_node,covers:[...],depends_on:[],task,deliverable,acceptance,resources}]；
external_checks=[{condition_id,metric,checkpoint,fallback}]；
unresolved_decisions=[]；resource_conflicts=[]。
重复、未知ID、未选来源、断裂父路径、循环依赖、缺行动字段与外部检查都阻止 closed。
action_ids 必须在决策当时冻结；终局新增行动无法仅靠填一个旧 source_node 通过审查。机器审核只能核对现有记录，禁止为通过审核而倒填历史，仍需核对当时选择的文字语义。
gaps 是该节点的完整剩余条件视图，终节点必须为空；新问题需先登记条件。

