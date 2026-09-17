# 文件用途｜第 06 章：从 fastp JSON 汇总过滤前后的质量变化并画图。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_qc_summary：从 fastp JSON 汇总过滤前后的质量变化并画图。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# plot_width（默认 9）：正数，单位英寸；输出图宽。增大可缓解标签拥挤，不改变统计筛选。
# plot_height（默认 7）：正数，单位英寸；输出图高。增大可容纳更多面板，不改变数据或显著性。
# plot_dpi（默认 180）：正数，单位像素/英寸；PNG 的像素密度。相同英寸下越大像素越多、文件通常越大；PDF
#   的矢量图形不靠此值提高清晰度。
# 返回/写出与边界：保存清洗汇总表与保留率/Q30 两类图的 PNG/PDF；不重新读取 FastQC，不重跑 fastp，也不
#   改过滤阈值。主要产物为文件。
run_qc_summary <- function(plot_width = 9,
  plot_height = 7,
  plot_dpi = 180) {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：读取 fastp JSON，比较 reads、bases 和质量统计并保存图表。
  # 不重新过滤；reads 保留率与碱基保留率分开计算，不用 Q30 高低自动判定样本优劣。
  library(jsonlite)
  library(ggplot2)
  samples <- read_samples()
  qc_summary <- do.call(rbind, lapply(samples$sample_id, function(id) {
    x <- fromJSON(file.path("2data/cleandata/fastp", paste0(id, ".fp.json")))
    before <- x$summary$before_filtering
    after <- x$summary$after_filtering
    stopifnot(after$total_reads > 0, after$total_reads <= before$total_reads)
    constant_q30 <- before$q30_bases == before$total_bases &&
      all(x$read1_before_filtering$quality_curves$mean == 30) &&
      all(x$read2_before_filtering$quality_curves$mean == 30)
    data.frame(sample_id = id, reads_before = before$total_reads, reads_after = after$total_reads,
               retention = after$total_reads / before$total_reads,
               bases_before = before$total_bases, bases_after = after$total_bases,
               base_retention = after$total_bases / before$total_bases,
               adapter_trimmed_reads = x$adapter_cutting$adapter_trimmed_reads,
               adapter_trimmed_bases = x$adapter_cutting$adapter_trimmed_bases,
               q30_before = before$q30_rate, q30_after = after$q30_rate,
               constant_q30_input = constant_q30)
  }))
  write.table(qc_summary, "2data/cleandata/qc_summary.tsv", sep = "\t", quote = FALSE, row.names = FALSE)

  # 功能：将已提取的 JSON 统计画成保留率与 Q30 对照；不重复读取或过滤 FASTQ。
  # plot_width/height/dpi 来自前段入口；两类质量统计分别显示，不合并为一个评分。
  qc_summary$sample_id <- factor(qc_summary$sample_id, levels = samples$sample_id)
  retention_plot <- ggplot(qc_summary, aes(sample_id, 100 * retention)) +
    geom_col(fill = "#216B87") + coord_flip() +
    scale_y_continuous(limits = c(0, 100)) +
    labs(x = NULL, y = "Retained reads (%)", title = "Read retention after fastp") +
    theme_classic(base_size = 11)
  q30_data <- rbind(data.frame(sample_id = qc_summary$sample_id, stage = "Raw", q30 = qc_summary$q30_before),
                    data.frame(sample_id = qc_summary$sample_id, stage = "Clean", q30 = qc_summary$q30_after))
  q30_plot <- ggplot(q30_data, aes(sample_id, 100 * q30, colour = stage, shape = stage)) +
    geom_point(size = 2) + coord_flip() +
    scale_colour_manual(values = c(Raw = "#C77C3D", Clean = "#216B87")) +
    labs(x = NULL, y = "Q30 bases (%)", colour = NULL, shape = NULL,
         caption = "Some input libraries have uniform Q30 scores; 100% does not establish superior base quality.") +
    theme_classic(base_size = 11)
  ggsave("2data/cleandata/read_retention.png", retention_plot, width = plot_width, height = plot_height, dpi = plot_dpi)
  ggsave("2data/cleandata/read_retention.pdf", retention_plot, width = plot_width, height = plot_height)
  ggsave("2data/cleandata/q30_comparison.png", q30_plot, width = plot_width, height = plot_height, dpi = plot_dpi)
  ggsave("2data/cleandata/q30_comparison.pdf", q30_plot, width = plot_width, height = plot_height)
}
