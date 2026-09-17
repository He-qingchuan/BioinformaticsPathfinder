# 文件用途｜第 14 章：只读取指定 ORA 对象重新安排 Top 条目展示。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_ora_redraw：只读取指定 ORA 对象重新安排 Top 条目展示。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# comparison_id（默认 with(read_contrasts(), contrast_id[enabled][1])）：一个已启用比较 ID 字符串；选
#   择要分析/重绘的比较，必须与所选结果来源对应。
# source_dir（默认 file.path(project_result("ORA_RESULT_ROOT", "9Enrichment_Analysis/ORA"),
#   comparison_id, "up")）：字符路径；明确选择已完成的原结果目录，内部须有本函数要读取的 RDS/TSV。不会查
#   找最近一次运行，也不从别的项目回退。
# redraw_dir（默认 file.path(source_dir, "custom_top15")）：字符路径；保存重绘结果的新目录。原对象保持
#   不动；相同目录参数冲突时用新目录或 variant_label，不能靠覆盖隐藏差别。
# term_num（默认 15）：正整数向量；每种图最多展示的富集条目数，如 c(10,20) 各出 Top10/Top20，只取已有
#   达标条目，不强行补足。要避免重算请选择重绘入口；完整分析入口改此值仍会运行相应分析。
# annotation（默认 "GO_BP"）：注释对象名称，如 GO_BP、GO_MF、GO_CC、GO_ALL 或 KEGG；必须是所选目录已经
#   保存的对象。
# result_style（默认 "raw"）：字符值 raw 或 simplified；GO 可选择原始/去冗余对象，KEGG 使用 raw。只是
#   读取已有对应对象，不在重绘阶段重新 simplify。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：重绘另存，不重新富集、不访问在线 KEGG 获取新检验；来源对象不存在会停止。
run_ora_redraw <- function(comparison_id = with(read_contrasts(), contrast_id[enabled][1]),
  source_dir = file.path(project_result("ORA_RESULT_ROOT", "9Enrichment_Analysis/ORA"), comparison_id, "up"),
  redraw_dir = file.path(source_dir, "custom_top15"),
  term_num = 15,
  annotation = "GO_BP",
  result_style = "raw",
  variant_label = "") {
  # 功能：准备独立重绘会话，读取项目的明确结果来源。
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：从已保存的对象重绘一个检验集合，不访问 KEGG、不重复统计检验。
  # 在项目根目录运行；从比较表选择一个来源，不需加载官方 OrgDb 或原始差异矩阵。
  # source 编号的 ORA 函数文件即可，不需要启动整个 ora_analysis。
  library(tidyverse)
  library(clusterProfiler)
  library(enrichplot)
  library(patchwork)
  source("0script/scripts/14_ora_functions.R", local = TRUE)
  # source_dir 选择实际存在的比较/方向目录；非模式路线改成其独立 ORA 目录。
  saved <- readRDS(file.path(source_dir, "ORA_results.rds"))
  stopifnot(annotation %in% names(saved$results), result_style %in% names(saved$results[[annotation]]))
  claim <- begin_result_stage(redraw_dir,
    list(term_num = term_num, annotation = annotation, result_style = result_style,
      plot_styles = c("bar", "dot"), width = 10, dpi = 180),
    list(statistical_object = file.path(source_dir, "ORA_results.rds")), variant_label)
  redraw_dir <- claim$path
  save_enrichment_plot(object = saved$results[[annotation]][[result_style]],
    title = paste(basename(dirname(source_dir)), basename(source_dir), annotation),
    prefix = file.path(redraw_dir, paste0(annotation, "_", result_style, "_top", term_num)),
    term_num = term_num, plot_styles = c("bar", "dot"), width = 10, dpi = 180)
  finish_result_dir(claim)
}
