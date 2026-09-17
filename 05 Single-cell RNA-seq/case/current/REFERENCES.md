# 数据与方法来源

- 主数据：[NeurIPS 2021 Benchmark dataset](https://figshare.com/articles/dataset/NeurIPS_2021_Benchmark_dataset/22716739)。
- 主流程参考：[Scanpy preprocessing and clustering](https://scanpy.scverse.org/en/stable/tutorials/basics/clustering.html)。
- 方法背景与注释讨论：[Single-cell Best Practices](https://www.sc-best-practices.org/)；课件中以作者键标出的教材参考文献可在相应章节文献列表查阅。
- 数据结构：[AnnData 文档](https://anndata.scverse.org/en/stable/)。
- 双细胞检测：[Scanpy Scrublet](https://scanpy.scverse.org/en/stable/generated/scanpy.pp.scrublet.html)。
- 整合：[Harmony](https://github.com/slowkow/harmonypy)、[BBKNN](https://bbknn.readthedocs.io/en/latest/bbknn.bbknn.html)、[scVI](https://docs.scvi-tools.org/en/stable/)。
- 自动注释：[CellTypist](https://www.celltypist.org/)、[软件与模型使用说明](https://github.com/Teichlab/celltypist)。
- 程序化运行：[NBClient](https://nbclient.readthedocs.io/en/latest/)。
- 环境迁移：[conda-pack](https://conda.github.io/conda-pack/)。
- 中文字体：Noto Sans CJK SC；许可随 assets/FONT_LICENSE.txt 提供。

本课程的教学代码和说明基于项目已有课件整理；数据和第三方软件、字体分别遵循其原许可。


## 项目交互与资源核查补充

- [CellTypist 官方模型目录](https://www.celltypist.org/models) 与 [结构化清单](https://celltypist.cog.sanger.ac.uk/models/models.json)：运行前实际查询适配候选，名单会更新。
- [CellTypist 模型元信息](https://celltypist.readthedocs.io/en/latest/celltypist.models.Model.html)：检查模型说明、特征和标签范围。
- [单细胞最佳实践：QC](https://www.sc-best-practices.org/preprocessing-visualization/quality-control/)：结合分布与实验背景判断阈值。
- [Scanpy 10x H5 读取](https://scanpy.scverse.org/en/stable/generated/scanpy.read_10x_h5.html)、[10x MTX 读取](https://scanpy.scverse.org/en/stable/generated/scanpy.read_10x_mtx.html)：格式与计数矩阵读取。课程固定版本与在线最新版可能有接口差别，辅助读取器已按随包版本验证。

这些资料帮助核对方法与资源，不代替当前数据的真实图表、研究设计或用户决定。
