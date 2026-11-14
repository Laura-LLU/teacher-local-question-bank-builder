# 一张板书 / 一句话，生成物理作业

面向教师的开放工作流：首次绑定有权使用的本地题库后，发板书图或说出章节、难度和题量，由具备本地执行与视觉阅读能力的Agent筛题、配答案、生成独立学生卷和答案卷。

首版支持 **Cambridge 9702 AS & A Level Physics** 与 **0625 IGCSE Physics**。代码与原创教学规则采用MIT许可；公开包不含Cambridge试卷、官方答案、真题截图、用户索引或学生资料。教师可免费自助使用；培训、资料适配和实施服务可另外提供，不作为工具使用的前提。

## 可以做什么

- 从板书判断已经教授的知识边界，排除已讲例题。
- 按一句话要求筛选本地题目，复核完整题目和对应答案。
- 区分9702的AS/A2/Paper3/Paper5与0625的Core/Extended/Paper5/Paper6。
- 输出学生卷、答案卷和可追溯选题记录。
- 用户可修改规则、适配自己的资料，并检查每一步。

这是Early Preview。板书阅读和语义筛题由宿主Agent完成，脚本不自带视觉模型；不是普通网页聊天机器人独立运行的软件。WorkBuddy/Codex等平台的文件处理和模型费用依各自设置；本工具不额外索要API Key，不承诺完全离线或零错误。

## 先跑原创演示

需要Python3.10+。在项目目录建立独立环境并安装requirements.txt，然后执行：

```bash
python examples/create_demo.py --output /你的本机目录/physics-homework-demo
python skill/physics-homework/scripts/homework.py --workspace /你的本机目录/physics-homework-work prepare --course 9702 --source-root /你的本机目录/physics-homework-demo/9702
python skill/physics-homework/scripts/homework.py --workspace /你的本机目录/physics-homework-work search --course 9702 --level AS
```

示例为作者新编题目，只验证安装、课程分流与PDF输出，不是Cambridge真题或官方评分方案。0625原创演示同理使用--course 0625、--level Extended。

## 在Agent里使用

将 `skill/physics-homework` 按宿主支持的方式安装为技能，或把整个项目目录提供给Agent。标准SKILL.md适用于通用Agent；WorkBuddy导入包由 `python tools/package_skill.py --platform workbuddy --output <新ZIP路径>` 生成，会自动加入其所需展示字段。WorkBuddy可本地导入该技能ZIP；不要把资料库上传到开放平台发布页。

第一次说明课程及授权资料路径，让Agent阅读Skill并完成题库绑定；原始PDF资料先建立可核验的小样本。后续可以直接说：

> 9702 A2圆周运动，3道中等结构题，不考引力。

> 0625 Extended速度—时间图，6道选择题和2道结构题，排除能量。

或发送板书图并指出课程。详细首次建库流程见 [first-bank.md](skill/physics-homework/references/first-bank.md)。默认工作目录为当前用户的~/codex/physics-homework，资料文件只读，索引和成品留在工作目录。

## 已有本地题库

适配已有9702/0625索引与标准catalog.json，不重新改写分类或复制整套资料；仅把当前可用题目的引用写入本机工作索引。标签不是逐题语义准确保证，完整题和答案仍须核验。只拥有Extended题库时不会自动获得Core题，缺少相应题目就报告不足。

## 开放范围与历史版本

本目录新增/整理的代码、原创规则和原创演示采用 [MIT](LICENSE)，允许使用、修改和商用，须保留许可声明。第三方考试材料不属于该许可；用户须有权用于相应处理方式。项目独立开发，与Cambridge International无隶属或背书关系。

本版本改变的是当前代码开放许可和双课程“板书到作业”定位；不自动重新许可历史Release附件，也不把私用含题库迁移包变为公共下载。旧版受限许可与历史说明不作为当前新代码的限制。

## 验收与参与

运行 `python -m unittest discover -s tests -v` 检查课程隔离、题型、路径和输出等机械约束。真实板书、不同系统与不同Agent的教学质量需要教师实测。反馈请包含课程、系统、复现步骤和已脱敏截图；不要公开学生答卷、凭据或无权分发的材料。
