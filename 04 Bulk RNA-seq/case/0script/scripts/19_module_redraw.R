# 文件用途｜第 19 章：将匹配的聚类对象和非模式富集表组合重绘。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_module_redraw：将匹配的聚类对象和非模式富集表组合重绘。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# combination（默认 "top_var_prop_0.1/Clusters_num_6"）：字符相对路径；一个已有比例/模块数组合，如
#   top_var_prop_0.1/Clusters_num_6，用于使聚类和富集来源指向同一组合。
# cluster_source_dir（默认 file.path(project_result("TIME_RESULT_ROOT", "10Time_Series"),
#   combination)）：字符路径；某个比例/模块数组合的聚类目录，尚未拼接 cluster_variant，内含所需聚类对象
#   与选中基因表。
# cluster_variant（默认 Sys.getenv("TIME_VARIANT_DIR", "")）：字符末级目录名；对应第 16 章已有
#   mark/GOtop/seed 变体，无此层的旧结果留空，按真实路径填写，不自动猜选。
# enrichment_source_dir（默认 file.path(project_result("NONMODEL_MODULE_RESULT_ROOT", "
#   9Enrichment_Analysis/OrgDb/diamond/module_enrichment"),      combination)）：字符路径；与所选聚类组
#   合对应的非模式模块富集目录，尚未拼接 enrichment_variant。不能混用不同模块成员的富集表。
# enrichment_variant（默认 Sys.getenv("NONMODEL_MODULE_VARIANT_DIR", "")）：字符末级目录名；指向已保存
#   非模式模块富集变体，旧结果无此层可空，不等同 cluster_variant。
# redraw_dir（默认 NULL）：字符路径；保存重绘结果的新目录。原对象保持不动；相同目录参数冲突时用新目录
#   或 variant_label，不能靠覆盖隐藏差别。
# markGenes_num（默认 20）：非负整数；优先标记的高变基因数量，总数而非每个模块各 N 个。0 不标基因；第
#   19 章允许 NULL 沿用保存名单，不改变聚类成员。
# enrichment_top_n（默认 10）：正整数；每个模块图上最多展示的 GO 条目数，不是标记基因数，只显示通过
#   enrichment_fdr 的条目。重绘入口可不重算；完整分析入口改此值仍会执行相应分析步骤。
# enrichment_fdr（默认 0.05）：数值 (0,1]；模块富集图取 p.adjust 不大于此值的 GO 条目，每个模块的检验
#   先完成 BH。没有达标条目时显示明确空结果提示。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：新图写 redraw_dir，不重算聚类或富集；cluster_variant 与 enrichment_variant 必须分别
#   对应真实来源。
run_module_redraw <- function(combination = "top_var_prop_0.1/Clusters_num_6",
  cluster_source_dir = file.path(project_result("TIME_RESULT_ROOT", "10Time_Series"), combination),
  cluster_variant = Sys.getenv("TIME_VARIANT_DIR", ""),
  enrichment_source_dir = file.path(project_result("NONMODEL_MODULE_RESULT_ROOT",
  "9Enrichment_Analysis/OrgDb/diamond/module_enrichment"), combination),
  enrichment_variant = Sys.getenv("NONMODEL_MODULE_VARIANT_DIR", ""),
  redraw_dir = NULL,
  markGenes_num = 20,
  enrichment_top_n = 10,
  enrichment_fdr = 0.05,
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：从同一套已有聚类和 DIAMOND 模块富集表重绘，不重做聚类或检验。
  # 在项目根目录运行；先 source scripts/16_time_functions.R 加载维护函数；不需要重做第 16 章分析。
  library(tidyverse)
  library(ClusterGVis)
  library(clusterProfiler)
  source("0script/scripts/16_time_functions.R", local = TRUE)
  if (nzchar(cluster_variant)) cluster_source_dir <- file.path(cluster_source_dir, cluster_variant)
  if (nzchar(enrichment_variant)) enrichment_source_dir <- file.path(enrichment_source_dir, enrichment_variant)
  if (is.null(redraw_dir)) redraw_dir <- file.path(enrichment_source_dir, "custom_labels20_terms10")
  # enrichment_fdr：本节局部的模块富集 BH 阈值，不自动引用 project.env 的 FDR_CUTOFF。
  cm <- readRDS(file.path(cluster_source_dir, "cluster_object.rds"))
  selected <- read_result_table(file.path(cluster_source_dir, "selected_genes.tsv"))
  enrichment_bh <- read.delim(file.path(enrichment_source_dir, "cluster_enrichment_BH.tsv"))
  claim <- begin_result_stage(redraw_dir,
    list(markGenes_num = markGenes_num, enrichment_top_n = enrichment_top_n,
      enrichment_fdr = enrichment_fdr, line_variants = character(), label_versions = TRUE, go_versions = TRUE),
    list(cluster = file.path(cluster_source_dir, "cluster_object.rds"), selected = selected,
      enrichment = enrichment_bh), variant_label)
  redraw_dir <- claim$path
  writeLines(head(selected$gene_id, markGenes_num), file.path(redraw_dir, "marked_genes.txt"))
  render_cluster_variants(
    cm = cm, markGenes = head(selected$gene_id, markGenes_num),
    enrichment_bh = enrichment_bh, output_dir = redraw_dir,
    enrichment_top_n = enrichment_top_n, enrichment_fdr = enrichment_fdr,
    line_variants = character(), label_versions = TRUE, go_versions = TRUE
  )
  finish_result_dir(claim)
  invisible(list(output_dir = redraw_dir))
}
