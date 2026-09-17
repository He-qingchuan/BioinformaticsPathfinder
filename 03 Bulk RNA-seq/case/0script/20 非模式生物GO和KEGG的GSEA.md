# 20 非模式生物支线：GO 和 KEGG 的 GSEA

<!-- normalized-inputs -->
输入字段和项目迁移规则见[输入规范](<附4 输入文件规范与项目迁移.md>)。代码从能看到 `0script` 的项目根目录运行。

## 本章从哪里读取参数

以下值来自 [project.env](project.env)，不是写死在函数里的常量。案例值与新项目模板值分别列出；实际运行读取你当前文件中的设置。图形特有参数仍在本章入口集中设置。修改后需重新运行读取/赋值段，再调用函数；已经在内存中的旧变量不会随文件编辑自动刷新。

| 参数 | 当前案例配置 | 空模板默认 | 用途与修改注意 |
| --- | --- | --- | --- |
| `FDR_CUTOFF` | `0.05` | `0.05` | 差异汇总、火山图及相应富集筛选使用的校正 P 值阈值；默认 0.05。 改小通常筛选更严格。各章具体作用见正文；不等于所有检验共享一次多重校正，也不控制所有同名局部阈值。 |
| `RANDOM_SEED` | `20260907` | `20260907` | 随机过程的整数种子；示例固定为 20260907，不需要随日期更新。 通常保留以便复现。变更可能改变随机标签位置或聚类，需另存结果；不保证跨软件版本完全一致。 |
| `DE_RESULT_FILE` | `5DESeq2/de_result.tsv` | `5DESeq2/padj0.05_lfc1/de_result.tsv` | 第 11–15、19–20 章读取的合并差异结果表。 第 10 章重新汇总后更新为实际新文件；更改阈值不会自动把旧表搬到新目录。 |

## 1. 排序不变，功能集合另建

本章继续使用第 10 章 DESeq2 的完整可排序基因，分别按 `log2FoldChange` 和 Wald `stat` 排序。区别在于 GO 来源是第 18 章自建 OrgDb，KEGG 来源是该路线的 `TERM2GENE`。不先筛选差异基因，也不因为某个排序结果更多就把另一种方法删掉。

DIAMOND 注释下的两种排序分目录保存。这些结果来自同一实验，不能把它们当作两次独立生物学验证。

## 2. GSEA 调用

本章参数在第 3 节设置。`comparison_ids` 选择比较，`rankings` 选择排序，`term_num` 选择展示条目数；`ontologies/include_kegg` 选择检验类别。`fdr_cutoff` 是 GSEA 的 P/BH 筛选阈值，`simplify_cutoff` 是 GO 去冗余阈值；`minGSSize/maxGSSize` 改变参与检验的基因集范围。含义与第 15 章保持一致，参数均通过本章函数传入，不需要修改第 15 章函数体。

使用第 15 章已展示的 `plot_GSEA` 函数，保留 GO BP/MF/CC/ALL、去冗余、Top10/Top20 曲线和点图，以及 Top1 有/无 P 值表。KEGG 用 clusterProfiler 的 `GSEA(TERM2GENE = ...)`，不把自定义基因 ID 强塞给模式物种接口。

实现：[查看编号脚本](scripts/20_nonmodel_gsea_functions.R)。

<!-- execute: nonmodel_gsea_functions env=rnaseq -->
```r
# 目的：加载本节共用函数，供后面的分析/重绘入口调用；本段不启动统计或绘图。
# source("路径")：在当前 R 会话读取该脚本及它声明的共用依赖。路径相对项目根目录，不是下载地址。
# 输入：0script/scripts/20_nonmodel_gsea_functions.R；产物是 R 会话中的函数定义，不是结果文件。
# 修改脚本后需重新 source；仅加载函数不会自动更新已有结果，后面的参数赋值和调用仍须执行。

source("0script/scripts/20_nonmodel_gsea_functions.R")
```

关键参数与第 15 章一致：基因集大小 10–500、BH 校正、固定随机种子、`eps = 0`、串行后端。背景由完整排序列表和注释匹配共同决定，不能另传一个只含显著基因的背景来改变这一含义。

## 3. 使用 DIAMOND 注释执行

实现：[查看编号脚本](scripts/20_diamond_gsea.R)。

<!-- execute: diamond_gsea env=rnaseq -->
```r
# 目的：批量运行 DIAMOND 自建注释的非模式 GSEA。
# 关键输出：output_root/fdr阈值_gs最小-最大_top展示数/比较ID/排序名[__标签]/。
#   默认根目录 9Enrichment_Analysis/OrgDb/diamond/GSEA；
#   all_tests 为返回的完整检验，raw 为筛选后未去冗余，simplified 为 GO 去冗余结果。
#   保存 *_all_tests.tsv、*_raw.tsv、*_simplified.tsv 和 GSEA_results.rds；空/未检验条目另有状态 TXT。
#   ranking.tsv 保存 gene_id/rank_value；
#   曲线名如 GO_BP_raw_top10_curves，点图以 _dotplot 结尾，Top1 区分 pvalue_table_TRUE/FALSE。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：单独保存支线结果与图，使用既有注释，不重新做蛋白搜索。
# 共用读取：readRenviron 读取 project.env；Sys.getenv 返回文本，as.numeric/as.integer 将阈值/种子转成数值。
#   更改配置后需重新执行读取与赋值，旧变量不会自动刷新。
# 参数设置（下方为本次取值；不需要修改函数内部实现）：
# comparison_ids：字符向量或 NULL，比较 ID 必须来自 contrasts.tsv 且已有差异结果。
#  NULL：处理全部启用比较；"Treat_vs_Control"：只处理这一个真实 ID。
#  c("A_vs_Control", "B_vs_Control")：只处理列出的多个比较，名称只是写法示例。
#  不按文件名拆组，不用 ""、NA 或 character() 代替“全部”；换项目从自己的比较表取值。
# rankings：单选或多选 c("log2FoldChange", "stat")；每一种都独立运行 GSEA。
#  "log2FoldChange"：按带正负方向的变化幅度排序；"stat"：按 DESeq2 Wald 统计量排序，结合效应与不确定性。
#  两者都使用完整可排序基因，不预先只选显著基因；不是同一个结果的两种画法。
#  排序正端对应实验组更高；结果可能不同，应按研究问题预先选用或并列作为探索。
# term_num：正整数向量；每种图最多展示的富集条目数，如 c(10,20) 各出 Top10/Top20，只取已有达标条目，不强行补足。要避免重算请选择重绘入口；
#   完整分析入口改此值仍会运行相应分析。
# ontologies：GO 本体，选 "BP"、"MF"、"CC"、"ALL" 中一个或多个，大小写按此填写。
#  "BP"：生物过程，如基因参与什么活动；"MF"：分子功能，如结合或催化能力。
#  "CC"：细胞组分，如位于什么结构；"ALL"：把三类 GO 条目合在同一次本体分析中。
#  c("BP", "MF", "CC", "ALL") 会分别运行四套，ALL 不是前三张显著表的简单拼接。
#  改本体会改变检验集合和校正范围；不只是换标题，不能在重绘阶段补算缺少的本体。
# include_kegg：单个 TRUE/FALSE；TRUE 计算所选路线的 KEGG 富集，FALSE 跳过 KEGG、仍分析所选 GO。
#  官方路线 TRUE 需匹配的物种代码、基因 ID 及可用 KEGG 服务；自建路线 TRUE 需第 18 章通路映射。
#  没有匹配注释时用 FALSE 明确跳过，不用另一物种的数据冒充。
# fdr_cutoff：数值阈值，通常 0.05，范围 (0,1]；控制当前步骤的校正 P 值筛选，调小更严格。各比较/富集本体分别校正，不代表全项目共同做一次 BH。
# minGSSize：正整数；与输入/背景匹配后的基因集中允许的最少基因数。提高会排除较小条目，改变参与检验的条目集合。
# maxGSSize：正整数，且不小于 minGSSize；允许的最大基因集规模。降低会排除过大的条目，改变检验范围。
# simplify_cutoff：0–1 数值；GO 语义相似性去冗余门槛，不是 P 值。越低越容易将相似条目合并；原始 raw 结果仍单独保留，KEGG 不做这项 GO 简化。
# seed：整数随机种子；用于需要随机过程的步骤，保持相同有助于复现，不是采样时间。改变种子可能改变聚类、GSEA 或标签布局，需保留独立结果。
# draw_dotplot：单个 TRUE/FALSE；TRUE 保存 GSEA 点图，FALSE 不画点图。
#  TopN 富集曲线仍由 term_num 控制，Top1 的附表版本由 pvalue_tables 控制。
#  此开关不改变统计量；要避免重算请使用本章重绘入口，而非完整分析入口。
# pvalue_tables：逻辑向量，仅控制 Top1 富集曲线的附表版本，不控制 TopN 多曲线。
#  FALSE：Top1 不附 P 值表；TRUE：Top1 附表；c(FALSE, TRUE)：两版都保存。
#  logical()：不画 Top1 版本，但仍按 term_num 画 TopN；附表不代表重新检验。
# plot_dpi：正数，单位像素/英寸；PNG 的像素密度。相同英寸下越大像素越多、文件通常越大；PDF 的矢量图形不靠此值提高清晰度。
# output_root：字符路径；本步骤输出根目录，函数再按比较/参数建立子目录。通常沿用；试算可选新目录，但后续读取位置不会自动更新。
# variant_label：一个文本标签，默认 "" 表示不加额外后缀；如 "large_font" 会给末级结果目录加 __large_font。
#  非空时只用字母、数字、点、下划线、短横线，首字符为字母或数字；不填路径、空格或 NA。
#  调整未进入目录名的图幅、字体等时用不同标签另存；标签本身不改变计算参数。
#  它不是强制覆盖开关：同一路径参数冲突仍停止，不修改旧结果清单。
# 调用：先加载脚本，再设置参数，最后运行函数。改值后重新执行赋值和调用。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/20_diamond_gsea.R")
comparison_ids <- NULL
rankings <- c("log2FoldChange", "stat")
term_num <- c(10, 20)
ontologies <- c("BP", "MF", "CC", "ALL")
include_kegg <- TRUE
fdr_cutoff <- as.numeric(Sys.getenv("FDR_CUTOFF"))
minGSSize <- 10
maxGSSize <- 500
simplify_cutoff <- 0.75
seed <- as.integer(Sys.getenv("RANDOM_SEED"))
draw_dotplot <- TRUE
pvalue_tables <- c(FALSE, TRUE)
plot_dpi <- 180
output_root <- "9Enrichment_Analysis/OrgDb/diamond/GSEA"
variant_label <- ""
# interface-parameters: diamond_gsea
run_diamond_gsea(
  comparison_ids = comparison_ids,
  rankings = rankings,
  term_num = term_num,
  ontologies = ontologies,
  include_kegg = include_kegg,
  fdr_cutoff = fdr_cutoff,
  minGSSize = minGSSize,
  maxGSSize = maxGSSize,
  simplify_cutoff = simplify_cutoff,
  seed = seed,
  draw_dotplot = draw_dotplot,
  pvalue_tables = pvalue_tables,
  plot_dpi = plot_dpi,
  output_root = output_root,
  variant_label = variant_label
)
```

### 查看本步关键文件

示例查看本次第一个比较和第一个排序。ranking 是实际有方向的完整排序；结果中的 NES 描述富集方向和程度，p.adjust 为本检验集合内的校正 P 值，core_enrichment 为核心基因。

```r
# 目的：只读当前参数路径的关键文本；留在上一框的 R 会话，不重新分析。
# 前提：上一分析已成功或明确提示完整结果复用；若报错/冲突，先处理，不把旧文件当本次成功结果。
# preview_dir/preview_files 只用于查看，不是传给分析函数的新参数。
# file.path 拼接路径；readLines(n = 10) 最多读前 10 行，含表头；不整表读入内存。
# file.exists 检查是否存在；cat 用 sep = "\n" 逐行显示；warn = FALSE 省略末行换行提示。
# nzchar 判断标签是否非空；非空时按原命名规则在末级目录加 __标签。
preview_comparisons <- read_contrasts()
preview_ids <- if (is.null(comparison_ids)) preview_comparisons$contrast_id[preview_comparisons$enabled] else comparison_ids
stopifnot(length(preview_ids) > 0)
preview_id <- preview_ids[1]
cat("示例比较：", preview_id, "\n")
preview_dir <- file.path(output_root, parameter_tag(fdr = fdr_cutoff, gs = c(minGSSize, maxGSSize),
  top = term_num), preview_id, rankings[1])
if (nzchar(variant_label)) preview_dir <- paste0(preview_dir, "__", variant_label)
preview_annotations <- c(paste0("GO_", ontologies), if (include_kegg) "KEGG" else character())
stopifnot(length(preview_annotations) > 0)
preview_annotation <- preview_annotations[1]
preview_files <- file.path(preview_dir, c("ranking.tsv", paste0(preview_annotation, c("_all_tests.tsv", "_raw.tsv", "_simplified.tsv"))))
if (preview_annotation == "KEGG") preview_files <- preview_files[!grepl("_simplified.tsv$", preview_files)]
for (preview_file in preview_files) {
  cat("\n文件：", preview_file, "\n")
  if (file.exists(preview_file)) {
    cat(readLines(preview_file, n = 10, warn = FALSE), sep = "\n")
  } else {
    cat("尚无此文件：核对上一步是否完成、是否选择该分析，以及空结果提示。\n")
  }
}
```

只运行一次时，把入口 `comparison_ids` 设为一个有效比较 ID、`rankings <- "stat"`、`ontologies <- "BP"`、`include_kegg <- FALSE`，并把输出目录改为同级 `GSEA/custom`；然后执行同一个调用段。无需再定义另一个 GSEA 函数。

已有统计结果只想改 Top 数量、是否附 P 值表时，使用第 15 章第 4.4 节的 `save_gsea_result()` 重绘示例，将 `source_dir` 设为本路线的比较/排序目录。该示例读取 `GSEA_results.rds`，不会重新查询数据库或进行 GSEA。

## 4. 结果文件

例如 `9Enrichment_Analysis/OrgDb/diamond/GSEA/ZT4_vs_ZT0/stat/` 表示 DIAMOND 注释、ZT4 相对 ZT0、Wald 统计量排序。`ranking.tsv` 保存实际排序；`GO_BP_all_tests.tsv` 保存调用返回的完整检验表，无法计算 P 值的条目可能被包移除，须结合第 15 章的警告说明阅读；`GO_BP_raw.tsv` 保存显著条目；`GO_BP_simplified.tsv` 保存 GO 去冗余后的代表条目。PDF 适合排版，PNG 适合直接浏览。

正 NES 偏向实验组上调的一端，负 NES 偏向下调的一端。不同注释覆盖和不同排序会影响 NES 与校正 P 值，不能将多个路线的结果拼在一起后宣称它们共享同一个 FDR。功能转移的可靠性仍需独立证据验证。

## 5. 本次 DIAMOND 结果示例

下面是 ZT4_vs_ZT0 在同一套 DIAMOND 注释下、去冗余前的显著条目数。两种排序都保留，不因某一种数量更多就把另一种删除。

| 检验集合 | log2FoldChange 排序 | Wald stat 排序 |
| --- | --- | --- |
| GO BP | 0 | 26 |
| GO MF | 0 | 4 |
| GO CC | 1 | 13 |
| GO ALL | 1 | 46 |
| KEGG | 5 | 31 |

数量来自各目录的 `*_raw.tsv`。ALL 的校正范围独立于 BP/MF/CC，因此不要求它等于三者数量相加。排序指标不同，基因位置和富集分数也会不同；不是把同一组 P 值换一个颜色。

log2FoldChange 排序下，`GO:0019005`（SCF ubiquitin ligase complex）的 NES 为 −2.137，BH 校正 P 值约为 0.00410。以下两张图对应完全相同的结果，区别只是是否显示 P 值表。

| 不附 P 值表 | 附 P 值表 |
| --- | --- |
| ![GO CC 单条目曲线，无 P 值表](../9Enrichment_Analysis/OrgDb/diamond/GSEA/ZT4_vs_ZT0/log2FoldChange/GO_CC_raw_top1_pvalue_table_FALSE.png) | ![GO CC 单条目曲线，有 P 值表](../9Enrichment_Analysis/OrgDb/diamond/GSEA/ZT4_vs_ZT0/log2FoldChange/GO_CC_raw_top1_pvalue_table_TRUE.png) |

Wald 排序下可以同时查看多个 GO BP 条目；多曲线用于整体方向，NES 点图便于逐项比较，详细核心基因仍应回看表格。

![Wald 排序的 GO BP Top20 曲线](../9Enrichment_Analysis/OrgDb/diamond/GSEA/ZT4_vs_ZT0/stat/GO_BP_raw_top20_curves.png)

![Wald 排序的 GO BP Top20 NES 点图](../9Enrichment_Analysis/OrgDb/diamond/GSEA/ZT4_vs_ZT0/stat/GO_BP_raw_top20_dotplot.png)

## 6. 示例的后端诊断

使用第 15 章的同一诊断函数，分别核对上面展示的 GO CC 单条目图和 GO BP 多条目图所依据的完整检验集合。它读取 DIAMOND 路线保存的基因集，不会改用官方 GO 集合，也不覆盖主结果。

实现：[查看编号脚本](scripts/20_diamond_example_diagnostics.R)。

<!-- execute: diamond_example_diagnostics env=rnaseq -->
```r
# 目的：选择启用列表中第二个比较（不足两个时取第一个）做非模式 GSEA 诊断。
# 关键输出：NONMODEL_GSEA_RESULT_ROOT/比较ID/排序/diagnostics/注释类别/，内含 注释类别_backend.tsv、_warnings.txt、_check.tsv。
#   选择启用列表中第二个比较（不足两个取第一个）；会复算诊断统计，但不覆盖原 GSEA_results.rds。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：读取保存对象，对 log2FoldChange/GO_CC 与 stat/GO_BP 两组底层 fgsea 复算核对；会计算诊断统计，但不重写原结果、不放宽阈值。
# 共用读取：readRenviron 读取 project.env；Sys.getenv 返回文本，as.numeric/as.integer 将阈值/种子转成数值。
#   更改配置后需重新执行读取与赋值，旧变量不会自动刷新。
# 本入口没有可调形参；先 source 加载当前定义，再调用函数即可。输入来自本节说明的项目文件，不需要寻找一个并不存在的参数赋值段。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/20_diamond_example_diagnostics.R")
run_diamond_example_diagnostics()
```

### 查看本步关键文件

查看两套诊断的 original_statistics_match、非有限 P 值数量及软件版本；这是核对统计的一致性，不是新的生物学验证。历史 runlogs 下的诊断不被当成本次新生成。

```r
# 目的：只读当前参数路径的关键文本；留在上一框的 R 会话，不重新分析。
# 前提：上一分析已成功或明确提示完整结果复用；若报错/冲突，先处理，不把旧文件当本次成功结果。
# preview_dir/preview_files 只用于查看，不是传给分析函数的新参数。
# file.path 拼接路径；readLines(n = 10) 最多读前 10 行，含表头；不整表读入内存。
# file.exists 检查是否存在；cat 用 sep = "\n" 逐行显示；warn = FALSE 省略末行换行提示。
preview_comparisons <- read_contrasts()
preview_ids <- preview_comparisons$contrast_id[preview_comparisons$enabled]
stopifnot(length(preview_ids) > 0)
preview_id <- preview_ids[min(2, length(preview_ids))]
preview_root <- project_result("NONMODEL_GSEA_RESULT_ROOT", "9Enrichment_Analysis/OrgDb/diamond/GSEA")
preview_files <- c(
  file.path(preview_root, preview_id, "log2FoldChange/diagnostics/GO_CC/GO_CC_check.tsv"),
  file.path(preview_root, preview_id, "stat/diagnostics/GO_BP/GO_BP_check.tsv")
)
for (preview_file in preview_files) {
  cat("\n文件：", preview_file, "\n")
  if (file.exists(preview_file)) {
    cat(readLines(preview_file, n = 10, warn = FALSE), sep = "\n")
  } else {
    cat("尚无此文件：核对上一步是否完成、是否选择该分析，以及空结果提示。\n")
  }
}
```

已有案例的完整后端表、警告文本和数值一致性检查保存在 `0script/runlogs/gsea_diagnostics/diamond`；新运行写入明确选定的 GSEA 比较/排序目录下的 `diagnostics/注释类别`。诊断范围仅限上面的两个检验集合，不据此替其他检验集合作保证，也不把随机抽样误差解释成生物学重复间变异。

本次分别核对 261 个 GO CC 集合和 1,626 个 GO BP 集合，P 值、BH 校正值、ES 和 NES 均与保存结果一致；这两次诊断没有非有限 P 值或缺失的误差估计。
