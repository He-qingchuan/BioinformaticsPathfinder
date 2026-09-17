# 文件用途｜第 19 章：批量执行 DIAMOND 自建注释的非模式 ORA。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_diamond_ora：批量执行 DIAMOND 自建注释的非模式 ORA。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# comparison_ids（默认 NULL）：字符向量或 NULL；NULL 读取比较表中的全部启用比较，指定 ID 则只处理这些
#   比较。ID 必须与 contrasts.tsv 和差异表一致，不从文件名猜组名。
# term_num（默认 c(10, 20)）：正整数向量；每种图最多展示的富集条目数，如 c(10,20) 各出 Top10/Top20，只
#   取已有达标条目，不强行补足。要避免重算请选择重绘入口；完整分析入口改此值仍会运行相应分析。
# directions（默认 c("all", "up", "down")）：字符向量；all 为已判为 up/down 的差异基因并集，up/down 各
#   取对应方向。读取差异表已保存的 direction，不把 all 理解为全部被检验基因。
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
# go_qvalue（默认 0.05）：0–1 数值；GO ORA 的 q-value 筛选设置，另于 fdr_cutoff 的 BH/p.adjust 门槛。
#   不是图中条目数量，也不用于 GSEA。
# kegg_qvalue（默认 0.2）：0–1 数值；KEGG ORA 的 q-value 筛选设置，独立于 BH 门槛；改它会影响保留的通
#   路。
# plot_styles（默认 c("bar", "dot")）：字符向量；bar 条形图与 dot 点图，可同时保存。使用同一个富集结果
#   对象，不重新检验。
# plot_width（默认 10）：正数，单位英寸；输出图宽。增大可缓解标签拥挤，不改变统计筛选。
# plot_dpi（默认 180）：正数，单位像素/英寸；PNG 的像素密度。相同英寸下越大像素越多、文件通常越大；PDF
#   的矢量图形不靠此值提高清晰度。
# overview_dpi（默认 150）：正数，像素/英寸；多面板富集综合图的 PNG 密度，与单张图的 plot_dpi 独立。
# output_root（默认 "9Enrichment_Analysis/OrgDb/diamond/ORA"）：字符路径；本步骤输出根目录，函数再按比
#   较/参数建立子目录。通常沿用；试算可选新目录，但后续读取位置不会自动更新。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存于支线 ORA 根目录，不重做第 18 章蛋白注释，也不覆盖模式物种 ORA。
run_diamond_ora <- function(comparison_ids = NULL,
  term_num = c(10, 20),
  directions = c("all", "up", "down"),
  ontologies = c("BP", "MF", "CC", "ALL"),
  include_kegg = TRUE,
  fdr_cutoff = as.numeric(Sys.getenv("FDR_CUTOFF")),
  minGSSize = 10,
  maxGSSize = 500,
  simplify_cutoff = 0.75,
  go_qvalue = 0.05,
  kegg_qvalue = 0.2,
  plot_styles = c("bar", "dot"),
  plot_width = 10,
  plot_dpi = 180,
  overview_dpi = 150,
  output_root = "9Enrichment_Analysis/OrgDb/diamond/ORA",
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：加载自建 ORA 所需函数和包，准备读取本章入口设置。
  # 首次先执行第 14 章 ora_functions 和本章 nonmodel_ora_functions。
  library(tidyverse)
  library(clusterProfiler)
  library(enrichplot)
  library(patchwork)
  source("0script/scripts/14_ora_functions.R", local = TRUE)
  source("0script/scripts/19_nonmodel_ora_functions.R", local = TRUE)
  readRenviron("0script/project.env")

  # 功能：设置本支线的 ORA 参数，随后完整传入函数。
  # 默认所有启用比较；指定一个比较可写 comparison_ids <- "ZT4_vs_ZT0"（本案例）。

  # 功能：运行入口选定范围；主函数和绘图子函数收到的是同一组参数。
  plot_nonmodel_ORA(method = "diamond", comparison_ids = comparison_ids,
    term_num = term_num, directions = directions, ontologies = ontologies, include_kegg = include_kegg,
    fdr_cutoff = fdr_cutoff, minGSSize = minGSSize, maxGSSize = maxGSSize,
    simplify_cutoff = simplify_cutoff, go_qvalue = go_qvalue, kegg_qvalue = kegg_qvalue,
    plot_styles = plot_styles, plot_width = plot_width, plot_dpi = plot_dpi, overview_dpi = overview_dpi,
    output_root = output_root, variant_label = variant_label)
  invisible(list(output_root = output_root))
}
