# 一张板书 / 一句话，生成物理作业

**面向Codex、Claude Code、WorkBuddy等Agent的通用物理作业技能。老师安装技能后，直接选择课程、发板书或说出要求，获取学生卷和答案卷。默认不需要自备题库、建库、填写资料路径或API Key。**

内置题库入口：9702物理4330题，0625物理2256题，共6586题。完整索引随技能安装；题目和答案从作者现有公开题库站点按需校验、缓存。首次需联网准备环境和素材，不必先下载整套大题库。

## 老师怎么用

1. 下载通用技能安装包，交给Codex、Claude Code或其他支持文件、执行和视觉阅读的Agent安装；WorkBuddy也提供专用导入包。
2. 说明课程并发送板书，或直接说“9702 A2圆周运动，3道中等结构题，不考引力”。
3. Agent自动准备环境与候选素材，查看完整题目/答案，按已教范围筛题，输出两份PDF供老师复核。

0625示例：“0625 Extended速度—时间图，6道选择题和2道结构题，排除能量。”普通老师不需要操作终端或理解内部文件结构。系统或宿主的正常授权提示仍须本人确认。

## 安装到不同Agent

通用分发文件为physics-homework-<版本>-agent-skill.zip，包含完整physics-homework目录。让Agent阅读包中SKILL.md并代为安装；老师无需操作终端。它是一份通用技能，由不同宿主各自加载，同一题库与规则不会随平台改变。

| 入口 | 安装与使用 |
| --- | --- |
| Codex | 使用技能安装工具，或由Agent安装到支持的技能位置；可用$physics-homework触发 |
| Claude Code | 由Agent安装到个人/项目技能目录；可用/physics-homework触发 |
| WorkBuddy | 使用附带展示字段的workbuddy.zip导入 |
| 其他Agent | 支持标准Skill时安装完整目录，否则明确读取SKILL.md后执行；需要相同工具能力 |

详细目录、官方来源、识别检查和更新规则见[跨Agent安装说明](skill/physics-homework/references/agent-installation.md)。仅支持聊天或不允许运行程序的界面无法完成本地出卷；Claude网页聊天与Claude Code不能直接视为同一个环境。兼容格式不等于各客户端已完成实测。

## 包内有什么

- 两门课的题库索引、出处、Topic/子知识点、难度与图片完整性标记。
- 自动首次准备入口及按需题目/答案缓存。
- 板书与一句话选题规则、课程分流、去重、配对PDF输出及检查流程。
- 可选的原创演示，以及接入其他授权题库的高级工具。

包内没有整套真题图片和官方答案文件；它们在首次需要时从已有公开来源获取。代码与原创规则按MIT开放；第三方考试材料不因本项目而成为MIT材料，不承诺脱离网络后能使用尚未缓存的题目。

## 当前范围

9702索引含AS Paper1/2、A2 Paper4及实验Paper3/5。0625当前内置素材为Extended Paper2/4；Core与实验题的分流规则存在，但没有相应内置素材时会说明不支持，不混入Extended题冒充。课程参考分别为2025–2027和2026–2028。

已在Mac空白工作目录中自动下载独立Python、安装依赖、初始化两门课程并生成真实素材作业/答案，未预置资料或手动绑定题库。WorkBuddy真实宿主安装与调用仍待测试；Windows入口已提供，独立Windows实机仍需测试。板书理解和语义筛题依赖宿主模型，不是脚本自带视觉模型，不承诺零错误。平台模型与积分消耗按宿主规则。

## 开发与打包

通用Agent使用 `skill/physics-homework/SKILL.md`，默认生成通用技能包；WorkBuddy只额外适配导入展示字段：

```bash
python tools/package_skill.py --output /本机目录/physics-homework-agent-skill.zip
python tools/package_skill.py --platform workbuddy --output /本机目录/physics-homework-workbuddy.zip
```

安装包包含索引，首次运行通过官方uv工具在专用工作目录准备独立Python和依赖，不改变系统Python或shell配置。资料默认缓存到当前用户的~/codex/physics-homework，不写iCloud。可通过PHYSICS_HOME指定独立测试目录。

开发验证：`python -m unittest discover -s tests -v`。高级自有题库绑定参见[首次建库说明](skill/physics-homework/references/first-bank.md)，它不是小白用户的前置要求。原创演示由examples/create_demo.py生成，不能称为官方真题。

## 开源与培训

代码、原创规则和本项目自有元数据工作流采用[MIT](LICENSE)，允许使用、修改和商用，保留许可声明。考试材料按其原有权利和来源条件使用。项目独立开发，与Cambridge International无隶属或背书关系。

免费自助工具可作为教师体验入口；实操培训、资料适配和学校实施服务可单独提供，不强制购买培训、关注或加群才能使用。历史Release附件和私人完整题库迁移包不由本次MIT代码许可自动重新许可。

错误反馈请提供课程、系统和已脱敏复现步骤，不公开学生答卷或凭据。
