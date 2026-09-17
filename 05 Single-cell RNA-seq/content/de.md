## 先问比较谁，再看统计表

本例既做每簇对其他簇的 one-versus-rest，也比较细粒度一级标签 B_cells 与 T_NK_ILCs。比较目标不同，背景也不同。必须在看 p 值前确定问题，不能挑完显著基因再倒推最有利的问题。

{{flow}}

{{illustration:replicates}}

## Wilcoxon 结果怎样读

本课使用 log1p 层，输出 names、scores、logfoldchanges、pvals、pvals_adj。scores 是排序检验统计量，logfoldchanges 是实现给出的近似 log2 倍数变化，pvals_adj 是多重检验校正后的值。三者含义不同；p 值不能当效应大小。

例如 B 对 T/NK/ILC 表中 CD74 的 logfoldchanges 约 5.025，支持该比较中的表达差异线索；这并不说明每一枚 B 细胞表达恰好是每一枚 T 细胞的固定倍数。数值为 0 的 p 值是有限精度表示，不是零错误风险。

{{figure:de_dot}}

{{figure:de_heat}}

## 特异性过滤后为什么会有空基因名

filter_rank_genes_groups 按簇内/簇外检出比例等规则过滤，不符合规则的候选可在对应导出位置留下空 names。它不等于原数据缺少那个基因，也不意味着应随意填一个新名字。

## 细胞很多，不等于重复很多

本课细胞级 Wilcoxon 作为描述性 marker 探索。要回答疾病或处理条件效应，需要独立生物学重复和匹配的设计，可考虑按样本与细胞类型汇总等方法，但本次教程不额外增加未运行的正式分析结果。

## AI 的停点

实际运行前先看可用标签、组别和人数，明确 comparison.question/group/reference，再确认执行。完成后同时报告幅度、检出比例、统计证据和设计边界。
