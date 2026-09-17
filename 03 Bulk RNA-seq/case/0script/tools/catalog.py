# 文件用途｜声明命令行可改参数的白名单和类型边界。
# 使用：由 0script/tools/run_chapter.py 导入；只提供规则/函数，不作为单独分析步骤执行。输入输出与每个
#   参数见下面接口注释。
# 注释用 # 独立行说明；现有 docstring 和程序帮助文本保持原样，不把注释变成执行时读取的新配置。

"""命令行参数定义；保留原章节的参数类型、范围和默认值。"""
# 接口｜parameter：声明一个 CLI 参数的元数据。
# 参数：
# default（必填，无默认值）：省略参数时的默认值；可为数字、字符、布尔或列表。
# label（必填，无默认值）：可读的简短中文名称，不是传参键名。
# help_text（必填，无默认值）：说明用途和修改影响的字符串。
# kind（默认 'number'）：参数类型名，如 number/integer/choice/string/boolean 及复数数组类型；决定验证
#   和转换。
# minimum（默认 None）：数值下界或 None；仅数值类型使用，None 不限制这一端。
# maximum（默认 None）：数值上界或 None；仅数值类型使用，None 不限制这一端。
# choices（默认 None）：允许值列表或 None；列表存在时每个值须在其中。
# style（默认 False）：bool；True 表示允许用于仅重绘请求，False 表示不能在 redraw 请求中修改；不代表参
#   数不写入清单。
# 返回/写出与边界：返回描述字典；这里只声明，不校验实际值、不运行分析。PARAMETERS 白名单由这些描述组成。
def parameter(default, label, help_text, kind="number", minimum=None, maximum=None, choices=None, style=False):
    return dict(default=default, label=label, help=help_text, type=kind,
                minimum=minimum, maximum=maximum, choices=choices, style=style)


# 数组参数在 CLI JSON 中提供列表，验证后才转为 R 向量；从不 eval 用户输入。
P = parameter
# 字典键是 MD 的 execute 单元名；每项的 default/类型/边界用于 CLI 验证，不意味着可以修改 MD 中没有白名
#   单的所有变量。
PARAMETERS = {
    "fastp": {
        "sample_jobs": P(2, "同时处理样本数", "总线程分给并行样本。", "integer", 1, 64),
        "min_length": P(20, "最短长度（nt）", "过滤后长度下限；更改会重新过滤。", "integer", 1, 1000),
        "qualified_quality_phred": P(20, "合格碱基质量", "Phred 阈值。", "integer", 0, 40),
        "unqualified_percent_limit": P(40, "不合格碱基上限（%）", "允许低质量碱基的最大百分比。", "integer", 0, 100),
        "n_base_limit": P(5, "N 碱基上限", "超过则过滤该 read。", "integer", 0, 1000),
        "compression_level": P(6, "压缩等级", "只影响体积和压缩耗时。", "integer", 1, 9),
    },
    "index": {"kmer_length": P(31, "索引 k-mer", "修改后需重新建索引及定量。", "integer", 15, 31)},
    "quantification": {
        "sample_jobs": P(2, "同时定量样本数", "总线程分给并行样本。", "integer", 1, 64),
        "library_type": P("A", "文库类型", "A 自动判断；其他值应依据建库记录。", "choice",
                          choices=["A", "IU", "ISF", "ISR", "OU", "OSF", "OSR", "MU", "MSF", "MSR"]),
    },
    "sample_relationships": {
        "removeVar": P(.3, "去除低变异基因比例", "0.3 为去除最低的 30%，不是保留 30%。", minimum=0, maximum=.99),
        "correlation_method": P("pearson", "相关系数", "改变后重新计算相关性。", "choice", choices=["pearson", "spearman"]),
        "pca_x": P("PC1", "横轴主成分", "必须存在的主成分。", "choice", choices=["PC1", "PC2", "PC3", "PC4", "PC5"]),
        "pca_y": P("PC2", "纵轴主成分", "不能与横轴相同。", "choice", choices=["PC1", "PC2", "PC3", "PC4", "PC5"]),
        "label_versions": P([False, True], "样本标签版本", "false 无标签，true 有标签，可保留两版。", "booleans", style=True),
        "encircle_versions": P([False, True], "分组包围版本", "只是视觉辅助，不是置信区间。", "booleans", style=True),
        "expression_threshold": P(1, "表达基因阈值", "单位为原流程 TMM 表达量。", minimum=0),
    },
    "deseq2": {
        "min_reps": P(2, "低表达过滤样本数", "至少多少个样本 CPM 大于阈值；更改会重新拟合。", "integer", 1, 10000),
        "min_cpm": P(1, "低表达过滤 CPM", "与 min_reps 联合使用。", minimum=0),
    },
    "sets": {
        "nintersects": P(30, "UpSet 交集数", "最多显示多少个交集。", "integer", 1, 500, style=True),
        "venn_first_n": P(3, "经典韦恩集合数", "过多集合优先查看 UpSet。", "integer", 2, 5, style=True),
        "venn_styles": P(["default", "gradient"], "韦恩图样式", "保留多个有效样式。", "strings", choices=["default", "gradient"], style=True),
        "directions": P(["all", "up", "down"], "基因方向", "按已保存差异结果取集合。", "strings", choices=["all", "up", "down"], style=True),
    },
    "volcano": {
        "top_n": P(5, "每个方向标签数", "10 表示上调、下调各最多标注 10 个基因；0 不选标签。", "integer", 0, 200, style=True),
        "methods": P(["enhanced", "classic", "gradient"], "火山图类型", "可同时保留三种，不改变差异分析。", "strings", choices=["enhanced", "classic", "gradient"], style=True),
        "label_versions": P([False, True], "标签版本", "false 无标签，true 有标签。", "booleans", style=True),
        "label_size": P(3, "标签字号", "只改变文字大小。", minimum=1, maximum=12, style=True),
        "width": P(10, "图宽（英寸）", "不改变统计结果。", minimum=2, maximum=40, style=True),
        "height": P(8, "图高（英寸）", "不改变统计结果。", minimum=2, maximum=40, style=True),
        "dpi": P(180, "PNG 分辨率", "PDF 仍为矢量输出。", "integer", 72, 600, style=True),
    },
    "top_heatmaps": {
        "top_num": P(30, "单比较 Top 基因数", "从保存的差异结果选择。", "integer", 1, 1000, style=True),
        "overview_top_nums": P([100, 300], "概览 Top 数量", "逗号分隔，可保留多套。", "integers", 1, 2000, style=True),
        "palettes": P(["blue_orange", "red_blue"], "热图配色", "保留两个配色选择。", "strings", choices=["blue_orange", "red_blue"], style=True),
        "plot_width": P(12, "图宽（英寸）", "只改变排版。", minimum=2, maximum=40, style=True),
        "fontsize": P(8, "字号", "只改变排版。", minimum=2, maximum=20, style=True),
    },
    "time_input": {"tpm_threshold": P(1, "表达过滤 TPM", "改变进入聚类的基因集合。", minimum=0)},
    "time_clustering": {
        "top_var_props": P([.1, .2], "高变异基因比例", "例如 0.1,0.2 分别保留两套。", "numbers", .001, 1),
        "cluster_numbers": P([6, 7, 8, 9, 10], "聚类数", "逗号分隔，保留原多个可选方案。", "integers", 2, 30),
        "markGenes_num": P(30, "标记基因数", "只改变展示时优先复用聚类对象。", "integer", 0, 500, style=True),
        "enrichment_top_n": P(5, "每模块 GO 条目数", "不是标记基因数。", "integer", 1, 50, style=True),
        "line_variants": P(["line1", "line2", "line3"], "时间曲线样式", "保留原三种样式。", "strings", choices=["line1", "line2", "line3"], style=True),
        "label_versions": P([False, True], "基因标签版本", "可同时有标签与无标签。", "booleans", style=True),
        "go_versions": P([False, True], "GO 展示版本", "只改变是否展示已计算的 GO 条目。", "booleans", style=True),
        "label_size": P(10, "标签字号", "只改变排版。", minimum=2, maximum=24, style=True),
        "heatmap_dpi": P(130, "热图分辨率", "PNG dpi。", "integer", 72, 400, style=True),
    },
    "jtk_input": {"tpm_threshold": P(.5, "周期输入过滤 TPM", "先按所有时期的组内中位数过滤。", minimum=0)},
    "jtk_analysis": {
        "minper": P(20, "最小候选周期（小时）", "实际可检验周期受采样间隔限制。", minimum=.01, maximum=1000),
        "maxper": P(28, "最大候选周期（小时）", "不能超过数据支持范围而声称已经检验。", minimum=.01, maximum=1000),
        "fdr_cutoff": P(.05, "周期 BH 阈值", "严格小于该值。", minimum=.000001, maximum=1),
    },
    "jtk_plots": {
        "top_genes": P(12, "曲线基因数", "只从已有检验结果绘图。", "integer", 1, 200, style=True),
        "facet_columns": P(4, "每行面板数", "只改变排版。", "integer", 1, 12, style=True),
        "plot_width": P(12, "图宽（英寸）", "只改变排版。", minimum=2, maximum=40, style=True),
        "plot_height": P(8, "图高（英寸）", "只改变排版。", minimum=2, maximum=40, style=True),
        "plot_dpi": P(180, "分辨率", "PNG dpi。", "integer", 72, 600, style=True),
    },
    "diamond": {
        "seed_evalue": P(.00001, "种子 E 值", "更改需重新注释。", minimum=1e-20, maximum=1),
        "max_annotation_threads": P(12, "注释最多线程", "同时受项目总线程约束。", "integer", 1, 64),
    },
    "diamond_modules": {
        "top_var_props": P([.1,.2], "已有高变异基因比例", "与第 16 章组合一致；未单独修改时继承本次聚类设置。", "numbers", .001, 1),
        "cluster_numbers": P([6,7,8,9,10], "已有聚类数", "只处理第 16 章已生成的组合。", "integers", 2, 30),
        "enrichment_top_n": P(5, "每模块 GO 条目数", "只改变展示条目数。", "integer", 1, 50, style=True),
        "enrichment_fdr": P(.05, "模块富集 BH 阈值", "用于模块富集筛选。", minimum=.000001, maximum=1),
        "enrich_type": P("BP", "模块 GO 类别", "使用自建注释的相应本体。", "choice", choices=["BP","MF","CC","ALL"]),
        "minGSSize": P(10, "最小基因集", "改变后重新模块富集。", "integer", 1, 10000),
        "maxGSSize": P(500, "最大基因集", "改变后重新模块富集。", "integer", 1, 100000),
        "label_versions": P([False,True], "标签版本", "可同时保留有标签与无标签。", "booleans", style=True),
        "label_size": P(10, "标签字号", "只改变排版。", minimum=2, maximum=24, style=True),
    },
}
for block in ("sample_relationships", "sets", "volcano", "top_heatmaps", "time_input",
              "time_clustering", "jtk_input", "jtk_analysis", "jtk_plots", "diamond_modules"):
    PARAMETERS[block]["variant_label"] = P("", "另存标签", "同一关键参数下保留不同排版；不能含路径。", "string", style=True)
for block in ("ora_analysis", "gsea_analysis", "diamond_ora", "diamond_gsea"):
    PARAMETERS[block] = {
        "variant_label": P("", "另存标签", "保留不同排版的整套结果。", "string", style=True),
        "term_num": P([10, 20], "展示条目数", "可设置多个 Top 数；与 Top1 显示独立。", "integers", 1, 50, style=True),
        "ontologies": P(["BP", "MF", "CC", "ALL"], "GO 类别", "保留原各类分析。", "strings", choices=["BP", "MF", "CC", "ALL"]),
        "include_kegg": P(True, "计算 KEGG", "新分析可能访问 KEGG 网络；重绘只用保存的对象。", "boolean"),
        "minGSSize": P(10, "最小基因集", "改变后需重新富集分析。", "integer", 1, 10000),
        "maxGSSize": P(500, "最大基因集", "改变后需重新富集分析。", "integer", 1, 100000),
        "simplify_cutoff": P(.75, "GO 去冗余阈值", "更改会改变简化结果。", minimum=0, maximum=1),
        "plot_dpi": P(180, "图形分辨率", "PNG dpi。", "integer", 72, 600, style=True),
    }
    if "ora" in block:
        PARAMETERS[block].update({
            "directions": P(["all", "up", "down"], "差异方向", "分别计算全部、上调、下调集合。", "strings", choices=["all", "up", "down"]),
            "plot_styles": P(["bar", "dot"], "富集图样式", "条形图与点图均可保留。", "strings", choices=["bar", "dot"], style=True),
            "plot_width": P(10, "图宽（英寸）", "只改变排版。", minimum=2, maximum=40, style=True),
            "overview_dpi": P(150, "综合图分辨率", "综合图单独控制。", "integer", 72, 400, style=True),
        })
    else:
        PARAMETERS[block].update({
            "rankings": P(["log2FoldChange", "stat"], "排序统计量", "改变后需重新计算 GSEA。", "strings", choices=["log2FoldChange", "stat"]),
            "pvalue_tables": P([False, True], "Top1 的 P 值表", "空数组关闭 Top1；不控制多条目 TopN。", "booleans", style=True),
            "draw_dotplot": P(True, "绘制点图", "保留原展示选项。", "boolean", style=True),
        })
