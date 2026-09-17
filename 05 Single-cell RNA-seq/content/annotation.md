## 先有证据，再给名字

聚类只提供计算分组。细胞注释把本次分组与生物学知识联系起来，必须同时考虑 marker、群内异质性、质量和组织背景。粗标签便于概括，细标签表达更具体判断，但需要更强支持。

{{flow}}

{{illustration:annotation}}

{{figure:fine_dot}}

{{figure:manual}}

## 历史参考与新建议表的区别

历史 annotation_evidence_legacy.csv 解释这次案例怎样得出标签。它不是新数据的答案。换数据、聚类或成员后，相同数字簇号可能对应完全不同群体。

新版第 08 章先导出 marker_evidence、cluster_qc_evidence 和空的 annotation_proposal。程序固定 cluster_key、cluster、n_cells；AI 根据本次图表填写 level1、level2、support、supporting_markers、opposing_markers、evidence_refs、rationale、uncertainty。

## 怎样与用户讨论

AI 逐簇说明拟注释成什么、有哪些支持、反证是否存在、哪里不确定，并给出本次证据路径。用户可以接受或修改。证据不足时用 Uncertain 或谨慎描述，不能为了把表填满而硬判一种类型。support 是定性支持程度，不是正确概率。

## 确认需要绑定本次证据

只有用户真实确认后才应用标签。若建议表、上游结果或成员变了，旧确认就失效；不能用 AI 自己的建议填成用户回复。最终保留两级标签、证据表与记录，方便后面发现矛盾时回到这一站修订。
