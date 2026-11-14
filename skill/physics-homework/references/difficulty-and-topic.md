# Direct Topic Request Mode

Use this mode when the user names a Cambridge 9702 Topic or microtopic without supplying a board image. Typical input may be spoken and terse.

## Parse the request

Extract these fields before searching:

| Field | Rule |
|---|---|
| Topic | Map Chinese or English wording to the nearest syllabus Topic/subsection. |
| Count | Honor an explicit number. Otherwise use the standard AS/A2 defaults in `SKILL.md`. |
| Difficulty | Normalize `简单/基础/easy`, `中等/medium`, and `困难/挑战/hard`. |
| Type | Normalize `选择题/MCQ`, `大题/结构题/structured`, or mixed. Enforce syllabus paper availability. |
| Source limits | Honor explicit year, session, paper, or component limits. |
| Repeats | Avoid prior homework by default when history is available. Allow repeats only when explicitly requested. |

If only a broad Topic is named, include all syllabus subsections within that Topic. If a microtopic is named, do not widen to neighboring subsections merely to reach the requested count.

## Enforce paper types

- AS Topics 1–11: Paper 1 for official MCQ and Paper 2 for structured questions.
- A2 Topics 12–25: Paper 4 structured questions only. Do not invent or adapt MCQ unless the user explicitly requests teacher-authored questions.
- Practical requests: Paper 3 or Paper 5 according to the named skill.

An explicit request such as “三道圆周运动中等题” maps to A2 Topic 12, three Paper 4 structured questions, all independently verified as medium.

## Judge difficulty from the complete question

Do not rely only on a bank label.

- **Easy:** direct definition, recognition, or one-step substitution; familiar representation; few dependent marks.
- **Medium:** two to four linked reasoning/calculation steps; standard force resolution, comparison, graph use, or interpretation in a familiar or mildly unfamiliar context; no hidden cross-topic dependency.
- **Hard:** non-obvious modelling or derivation, several dependent stages, unfamiliar synthesis, demanding graph/data inference, or substantial cross-linking of concepts.

Use the complete retained question and its mark scheme. A long question is not automatically hard, and a short conceptual question is not automatically easy.

For an exact difficulty request, every item must match. For wording such as “medium-focused” or “以中等为主”, prefer the requested level and use an adjacent level only if needed; report the substitution.

## Select a balanced set

Within the requested boundary and difficulty:

1. Prefer different physical contexts and assessment operations.
2. Avoid three numerical variants of the same method.
3. Spread years and components when possible.
4. Reject any question whose later subpart crosses the requested boundary.
5. Reject any question with uncertain question/mark-scheme alignment.

## Deliver

Return separate clickable Student Questions and Answers/Mark Scheme PDFs. State the level and paper type, actual count, total marks when known, sources, difficulty judgment, and any reduction or substitution.
