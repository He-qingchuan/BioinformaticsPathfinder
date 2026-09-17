# 文件用途｜第 18 章：从已保存 DIAMOND 注释重画覆盖率概览。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_diamond_coverage：从已保存 DIAMOND 注释重画覆盖率概览。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# width（默认 10）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
# height（默认 6）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
# dpi（默认 180）：正数，单位像素/英寸；控制 PNG 像素密度，不改变图幅的英寸数或统计结果。
# plot_output_dir（默认 NULL）：NULL 或字符路径；NULL 沿用注释 output 目录，给新路径可另存覆盖率图片。
#   注意覆盖率 TSV 仍写原注释 output 目录。
# 返回/写出与边界：调用覆盖率函数写表与图，不重做注释搜索；仅图目录由 plot_output_dir 控制，原注释统计
#   表仍会写出。
run_diamond_coverage <- function(width = 10,
  height = 6,
  dpi = 180,
  plot_output_dir = NULL) {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：载入覆盖率绘图函数，从既有注释重画覆盖图，不重新搜索或建库。
  library(tidyverse)
  library(AnnotationDbi)
  source("0script/scripts/18_orgdb_builder.R", local = TRUE)
  # 功能：只重绘覆盖率；图幅为英寸，PNG 像素密度由 dpi 控制。
  # 改参试绘可将 plot_output_dir 设为 diamond/output/custom_coverage。
  plot_annotation_coverage(method = "diamond", width = width, height = height,
    dpi = dpi, plot_output_dir = plot_output_dir)
  invisible(list(plot_output_dir = plot_output_dir))
}
