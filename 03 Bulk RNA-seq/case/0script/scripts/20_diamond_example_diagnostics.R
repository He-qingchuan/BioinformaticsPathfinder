# 文件用途｜第 20 章：选择启用列表中第二个比较（不足两个时取第一个）做非模式 GSEA 诊断。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：本文件运行入口没有形参，输入按下方读取语句来自项目文件。重新加载定义后直接调用，不需寻找额
#   外赋值段；文件编辑不会自动更新已经打开的 R 会话。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_diamond_example_diagnostics：选择启用列表中第二个比较（不足两个时取第一个）做非模式 GSEA
#   诊断。
# 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
# 返回/写出与边界：读取保存对象，对 log2FoldChange/GO_CC 与 stat/GO_BP 两组底层 fgsea 复算核对；会计算
#   诊断统计，但不重写原结果、不放宽阈值。
run_diamond_example_diagnostics <- function() {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  library(tidyverse)
  library(clusterProfiler)
  library(BiocParallel)
  source("0script/scripts/15_gsea_diagnostic_functions.R", local = TRUE)
  comparisons <- read_contrasts()
  comparisons <- comparisons[toupper(as.character(comparisons$enabled)) == "TRUE", ]
  stopifnot(nrow(comparisons) > 0)
  diagnostic_id <- comparisons$contrast_id[min(2, nrow(comparisons))]
  diagnose_saved_GSEA("diamond", diagnostic_id, "log2FoldChange", "GO_CC")
  diagnose_saved_GSEA("diamond", diagnostic_id, "stat", "GO_BP")
}
