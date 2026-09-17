# 文件用途｜第 15 章：按比较和排序统计量批量运行模式物种 GSEA。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_gsea_analysis：按比较和排序统计量批量运行模式物种 GSEA。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# comparison_ids（默认 NULL）：字符向量或 NULL；NULL 读取比较表中的全部启用比较，指定 ID 则只处理这些
#   比较。ID 必须与 contrasts.tsv 和差异表一致，不从文件名猜组名。
# rankings（默认 c("log2FoldChange", "stat")）：字符向量；log2FoldChange 按效应量，stat 按带方向的
#   DESeq2 统计量排序，各自运行 GSEA。二者不是一张图的两种配色。
# term_num（默认 c(10, 20)）：正整数向量；每种图最多展示的富集条目数，如 c(10,20) 各出 Top10/Top20，只
#   取已有达标条目，不强行补足。要避免重算请选择重绘入口；完整分析入口改此值仍会运行相应分析。
# ontologies（默认 c("BP", "MF", "CC", "ALL")）：字符向量；BP 生物过程、MF 分子功能、CC 细胞组分、ALL
#   合并本体。可同时分析；改变本体会改变检验的条目集合，不只是换标题。
# include_kegg（默认 TRUE）：TRUE/FALSE；FALSE 跳过 KEGG。模式物种路线使用匹配物种/ID 类型，非模式路线
#   使用保存的通路对应表；不能借用另一物种的注释。
# fdr_cutoff（默认 as.numeric(Sys.getenv("FDR_CUTOFF"))）：数值阈值，通常 0.05，范围 (0,1]；控制当前步
#   骤的校正 P 值筛选，调小更严格。各比较/富集本体分别校正，不代表全项目共同做一次 BH。
# minGSSize（默认 10）：正整数；与输入/背景匹配后的基因集中允许的最少基因数。提高会排除较小条目，改变
#   参与检验的条目集合。
# maxGSSize（默认 500）：正整数，且不小于 minGSSize；允许的最大基因集规模。降低会排除过大的条目，改变
#   检验范围。
# simplify_cutoff（默认 0.75）：0–1 数值；GO 语义相似性去冗余门槛，不是 P 值。越低越容易将相似条目合并
#   ；原始 raw 结果仍单独保留，KEGG 不做这项 GO 简化。
# seed（默认 as.integer(Sys.getenv("RANDOM_SEED"))）：整数随机种子；用于需要随机过程的步骤，保持相同有
#   助于复现，不是采样时间。改变种子可能改变聚类、GSEA 或标签布局，需保留独立结果。
# draw_dotplot（默认 TRUE）：TRUE/FALSE；是否保存 GSEA 的点图；不控制富集曲线，也不重新检验通路。
# pvalue_tables（默认 c(FALSE, TRUE)）：逻辑向量；控制 Top1 富集曲线的无/有 P 值表版本，c(FALSE,TRUE)
#   两版，logical() 不画 Top1。多条目 TopN 由 term_num 独立控制。
# plot_dpi（默认 180）：正数，单位像素/英寸；PNG 的像素密度。相同英寸下越大像素越多、文件通常越大；PDF
#   的矢量图形不靠此值提高清晰度。
# output_root（默认 "9Enrichment_Analysis/GSEA"）：字符路径；本步骤输出根目录，函数再按比较/参数建立子
#   目录。通常沿用；试算可选新目录，但后续读取位置不会自动更新。
# kegg_keytype（默认 Sys.getenv("KEGG_KEYTYPE", "kegg")）：字符 ID 类型；传给模式物种 KEGG 接口，如
#   kegg。不同于 OrgDb 的 keyType；须与真实输入基因 ID 匹配，不会自动把 TAIR 改成人类 ID。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：每种 ranking 单独计算并保存；效应量排序与 stat 排序是两个分析选择，不是重复画同一套
#   图。
run_gsea_analysis <- function(comparison_ids = NULL,
  rankings = c("log2FoldChange", "stat"),
  term_num = c(10, 20),
  ontologies = c("BP", "MF", "CC", "ALL"),
  include_kegg = TRUE,
  fdr_cutoff = as.numeric(Sys.getenv("FDR_CUTOFF")),
  minGSSize = 10,
  maxGSSize = 500,
  simplify_cutoff = 0.75,
  seed = as.integer(Sys.getenv("RANDOM_SEED")),
  draw_dotplot = TRUE,
  pvalue_tables = c(FALSE, TRUE),
  plot_dpi = 180,
  output_root = "9Enrichment_Analysis/GSEA",
  kegg_keytype = Sys.getenv("KEGG_KEYTYPE", "kegg"),
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：载入维护的 GSEA 函数、输入表与官方注释。
  # 直接 source 编号函数脚本；不必先运行其他章节的批量分析。
  library(tidyverse)
  library(clusterProfiler)
  library(enrichplot)
  BiocParallel::register(BiocParallel::SerialParam())
  readRenviron("0script/project.env")
  source("0script/scripts/15_gsea_functions.R", local = TRUE)
  package <- Sys.getenv("ORGDB_PACKAGE")
  OrgDb_name <- get(package, envir = asNamespace(package))
  # 基因 ID 按文本保留，包括 NCBI 数字 ID；其余统计列仍正常读为数值。
  de_result <- read.delim(project_result("DE_RESULT_FILE", "5DESeq2/de_result.tsv"),
    check.names = FALSE, colClasses = c(gene_id = "character", contrast_id = "character"))
  contrasts <- read_contrasts() |>
    filter(toupper(as.character(enabled)) == "TRUE")
  stopifnot(nrow(contrasts) > 0)

  # 功能：设置分析范围和图形选项；只需一个排序时把 rankings 改成一个名称。
  # term_num、draw_dotplot、pvalue_tables 只管展示；排名/集合大小改变则需重做检验。
  if (is.null(comparison_ids)) comparison_ids <- contrasts$contrast_id

  # 功能：比较与排序两层循环只负责组织调用，具体参数全部来自上方入口。
  stopifnot(all(comparison_ids %in% contrasts$contrast_id), all(rankings %in% names(de_result)))
  for (id in comparison_ids) {
    for (ranking_column in rankings) {
      plot_GSEA(de_result = de_result, contrast_id = id, ranking_column = ranking_column,
        # 配置来源 ORGDB_KEYTYPE：案例 TAIR；空模板 空；实际以 project.env 为准。
        OrgDb_name = OrgDb_name, keyType = Sys.getenv("ORGDB_KEYTYPE"),
        # 配置来源 KEGG_ORGANISM：案例 ath；空模板 空；实际以 project.env 为准。
        organism_name = Sys.getenv("KEGG_ORGANISM"), fdr_cutoff = fdr_cutoff,
        seed = seed, term_num = term_num, ontologies = ontologies, include_kegg = include_kegg,
        minGSSize = minGSSize, maxGSSize = maxGSSize, simplify_cutoff = simplify_cutoff,
        draw_dotplot = draw_dotplot, pvalue_tables = pvalue_tables,
        plot_dpi = plot_dpi, output_root = output_root,
        kegg_keytype = kegg_keytype, variant_label = variant_label)
    }
  }
  invisible(list(output_root = output_root))
}
