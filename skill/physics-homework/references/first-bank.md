# 高级功能：接入自己的题库

普通老师无需阅读本文件。默认内置9702与0625的完整检索索引，题目和答案自动从现有公开题库按需缓存。只有用户主动要求接入其他资料，或内置范围不覆盖且用户愿意补充资料时，才使用下列步骤。

公开安装包不包含整套Cambridge题图与官方答案裁图。高级接入时由教师提供有权处理的本地资料。先确认9702/0625等课程代码，不从“电学”“运动”等重叠知识点猜课程（本项目仅支持9702和0625）。

## 已有题库

CLI `prepare --course <9702或0625> --source-root <题库根目录>` 支持本项目既有9702/0625本地数据结构，以及标准 `catalog.json` 题库。题库只读；工作索引写到workspace，不移动原素材。默认workspace为当前用户 `~/codex/physics-homework`，可通过CLI的 `--workspace` 指定本机位置。info查看课程、题量及组件覆盖；没有Core题时如实说明，不把Extended卷冒充Core。

## 只有QP/MS PDF

由具备本地PDF/图像阅读能力的Agent执行：核对科目、考季、年份、组件及题号；先为本次作业所需候选题建立小样本，不因一次作业强迫老师等待整库分类。若要长期建库，先做20–50道黄金样本由老师复核，再扩展全库。

读取完整题及跨页小问和官方答案，给每题记录课程、组件、主题、子知识点、难度及依据、已知分值、来源。所有保留部分须独立可答。写JSON裁剪清单：

```json
{
  "course":"0625",
  "reviewed":true,
  "questions":[{
    "id":"my-reviewed-question",
    "paper":"4",
    "topics":["1 Motion, forces and energy"],
    "subtopics":["1.2 Motion"],
    "difficulty":"medium",
    "difficulty_reason":"填写阅读完整题后的具体判断依据",
    "marks":null,
    "source_ref":"填写已核对的原卷代码与题号",
    "question_pages":[{"pdf":"papers/question.pdf","page":0,"crop":[0.04,0.2,0.96,0.9]}],
    "answer_pages":[{"pdf":"papers/answer.pdf","page":0,"crop":[0.04,0.4,0.96,0.9]}]
  }]
}
```

这只是格式示例，不代表真实题号、题目、答案或已核对状态。页码从0开始，crop是左下原点 `[left,bottom,right,top]`，在0–1之间；跨页按顺序多写一项。坐标须由实际查看页面决定，禁止盲用示例坐标。原题号、分值、图表、选项与版权标识不得误裁。执行：

`python materialize.py <清单.json> --source-root <原PDF文件夹> --output <新的本机样本目录>`

生成后实际查看每张题目与答案裁图，再执行prepare绑定样本目录。导出后还须查看PDF。不把reviewed字段、文件存在或无报错当成语义正确。扫描件无法读清时停在该题，不私自外发OCR；用户若允许外部服务，先明确材料和目的地。
