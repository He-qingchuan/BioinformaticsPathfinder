## 几种图说的是不同侧面

UMAP 表达图问“信号在哪里”，小提琴问“群内分布怎样”，点图同时问“多少细胞检出、均值多高”，矩阵图看群均值，热图展开单细胞差异。切换图形不等于重复证明同一个结论，它们提供互补视角。

{{flow}}

{{illustration:dotplot}}

## 先看位置，再看分布

{{figure:marker_feature}}

{{figure:marker_violin}}

{{figure:stacked}}

## 点的面积与颜色必须分别读

{{figure:marker_dot}}

{{lab:dot}}

## 同样是热颜色，数值口径可能不同

{{figure:matrix}}

{{figure:zmatrix}}

## 群均值之外，看看每枚细胞

{{figure:heat}}

{{figure:zheat}}

## 一组 marker 比一个 marker 更可靠

使用前核对物种、组织和基因 ID。骨髓中的 HBA1/HBB、MS4A1、CD3D/TRAC、LYZ 等提供不同谱系线索，但每个基因都不是无条件专一。证据应包含多个支持 marker、反证、检出比例、QC 和样本组成。不存在的数据列或未检测基因要明确说明，不能把缺失当阴性。
