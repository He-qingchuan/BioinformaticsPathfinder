# 文件用途｜第 16 章：读取一个已有聚类组合调整标记基因和 GO 侧栏。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_time_redraw：读取一个已有聚类组合调整标记基因和 GO 侧栏。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# source_dir（默认 file.path(project_result("TIME_RESULT_ROOT", "10Time_Series"),      "
#   top_var_prop_0.1/Clusters_num_6", Sys.getenv("TIME_VARIANT_DIR",          ""))）：字符路径；明确选择
#   已完成的原结果目录，内部须有本函数要读取的 RDS/TSV。不会查找最近一次运行，也不从别的项目回退。
# redraw_dir（默认 file.path(source_dir, "custom_labels20_terms10")）：字符路径；保存重绘结果的新目录
#   。原对象保持不动；相同目录参数冲突时用新目录或 variant_label，不能靠覆盖隐藏差别。
# markGenes_num（默认 20）：非负整数；从本组合已选高变基因中优先标记的总数，不是每模块各 N 个，0 不标
#   记。只重绘用本章重绘入口；完整聚类入口改它仍可能执行整步。
# enrichment_top_n（默认 10）：正整数；每个模块图上最多展示的 GO 条目数，不是标记基因数，只显示通过
#   enrichment_fdr 的条目。重绘入口可不重算；完整分析入口改此值仍会执行相应分析步骤。
# enrichment_fdr（默认 0.05）：数值 (0,1]；模块富集图取 p.adjust 不大于此值的 GO 条目，每个模块的检验
#   先完成 BH。没有达标条目时显示明确空结果提示。
# go_versions（默认 TRUE）：逻辑向量；FALSE 不附 GO 侧栏，TRUE 附上已有模块 GO 结果。不能用 TRUE 代替
#   实际计算富集。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：另存重绘，不重新运行 Mfuzz/富集；若请求 GO 却缺少保存富集输入则停止。
run_time_redraw <- function(source_dir = file.path(project_result("TIME_RESULT_ROOT", "10Time_Series"),
    "top_var_prop_0.1/Clusters_num_6", Sys.getenv("TIME_VARIANT_DIR", "")),
  redraw_dir = file.path(source_dir, "custom_labels20_terms10"),
  markGenes_num = 20,
  enrichment_top_n = 10,
  enrichment_fdr = 0.05,
  go_versions = TRUE,
  variant_label = "") {
  # 功能：从已完成组合重绘，不重新计算 Mfuzz 或富集检验。
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  readRenviron("0script/project.env")
  # 参数：markGenes_num 取当前组合 selected_genes.tsv 中的前 N 个；不能跨组合取标签。
  library(tidyverse)
  library(ClusterGVis)
  library(clusterProfiler)
  source("0script/scripts/16_time_functions.R", local = TRUE)
  cm <- readRDS(file.path(source_dir, "cluster_object.rds"))
  selected <- read_result_table(file.path(source_dir, "selected_genes.tsv"))
  markGenes <- head(selected$gene_id, markGenes_num)
  stopifnot(is.logical(go_versions), length(go_versions) > 0, !anyNA(go_versions))
  enrichment_file <- file.path(source_dir, "cluster_enrichment_BH.tsv")
  if (any(go_versions) && !file.exists(enrichment_file))
    stop("没有已有模块富集表；仅改聚类标签请设 go_versions = FALSE，不能把未检验写成无显著条目")
  enrichment_bh <- if (any(go_versions)) read.delim(enrichment_file) else data.frame()
  claim <- begin_result_stage(redraw_dir,
    list(markGenes_num = markGenes_num, enrichment_top_n = enrichment_top_n,
      enrichment_fdr = enrichment_fdr, line_variants = character(), label_versions = TRUE, go_versions = go_versions),
    list(cluster = cm, selected = selected, enrichment = enrichment_bh), variant_label)
  redraw_dir <- claim$path
  render_cluster_variants(
    cm = cm, markGenes = markGenes, enrichment_bh = enrichment_bh, output_dir = redraw_dir,
    enrichment_top_n = enrichment_top_n, enrichment_fdr = enrichment_fdr,
    line_variants = character(), label_versions = TRUE, go_versions = go_versions
  )
  writeLines(markGenes, file.path(redraw_dir, "marked_genes.txt"))
  finish_result_dir(claim)
  invisible(list(output_dir = redraw_dir))
}
