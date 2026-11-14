# 跨Agent安装与首次使用

本项目提供同一个通用Agent Skill，以及WorkBuddy展示字段适配包。题库、规则、下载和PDF代码相同；不为每个模型复制维护实现。

## 给老师的最短路径

下载通用技能ZIP并交给Agent，要求“请阅读包里的SKILL.md，帮我安装并用内置题库出作业”。有平台导入功能时使用导入；没有时由Agent把完整physics-homework文件夹安装到对应技能位置。不要只复制SKILL.md，scripts、references和resources必须一起保留。不要求老师找题库、配Python或填写API Key。

如果Agent不能访问附件中的文件，请让老师选择解压后的文件夹或授予宿主正常文件访问权限；不要假装看到了文件。只有当前环境缺少必要能力时才说明阻碍。

## Codex本地技能

按当前官方文档，用户级位置为~/.agents/skills/physics-homework/，项目级位置为<项目>/.agents/skills/physics-homework/。已有Codex技能安装工具时优先使用其原生安装机制，并遵从该版本实际目录。完整文件夹就位后在下一轮或新会话检查技能是否被识别；不要靠文件复制成功宣称宿主已加载。

可以指定$physics-homework触发，也可自然语言请求。未识别时可先明确读取实际SKILL.md，再执行流程；这属于本轮显式使用，不冒充已完成持久安装。

官方说明：https://developers.openai.com/codex/skills/ 。不同版本的安装器可能使用兼容目录，以实际安装器和技能列表为准。

## Claude Code本地技能

用户级位置为~/.claude/skills/physics-homework/，项目级为<项目>/.claude/skills/physics-homework/。安装后检查/physics-homework是否可用，必要时开启新会话。可自然语言调用，或使用/physics-homework加作业要求。

这里的Claude指可执行本地工具的Claude Code。Claude网页聊天、Cowork、云端会话具有不同的技能加载和运行限制，不能因名称相同而声称已兼容。必须单独核对当前宿主是否能加载全部资源并执行、下载和查看结果。

官方说明：https://code.claude.com/docs/en/skills 。

## WorkBuddy

优先使用单独生成的workbuddy.zip，通过当前客户端提供的本地技能导入功能安装；包中保留其展示字段，核心实现相同。导入后核对技能可见，再实际调用。不把文档兼容与打包通过当作客户端已经验收。

## 其他Agent

能读取标准SKILL.md的宿主，按自己的技能安装机制加载完整目录。没有原生技能发现机制，但能访问本机文件和工具的Agent，可以由用户明确指示读取SKILL.md来执行本次任务；这不等于所有Agent都能自动发现技能。

能力要求：文件读写、命令执行、联网取题、完整题答图片阅读、PDF渲染页检查。能力不足应指出缺项。纯文本模型、无法执行脚本的聊天界面，不能仅凭上传ZIP完成本流程。

## 所有宿主共用的运行方式

定位实际技能目录；Mac/Linux用bash <实际技能目录>/scripts/run.sh，Windows用PowerShell执行scripts/run.ps1。首次先info --course 9702或0625，自动建立独立环境和内置索引；随后search、完整题答阅读、export和qa。完整参数与教学规则见SKILL.md。

自动准备不会修改系统Python或shell配置；平台模型费用与权限按宿主设置。题库默认缓存到~/codex/physics-homework，PHYSICS_HOME可指定其他本机位置。多个Agent在同一系统用户下会共享此默认缓存与已用题记录；需要分开班级/试用时由Agent设定独立PHYSICS_HOME，不要求老师手填。

安装时如果目标目录已存在，先核对版本及是否有用户改动，不能盲目覆盖或删除；更新应保留工作目录中的缓存、选题记录与已导出的作业。
