# 文件用途｜第 16 章：枚举保留比例与模块数并调用时间聚类流程。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_time_clustering：枚举保留比例与模块数并调用时间聚类流程。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# include_module_enrichment（默认 FALSE）：TRUE/FALSE；是否计算聚类模块 GO 富集。FALSE 可只做聚类，并
#   关闭带 GO 注释的图，不能在未计算富集时把空白当无显著结果。
# top_var_props（默认 c(0.1, 0.2)）：数值向量，范围 (0,1]；按过滤后的时间表达矩阵基因方差分别保留前若
#   干比例，0.1 为高变异的 10%。每个比例与每个模块数组合单独分析，不是去除比例。
# cluster_numbers（默认 6:10）：整数向量，元素至少 2；第 16 章逐一运行这些 Mfuzz 聚类数，第 19 章读取
#   对应已有组合；选中基因数须足够。
# markGenes_num（默认 30）：非负整数；从本组合已选高变基因中优先标记的总数，不是每模块各 N 个，0 不标
#   记。只重绘用本章重绘入口；完整聚类入口改它仍可能执行整步。
# enrichment_top_n（默认 5）：正整数；每个模块图上最多展示的 GO 条目数，不是标记基因数，只显示通过
#   enrichment_fdr 的条目。重绘入口可不重算；完整分析入口改此值仍会执行相应分析步骤。
# compatibility_top_n（默认 5）：正整数；原 ClusterGVis::enrichCluster 兼容展示表的 Top 数，独立于主图
#   BH 表的 enrichment_top_n。该兼容表不替代主图的多重校正结果。
# enrichment_fdr（默认 0.05）：数值 (0,1]；模块富集图取 p.adjust 不大于此值的 GO 条目，每个模块的检验
#   先完成 BH。没有达标条目时显示明确空结果提示。
# enrich_type（默认 "BP"）：单个 BP、MF、CC 或 ALL；指定模块 GO 富集的本体，改变时需要相应富集结果，不
#   能只重写图标题。
# minGSSize（默认 10）：正整数；与输入/背景匹配后的基因集中允许的最少基因数。提高会排除较小条目，改变
#   参与检验的条目集合。
# maxGSSize（默认 500）：正整数，且不小于 minGSSize；允许的最大基因集规模。降低会排除过大的条目，改变
#   检验范围。
# seed（默认 as.integer(Sys.getenv("RANDOM_SEED"))）：整数随机种子；用于需要随机过程的步骤，保持相同有
#   助于复现，不是采样时间。改变种子可能改变聚类、GSEA 或标签布局，需保留独立结果。
# input_file（默认 project_result("TIME_INPUT_FILE", "10Time_Series/clustering_input_log2.tsv")）：字
#   符路径；当前步骤使用的已准备输入文件。时间聚类读取第 16 章输出的 log2 矩阵，不用原 counts 直接替代。
# output_root（默认 "10Time_Series"）：字符路径；本步骤输出根目录，函数再按比较/参数建立子目录。通常沿
#   用；试算可选新目录，但后续读取位置不会自动更新。
# line_variants（默认 c("line1", "line2", "line3")）：字符向量；line1、line2、line3 对应三种
#   ClusterGVis 时间曲线展示，line3 不加模块中位数线；character() 跳过独立曲线，不改变聚类。
# label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示已选标记基因标签，TRUE 显示，c(FALSE,
#   TRUE) 保存两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
# go_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不附 GO 侧栏，TRUE 附上已有模块 GO 结果。不能用
#   TRUE 代替实际计算富集。
# label_size（默认 10）：正数；时间聚类热图中标记基因的字号，通常从 10 调整，经 genes.gp 传给绘图函数
#   ；不改变标签名单或聚类结果。
# heatmap_width（默认 NULL）：NULL 或正数（英寸）；NULL 根据是否有 GO 侧栏采用自动宽度，数值用于手动图
#   宽，不影响聚类或显著性。
# heatmap_height（默认 NULL）：NULL 或正数（英寸）；NULL 根据模块数和 GO 展示量估算高度，数值用于手动
#   图高。条目多时增高可减少拥挤。
# heatmap_dpi（默认 130）：正数，像素/英寸；时间热图 PNG 的输出密度，不改变行标准化、模块或 GO 筛选。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：每个比例×模块数组合独立保存；include_module_enrichment=FALSE 仍做聚类，但不虚构 GO
#   注释。
run_time_clustering <- function(include_module_enrichment = FALSE,
  top_var_props = c(0.1, 0.2),
  cluster_numbers = 6:10,
  markGenes_num = 30,
  enrichment_top_n = 5,
  compatibility_top_n = 5,
  enrichment_fdr = 0.05,
  enrich_type = "BP",
  minGSSize = 10,
  maxGSSize = 500,
  seed = as.integer(Sys.getenv("RANDOM_SEED")),
  input_file = project_result("TIME_INPUT_FILE", "10Time_Series/clustering_input_log2.tsv"),
  output_root = "10Time_Series",
  line_variants = c("line1", "line2", "line3"),
  label_versions = c(FALSE, TRUE),
  go_versions = c(FALSE, TRUE),
  label_size = 10,
  heatmap_width = NULL,
  heatmap_height = NULL,
  heatmap_dpi = 130,
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：载入维护函数，按需准备官方 OrgDb；后续调用时才执行聚类。
  # 首次使用先运行 time_functions；自动任务间不共享 R 内存，故显式 source。
  library(tidyverse)
  library(ClusterGVis)
  library(clusterProfiler)
  readRenviron("0script/project.env")
  stopifnot(packageVersion("ClusterGVis") == "0.1.2")
  source("0script/scripts/16_time_functions.R", local = TRUE)
  package <- Sys.getenv("ORGDB_PACKAGE")
  OrgDb_name <- if (include_module_enrichment) get(package, envir = asNamespace(package)) else NULL

  # 功能：接收第 16 章 MD 已设定的组合；这里仅传递参数，不在循环内部另改比例或模块数。
  # 默认 2 个比例 × 5 个模块数 = 10 个组合；只跑一个时在 MD 入口分别设为 0.2 和 8。

  # 功能：逐个组合运行；所有可调参数均显式传入，没有在循环内固定另一个数值。
  for (top_var_prop in top_var_props) {
    for (Clusters_num in cluster_numbers) {
      plot_Time_Series(top_var_prop = top_var_prop, Clusters_num = Clusters_num,
        markGenes_num = markGenes_num, OrgDb_name = OrgDb_name, enrich_type = enrich_type,
        # 配置来源 ORGDB_KEYTYPE：案例 TAIR；空模板 空；实际以 project.env 为准。
        # 配置来源 KEGG_ORGANISM：案例 ath；空模板 空；实际以 project.env 为准。
        Gene_id_type = Sys.getenv("ORGDB_KEYTYPE"), organism_name = Sys.getenv("KEGG_ORGANISM"),
        input_file = input_file, output_root = output_root, seed = seed,
        enrichment_top_n = enrichment_top_n, enrichment_fdr = enrichment_fdr,
        compatibility_top_n = compatibility_top_n, minGSSize = minGSSize, maxGSSize = maxGSSize,
        line_variants = line_variants, label_versions = label_versions, go_versions = go_versions,
        label_size = label_size, heatmap_width = heatmap_width,
        heatmap_height = heatmap_height, heatmap_dpi = heatmap_dpi,
        include_module_enrichment = include_module_enrichment, variant_label = variant_label)
    }
  }
  invisible(list(output_root = output_root))
}
