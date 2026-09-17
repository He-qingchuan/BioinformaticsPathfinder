# 文件用途｜第 19 章：枚举已有聚类组合调用非模式模块 GO 分析。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_diamond_modules：枚举已有聚类组合调用非模式模块 GO 分析。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# top_var_props（默认 c(0.1, 0.2)）：比例向量 (0,1]；用于定位第 16 章已经完成的高变基因组合，如 c(0.1,
#   0.2)。这里不重新挑选基因/聚类，所列组合必须有匹配的保存对象。
# cluster_numbers（默认 6:10）：整数向量，元素至少 2；第 16 章逐一运行这些 Mfuzz 聚类数，第 19 章读取
#   对应已有组合；选中基因数须足够。
# markGenes_num（默认 NULL）：非负整数；优先标记的高变基因数量，总数而非每个模块各 N 个。0 不标基因；
#   第 19 章允许 NULL 沿用保存名单，不改变聚类成员。
# enrichment_top_n（默认 5）：正整数；每个模块图上最多展示的 GO 条目数，不是标记基因数，只显示通过
#   enrichment_fdr 的条目。重绘入口可不重算；完整分析入口改此值仍会执行相应分析步骤。
# enrichment_fdr（默认 0.05）：数值 (0,1]；模块富集图取 p.adjust 不大于此值的 GO 条目，每个模块的检验
#   先完成 BH。没有达标条目时显示明确空结果提示。
# enrich_type（默认 "BP"）：单个 BP、MF、CC 或 ALL；指定模块 GO 富集的本体，改变时需要相应富集结果，不
#   能只重写图标题。
# minGSSize（默认 10）：正整数；与输入/背景匹配后的基因集中允许的最少基因数。提高会排除较小条目，改变
#   参与检验的条目集合。
# maxGSSize（默认 500）：正整数，且不小于 minGSSize；允许的最大基因集规模。降低会排除过大的条目，改变
#   检验范围。
# label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示已选标记基因标签，TRUE 显示，c(FALSE,
#   TRUE) 保存两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
# label_size（默认 10）：正数；时间聚类热图中标记基因的字号，通常从 10 调整，经 genes.gp 传给绘图函数
#   ；不改变标签名单或聚类结果。
# cluster_root（默认 project_result("TIME_RESULT_ROOT", "10Time_Series")）：字符路径；已完成的第 16 章
#   聚类根目录，配合比例、模块数、cluster_variant 定位保存对象。不是本步新聚类的输出。
# cluster_variant（默认 Sys.getenv("TIME_VARIANT_DIR", "")）：字符末级目录名；对应第 16 章已有
#   mark/GOtop/seed 变体，无此层的旧结果留空，按真实路径填写，不自动猜选。
# output_root（默认 "9Enrichment_Analysis/OrgDb/diamond/module_enrichment"）：字符路径；本步骤输出根目
#   录，函数再按比较/参数建立子目录。通常沿用；试算可选新目录，但后续读取位置不会自动更新。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：复用第 16 章 cluster_object.rds，输出支线富集和图片；展示参数与原模块成员分开记录。
run_diamond_modules <- function(top_var_props = c(0.1, 0.2),
  cluster_numbers = 6:10,
  markGenes_num = NULL,
  enrichment_top_n = 5,
  enrichment_fdr = 0.05,
  enrich_type = "BP",
  minGSSize = 10,
  maxGSSize = 500,
  label_versions = c(FALSE, TRUE),
  label_size = 10,
  cluster_root = project_result("TIME_RESULT_ROOT", "10Time_Series"),
  cluster_variant = Sys.getenv("TIME_VARIANT_DIR", ""),
  output_root = "9Enrichment_Analysis/OrgDb/diamond/module_enrichment",
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：载入模块富集函数；随后的入口和调用段在同一时间分析环境执行。
  library(tidyverse)
  library(ClusterGVis)
  library(clusterProfiler)
  source("0script/scripts/16_time_functions.R", local = TRUE)
  source("0script/scripts/19_nonmodel_ora_functions.R", local = TRUE)
  source("0script/scripts/19_nonmodel_module_functions.R", local = TRUE)

  # 功能：选择已有时间组合和显示参数；只分析一个组合时分别改为 0.2 和 8。

  # 功能：调用自建模块富集，参数继续传到第 16 章的富集/面板函数。
  plot_nonmodel_modules(method = "diamond", top_var_props = top_var_props, cluster_numbers = cluster_numbers,
    markGenes_num = markGenes_num, enrichment_top_n = enrichment_top_n, enrichment_fdr = enrichment_fdr,
    enrich_type = enrich_type, minGSSize = minGSSize, maxGSSize = maxGSSize,
    label_versions = label_versions, label_size = label_size, cluster_root = cluster_root, output_root = output_root,
    cluster_variant = cluster_variant, variant_label = variant_label)
  invisible(list(output_root = output_root))
}
