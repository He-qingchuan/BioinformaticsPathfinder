# 15 模式生物 GO 和 KEGG 的 GSEA

<!-- normalized-inputs -->
输入字段和项目迁移规则见[输入规范](<附4 输入文件规范与项目迁移.md>)。代码从能看到 `0script` 的项目根目录运行。

## 本章从哪里读取参数

以下值来自 [project.env](project.env)，不是写死在函数里的常量。案例值与新项目模板值分别列出；实际运行读取你当前文件中的设置。图形特有参数仍在本章入口集中设置。修改后需重新运行读取/赋值段，再调用函数；已经在内存中的旧变量不会随文件编辑自动刷新。

| 参数 | 当前案例配置 | 空模板默认 | 用途与修改注意 |
| --- | --- | --- | --- |
| `ORGDB_PACKAGE` | `org.At.tair.db` | 空（按条件填写） | 第 14–16 章使用的物种 OrgDb 包名称；案例为 org.At.tair.db。 换物种时安装并填写匹配的包；没有合适 OrgDb 时不能借用拟南芥或小鼠包冒充。 |
| `ORGDB_KEYTYPE` | `TAIR` | 空（按条件填写） | 传给 OrgDb 的基因 ID 类型；案例 TAIR，与输入 gene_id 对应。 通过 AnnotationDbi::keytypes() 核实；修改字符串并不会自动转换基因 ID。 |
| `KEGG_ORGANISM` | `ath` | 空（按条件填写） | 第 14–16 章 KEGG 的物种代码；案例 ath，人类 hsa，小鼠 mmu。 核对目标物种与实际 ID；没有匹配 KEGG 时明确关闭相应分析，不照搬案例代码。 |
| `KEGG_KEYTYPE` | `kegg` | `kegg` | KEGG 接口的 ID 类型；默认 kegg，不是 OrgDb 的 keyType。 按已取得的基因标识核实，可用类型取决于接口；不要把 ENSEMBL 字符串假装成 NCBI GeneID。 |
| `FDR_CUTOFF` | `0.05` | `0.05` | 差异汇总、火山图及相应富集筛选使用的校正 P 值阈值；默认 0.05。 改小通常筛选更严格。各章具体作用见正文；不等于所有检验共享一次多重校正，也不控制所有同名局部阈值。 |
| `RANDOM_SEED` | `20260907` | `20260907` | 随机过程的整数种子；示例固定为 20260907，不需要随日期更新。 通常保留以便复现。变更可能改变随机标签位置或聚类，需另存结果；不保证跨软件版本完全一致。 |
| `DE_RESULT_FILE` | `5DESeq2/de_result.tsv` | `5DESeq2/padj0.05_lfc1/de_result.tsv` | 第 11–15、19–20 章读取的合并差异结果表。 第 10 章重新汇总后更新为实际新文件；更改阈值不会自动把旧表搬到新目录。 |
| `GSEA_RESULT_ROOT` | `9Enrichment_Analysis/GSEA` | `9Enrichment_Analysis/GSEA/fdr0.05_gs10-500_top10-20` | 第 15 章重绘已有模式物种 GSEA 结果时读取的根目录。 换结果组合时更新；不混读另一种阈值或 ID 类型的结果，通常无需为换样本名修改。 |
| `NONMODEL_GSEA_RESULT_ROOT` | `9Enrichment_Analysis/OrgDb/diamond/GSEA` | `9Enrichment_Analysis/OrgDb/diamond/GSEA/fdr0.05_gs10-500_top10-20` | 第 20 章非模式支线 GSEA 重绘读取目录。 支线结果组合改变后明确更新；不是主线 GSEA 的目录。 |

## 1. 不先筛出差异基因

GSEA 使用完整的、有方向的基因排序，判断一个功能集合是否集中在列表的一端。它能发现许多基因变化幅度不大但方向一致的信号。若先筛选显著基因，排序列表被截断，就不再是这里定义的分析。

这里“完整”指未按差异显著性截断的可检验、可排序基因：输入已通过第 10 章比较内 CPM 过滤，本章还排除非有限排序值或非有限检验 P 值，并非所有定量基因。实际 `geneList` 界定排序空间，不能套用 ORA 的候选/背景比例解释。

保留原稿的 `log2FoldChange` 排序，并独立运行 Wald `stat` 排序。前者强调效应大小，后者同时考虑标准误。两种结果分目录保存，不在缺失 `stat` 时悄悄切换，不根据哪一种更显著事后决定方法。

## 2. 参数与图形

| 参数 | 含义 |
| --- | --- |
| `geneList` | 递减排序的命名数值向量；名称是唯一基因 ID，数值是该路线的排序指标 |
| `minGSSize/maxGSSize` | 10/500，以与输入排序列表匹配后的集合大小为基础 |
| `eps = 0` | 不把较小尾部概率截断在默认下界；并不意味着改成精确检验 |
| `pAdjustMethod = "BH"` | 对本次检验的基因集做多重校正 |
| `seed = TRUE` | 使用固定随机种子，使近似计算可追溯 |
| `BPPARAM = SerialParam()` | 使用串行后端，避免受限系统的本地通信问题，不更换分析算法 |
| `term_num` | 默认 `c(10, 20)`；改 `5` 将多条目曲线/点图改为 Top5；Top1 另由 `pvalue_tables` 控制，数量不足时不补条目 |
| `rankings` | 默认 `c("log2FoldChange", "stat")`；每种排序单独计算，不是同一结果换颜色 |
| `ontologies / include_kegg` | BP/MF/CC/ALL 和 KEGG 的选择；改变后计算对应检验集合 |
| `fdr_cutoff / simplify_cutoff` | 默认 0.05 / 0.75，分别是 P/BH 筛选与 GO 语义去冗余阈值 |
| `draw_dotplot / pvalue_tables` | 默认 `TRUE / c(FALSE, TRUE)`，控制点图与 Top1 有/无 P 值表 |
| `plot_dpi / output_root` | 默认 PNG 180 dpi；改参示例另设输出目录，不覆盖原图 |
| NES | 正值偏向排序顶部、负值偏向底部；对应实验组相对参照组的方向 |

BP/MF/CC 分别检验；ALL 将三类条目放进同一 GSEA 检验集合。不同检验集合的 BH 校正范围不同，不能直接按各表显著条目数量评价哪个分析更好。

## 3. GSEA 和绘图函数

实现：[查看编号脚本](scripts/15_gsea_functions.R)。

<!-- execute: gsea_functions env=rnaseq -->
```r
# 目的：加载本节共用函数，供后面的分析/重绘入口调用；本段不启动统计或绘图。
# source("路径")：在当前 R 会话读取该脚本及它声明的共用依赖。路径相对项目根目录，不是下载地址。
# 输入：0script/scripts/15_gsea_functions.R；产物是 R 会话中的函数定义，不是结果文件。
# 修改脚本后需重新 source；仅加载函数不会自动更新已有结果，后面的参数赋值和调用仍须执行。

source("0script/scripts/15_gsea_functions.R")
```

## 4. 运行与可选重绘

### 4.1 准备与参数入口

实现：[查看编号脚本](scripts/15_gsea_analysis.R)。

<!-- execute: gsea_analysis env=rnaseq -->
```r
# 目的：按比较和排序统计量批量运行模式物种 GSEA。
# 关键输出：output_root/fdr阈值_gs最小-最大_top展示数/比较ID/排序名[__标签]/。
#   默认根目录 9Enrichment_Analysis/GSEA；all_tests 为返回的完整检验，raw 为筛选后未去冗余，simplified 为 GO 去冗余结果。
#   保存 *_all_tests.tsv、*_raw.tsv、*_simplified.tsv 和 GSEA_results.rds；空/未检验条目另有状态 TXT。
#   ranking.tsv 保存 gene_id/rank_value；
#   曲线名如 GO_BP_raw_top10_curves，点图以 _dotplot 结尾，Top1 区分 pvalue_table_TRUE/FALSE。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：每种 ranking 单独计算并保存；效应量排序与 stat 排序是两个分析选择，不是重复画同一套图。
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
# kegg_keytype：官方 KEGG 接口的输入 ID 类型，取自 KEGG_KEYTYPE，单选一个字符串。
#  "kegg"：该物种的 KEGG 基因编号；"ncbi-geneid"：NCBI GeneID。
#  "ncbi-proteinid"：NCBI 蛋白编号；"uniprot"：UniProt 编号。
#  只有物种和当前输入 ID 存在可用映射才可选；不能将 ENSEMBL、TAIR 等直接写成这里的新选项。
#  本流程不自动替你转换差异表 ID；include_kegg=FALSE 时不调用官方 KEGG 接口。
# variant_label：一个文本标签，默认 "" 表示不加额外后缀；如 "large_font" 会给末级结果目录加 __large_font。
#  非空时只用字母、数字、点、下划线、短横线，首字符为字母或数字；不填路径、空格或 NA。
#  调整未进入目录名的图幅、字体等时用不同标签另存；标签本身不改变计算参数。
#  它不是强制覆盖开关：同一路径参数冲突仍停止，不修改旧结果清单。
# 调用：先加载脚本，再设置参数，最后运行函数。改值后重新执行赋值和调用。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/15_gsea_analysis.R")
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
output_root <- "9Enrichment_Analysis/GSEA"
kegg_keytype <- Sys.getenv("KEGG_KEYTYPE", "kegg")
variant_label <- ""
# interface-parameters: gsea_analysis
run_gsea_analysis(
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
  kegg_keytype = kegg_keytype,
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

### 4.2 单次示例（可选）

```r
# 目的：按本节的单次选择运行；这是独立可选示例，不必接在批量分析后执行。
# 关键输出：output_root/fdr阈值_gs最小-最大_top展示数/比较ID/排序名[__标签]/。
#   默认根目录 9Enrichment_Analysis/GSEA；all_tests 为返回的完整检验，raw 为筛选后未去冗余，simplified 为 GO 去冗余结果。
#   保存 *_all_tests.tsv、*_raw.tsv、*_simplified.tsv 和 GSEA_results.rds；空/未检验条目另有状态 TXT。
#   ranking.tsv 保存 gene_id/rank_value；
#   曲线名如 GO_BP_raw_top10_curves，点图以 _dotplot 结尾，Top1 区分 pvalue_table_TRUE/FALSE。
# 输入与输出：使用同一份项目配置和规范输入；输出根目录由下方 output_root 明确指定。
# 文件命名、全部参数的取值含义及限制见本章紧邻的完整参数入口与结果说明。
# 下方把全部公开参数列出，常改项在前，通常沿用项在后；不需要改函数体。
# source 加载函数；readRenviron 先读取配置，保证阈值和种子取自当前项目。
# comparison_id/selected_ids：由比较表取示例 ID，须核实所选比较已启用且已有结果。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/15_gsea_analysis.R")
comparison_id <- with(read_contrasts(), contrast_id[enabled][1])

# 本例选择：可以在此更换比较、分析内容和输出位置。
comparison_ids <- comparison_id
rankings <- "stat"
term_num <- 5
ontologies <- "BP"
include_kegg <- FALSE
output_root <- "9Enrichment_Analysis/GSEA/custom"

# 通常沿用：数值与原函数默认行为一致；需要调整时仍在这里修改。
fdr_cutoff <- as.numeric(Sys.getenv("FDR_CUTOFF"))
minGSSize <- 10
maxGSSize <- 500
simplify_cutoff <- 0.75
seed <- as.integer(Sys.getenv("RANDOM_SEED"))
draw_dotplot <- TRUE
pvalue_tables <- c(FALSE, TRUE)
plot_dpi <- 180
kegg_keytype <- Sys.getenv("KEGG_KEYTYPE", "kegg")
variant_label <- ""

run_gsea_analysis(
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
  kegg_keytype = kegg_keytype,
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

### 4.4 只重绘已有 GSEA 结果

实现：[只重绘脚本](scripts/15_gsea_redraw.R)。以下调用只读取已有对象，不重新检验。

```r
# 目的：读取指定保存的 GSEA 对象重绘曲线和点图。
# 关键输出：redraw_dir[__标签]/：所选 GSEA 对象的 TSV、TopN 曲线和点图、Top1 有/无 P 值表图。
#   名称使用 annotation_result_style，如 GO_BP_raw.tsv、GO_BP_raw_top5_curves.png/.pdf；不重算 GSEA。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：新图写 redraw_dir，原检验对象不改变；不因为 term_num 变动重新运行 GSEA。
# 共用读取：readRenviron 读取 project.env；Sys.getenv 返回文本，as.numeric/as.integer 将阈值/种子转成数值。
#   更改配置后需重新执行读取与赋值，旧变量不会自动刷新。
# 参数设置（下方为本次取值；不需要修改函数内部实现）：
# comparison_id：本次明确选取的比较 ID；示例用已启用比较中的第一个，不代表所有项目都有某个固定 ZT 名称。
# source_dir：字符路径；明确选择已完成的原结果目录，内部须有本函数要读取的 RDS/TSV。不会查找最近一次运行，也不从别的项目回退。
# redraw_dir：字符路径；保存重绘结果的新目录。原对象保持不动；相同目录参数冲突时用新目录或variant_label，不能靠覆盖隐藏差别。
# annotation：重绘时选择一个已有对象："GO_BP" 生物过程、"GO_MF" 分子功能、
#  "GO_CC" 细胞组分、"GO_ALL" 三类合并、"KEGG" 通路。
#  必须已经存在于所选来源的结果对象中；它不是下载数据库或补算本体的开关。
# result_style：单选 "raw" 或 "simplified"；与 annotation 一起选择已经保存的结果。
#  "raw"：通过筛选但未做 GO 语义去冗余；不是完整检验表，完整检验见 *_all_tests.tsv。
#  "simplified"：已有 GO 去冗余代表条目；KEGG 只使用 "raw"。
#  重绘不会补做 simplify，缺少对应对象时先核对来源，不能只改文件名。
# term_num：正整数向量；每种图最多展示的富集条目数，如 c(10,20) 各出 Top10/Top20，只取已有达标条目，不强行补足。要避免重算请选择重绘入口；
#   完整分析入口改此值仍会运行相应分析。
# pvalue_tables：逻辑向量，仅控制 Top1 富集曲线的附表版本，不控制 TopN 多曲线。
#  FALSE：Top1 不附 P 值表；TRUE：Top1 附表；c(FALSE, TRUE)：两版都保存。
#  logical()：不画 Top1 版本，但仍按 term_num 画 TopN；附表不代表重新检验。
# variant_label：一个文本标签，默认 "" 表示不加额外后缀；如 "large_font" 会给末级结果目录加 __large_font。
#  非空时只用字母、数字、点、下划线、短横线，首字符为字母或数字；不填路径、空格或 NA。
#  调整未进入目录名的图幅、字体等时用不同标签另存；标签本身不改变计算参数。
#  它不是强制覆盖开关：同一路径参数冲突仍停止，不修改旧结果清单。
# with(read_contrasts(), contrast_id[enabled][1])：先取 enabled=TRUE 的比较，再选第一个 ID；不是按 P值挑比较。
# 路径组合：file.path 按目录层级拼接；project_result 读取配置指定来源并核对存在，不查找最新目录。重绘来源与输出目录应分清。
# 调用：先加载脚本，再设置参数，最后运行函数。改值后重新执行赋值和调用。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/15_gsea_redraw.R")
comparison_id <- with(read_contrasts(), contrast_id[enabled][1])
source_dir <- file.path(project_result("GSEA_RESULT_ROOT", "9Enrichment_Analysis/GSEA"), comparison_id, "stat")
redraw_dir <- file.path(source_dir, "custom_top5")
annotation <- "GO_BP"
result_style <- "raw"
term_num <- 5
pvalue_tables <- c(FALSE, TRUE)
variant_label <- ""
# interface-parameters: gsea_redraw
run_gsea_redraw(
  comparison_id = comparison_id,
  source_dir = source_dir,
  redraw_dir = redraw_dir,
  annotation = annotation,
  result_style = result_style,
  term_num = term_num,
  pvalue_tables = pvalue_tables,
  variant_label = variant_label
)
```

### 查看本步关键文件

查看重绘所用的同一份显著条目；它不会因为 Top 数量变化而成为一次新的检验。

```r
# 目的：只读当前参数路径的关键文本；留在上一框的 R 会话，不重新分析。
# 前提：上一分析已成功或明确提示完整结果复用；若报错/冲突，先处理，不把旧文件当本次成功结果。
# preview_dir/preview_files 只用于查看，不是传给分析函数的新参数。
# file.path 拼接路径；readLines(n = 10) 最多读前 10 行，含表头；不整表读入内存。
# file.exists 检查是否存在；cat 用 sep = "\n" 逐行显示；warn = FALSE 省略末行换行提示。
# nzchar 判断标签是否非空；非空时按原命名规则在末级目录加 __标签。
preview_dir <- redraw_dir
if (nzchar(variant_label)) preview_dir <- paste0(preview_dir, "__", variant_label)
preview_files <- file.path(preview_dir, paste0(annotation, "_", result_style, ".tsv"))
for (preview_file in preview_files) {
  cat("\n文件：", preview_file, "\n")
  if (file.exists(preview_file)) {
    cat(readLines(preview_file, n = 10, warn = FALSE), sep = "\n")
  } else {
    cat("尚无此文件：核对上一步是否完成、是否选择该分析，以及空结果提示。\n")
  }
}
```

## 5. 输出和解读

`ranking.tsv` 是实际输入的完整排序；`all_tests` 保存本次调用返回的完整检验表，`raw` 为显著结果，GO 的 `simplified` 为去冗余版本。当前包会移除无法计算 P 值的条目，因此 `all_tests` 不能被解释为数据库全部条目；日志中的数值计算警告也必须一起阅读。每一种排序和每一个比较独立保存，不能混合它们的 NES 或校正 P 值。

保留原稿的 Top10/Top20 多曲线供整体查看；重叠过多时使用 Top1 图查看细节，或用点图比较 NES。单条曲线的峰值位置、命中刻度和排序指标共同帮助解释富集来源。显著集合的名称不等于已经证明某个过程被激活或抑制。

当显著条目不足 10/20 个时，只画实际条目，不补足数量。单曲线标题写出 GO/KEGG ID 与条目名，无 P 值表版本也能明确识别对象。修改这些显示设置后可读取 `GSEA_results.rds`，将其中的结果对象交给 `save_gsea_result()` 重绘，不需要重复 GSEA 检验。

这里的 `draw_dotplot`、`refresh_layout_only` 是底层 `save_gsea_result()` 的形参，不是上面的 `run_gsea_redraw()` 参数。顶层重绘入口目前固定保留点图；不要把这两个参数直接加进该顶层调用。需要只画曲线时，按已有对象接口调用 `save_gsea_result()` 并设 `draw_dotplot = FALSE`。`refresh_layout_only = TRUE` 只限制点图刷新为需要超过原 8 英寸高度的图，曲线和表格仍会写出，并非只读模式；须选择未占用的输出前缀。

## 6. 本次结果示例

ZT4_vs_ZT0 的去冗余前显著条目数如下，数字分别取自两种排序目录中的 `*_raw.tsv`。

| 检验集合 | log2FoldChange 排序 | Wald stat 排序 |
| --- | --- | --- |
| GO BP | 60 | 99 |
| GO MF | 10 | 8 |
| GO CC | 1 | 21 |
| GO ALL | 68 | 128 |
| KEGG | 11 | 26 |

log2FoldChange 排序下，`GO:1901659`（glycosyl compound biosynthetic process）的 NES 为 2.330，BH 校正 P 值约为 1.22 × 10⁻⁶。正 NES 表示其基因更偏向 ZT4 相对 ZT0 的排序上端；不是所有成员都上调，也不等于已经直接测量到合成通量增加。

![log2FoldChange 排序的 GO BP Top20 多条目曲线](../9Enrichment_Analysis/GSEA/ZT4_vs_ZT0/log2FoldChange/GO_BP_raw_top20_curves.png)

![同一结果的 GO BP Top20 NES 点图](../9Enrichment_Analysis/GSEA/ZT4_vs_ZT0/log2FoldChange/GO_BP_raw_top20_dotplot.png)

Wald 排序还突出 `response to water deprivation` 等条目。该名称来自基因功能注释，不表示本实验进行了干旱处理；仍需回到命中基因及真实的光周期实验背景解释。

![Wald 排序的 GO BP Top20 NES 点图](../9Enrichment_Analysis/GSEA/ZT4_vs_ZT0/stat/GO_BP_raw_top20_dotplot.png)

## 7. 数值警告与解释边界

本次主线日志出现部分通路 P 值可能被高估的提示，这是 fgsea 多层抽样估计的警告，不是下载失败，也不自动证明所有结果无效。[fgsea 的实现](https://github.com/alserglab/fgsea/blob/master/R/fgseaMultilevel.R)会把相关条目的误差估计 `log2err` 设为 NA；当前 clusterProfiler/DOSE 返回表不保留这一列。因此不能凭这里的表格反推每一个被警告条目的身份，也不应将近似 P 值当作精确概率。涉及关键结论时，应对相同排序与基因集单独保留后端诊断并检查稳定性，不能通过反复改变参数挑选更小的 P 值。

另一类警告是正负排序值失衡导致 P 值或 NES 无法计算，这与“得到一个不显著的有限 P 值”不同；若出现，应记录被遗漏的集合和原因，不补零或把 NA 改成显著。本次完整检查记录与实际日志一起保存。

下面仅对选定比较追加后端诊断，输入读取已保存的对象，不再查询注释，也不改动主结果。它使用相同的 fgsea 后端和参数，额外保留 `log2err`。这里复现的是 **DOSE 4.4.0** 的 `seed=TRUE` 调用行为；该版本会执行 `set.seed(.Random.seed)`，所以不能把入口种子数字直接理解为 fgsea 的最终随机种子。包版本变化时必须重新核对这一实现。

实现：[查看编号脚本](scripts/15_gsea_diagnostic_functions.R)。

<!-- execute: gsea_diagnostic_functions env=rnaseq -->
```r
# 目的：加载本节共用函数，供后面的分析/重绘入口调用；本段不启动统计或绘图。
# source("路径")：在当前 R 会话读取该脚本及它声明的共用依赖。路径相对项目根目录，不是下载地址。
# 输入：0script/scripts/15_gsea_diagnostic_functions.R；产物是 R 会话中的函数定义，不是结果文件。
# 修改脚本后需重新 source；仅加载函数不会自动更新已有结果，后面的参数赋值和调用仍须执行。

source("0script/scripts/15_gsea_diagnostic_functions.R")
```

下面自动选择比较表中第二个启用比较，不足两个时取第一个；本案例对应 ZT4_vs_ZT0。更换项目不需要在这里重新填写组名。也可以按研究问题从同一比较表选择其他 ID，不修改诊断函数的中间逻辑。下面的 `run_gsea_example_diagnostics()` 没有 `route` 形参，固定检查模式路线的这一个比较。非模式结果完成后用第 20 章的现成诊断入口；需要自选比较时，调用已定义的 `diagnose_saved_GSEA()`，明确传入 `route`（`main` 或 `diamond`）、`contrast_id`、`ranking` 和 `annotation`，不用改函数内部逻辑。该诊断会复算底层 fgsea 并核对原统计，不等于只读重绘。

实现：[查看编号脚本](scripts/15_gsea_example_diagnostics.R)。

<!-- execute: gsea_example_diagnostics env=rnaseq -->
```r
# 目的：选择启用列表中的第二个比较（不足两个时取第一个）做模式 GSEA 诊断。
# 关键输出：GSEA_RESULT_ROOT/比较ID/排序/diagnostics/注释类别/，内含 注释类别_backend.tsv、_warnings.txt、_check.tsv。
#   选择启用列表中第二个比较（不足两个取第一个）；会复算诊断统计，但不覆盖原 GSEA_results.rds。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：对该比较的 log2FoldChange/stat 两种排序的 GO_BP 调用底层复算诊断；不是遍历所有比较，原富集结果不覆盖。
# 共用读取：readRenviron 读取 project.env；Sys.getenv 返回文本，as.numeric/as.integer 将阈值/种子转成数值。
#   更改配置后需重新执行读取与赋值，旧变量不会自动刷新。
# 本入口没有可调形参；先 source 加载当前定义，再调用函数即可。输入来自本节说明的项目文件，不需要寻找一个并不存在的参数赋值段。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/15_gsea_example_diagnostics.R")
run_gsea_example_diagnostics()
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
preview_root <- project_result("GSEA_RESULT_ROOT", "9Enrichment_Analysis/GSEA")
preview_files <- c(
  file.path(preview_root, preview_id, "log2FoldChange/diagnostics/GO_BP/GO_BP_check.tsv"),
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

这些诊断只覆盖明确选中的检验集合，不能据此声称已经逐条核查所有比较的抽样误差。改变抽样精度属于另一次敏感性分析，应另存参数与结果，不能代替这里对原结果的可重复性核对。

本次两种排序的 GO BP 后端均返回 1,920 个集合，P 值、BH 校正值、ES 和 NES 与保存结果核对一致；这两次诊断没有非有限 P 值，也没有缺失的 `log2err`。它们不代表其他比较的警告可以忽略。
