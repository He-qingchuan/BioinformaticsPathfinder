# 文件用途｜第 17 章：从已有周期检验结果画周期分布和候选曲线。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_jtk_plots：从已有周期检验结果画周期分布和候选曲线。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# legacy_file（默认 ""）：字符文件名；仅旧结果缺少 JTK_analysis_parameters.rds 时使用的候选表名，位于
#   所选 JTK 结果目录中。有参数记录时优先读取记录。
# legacy_fdr（默认 NA_real_）：数值 (0,1]；仅兼容旧 JTK 结果的阈值说明。有保存参数时读取其实际阈值；不
#   能仅改变它就声称重新完成周期筛选。
# output_dir（默认 project_result("JTK_RESULT_ROOT", "10Time_Series/JTK_CYCLE")）：字符路径；虽然沿用
#   output_dir 名称，这里首先是已完成 JTK 检验的读取目录（JTK_RESULT_ROOT），新图写其 plots 子目录；不能
#   填任意空目录。
# top_genes（默认 12）：正整数；周期曲线最多展示的基因数，优先用已有有效周期候选。无达标候选时诊断曲线
#   会明确注明，不把展示基因当成已证实节律。
# facet_columns（默认 4）：正整数；每行曲线面板的列数。只影响排版，应配合图宽/图高，不改变基因检验结果。
# plot_width（默认 12）：正数，单位英寸；输出图宽。增大可缓解标签拥挤，不改变统计筛选。
# plot_height（默认 8）：正数，单位英寸；输出图高。增大可容纳更多面板，不改变数据或显著性。
# plot_dpi（默认 180）：正数，单位像素/英寸；PNG 的像素密度。相同英寸下越大像素越多、文件通常越大；PDF
#   的矢量图形不靠此值提高清晰度。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：把图及展示数据写 JTK 结果下的 plots 子目录；无有效周期显著基因时明确给出诊断说明，
#   不重新检验。
run_jtk_plots <- function(legacy_file = "",
  legacy_fdr = NA_real_,
  output_dir = project_result("JTK_RESULT_ROOT", "10Time_Series/JTK_CYCLE"),
  top_genes = 12,
  facet_columns = 4,
  plot_width = 12,
  plot_height = 8,
  plot_dpi = 180,
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：只从已保存的输入/检验结果绘图，不重新运行 meta2d。
  # 改 top_genes 或排版参数只需运行本节，且应另设 plot_output_dir 保留原图。
  library(tidyverse)
  stopifnot(top_genes >= 1, top_genes == floor(top_genes), facet_columns >= 1,
            facet_columns == floor(facet_columns), plot_width > 0, plot_height > 0, plot_dpi > 0)
  # 旧结果必须在入口明确声明旧阈值和文件，不自动猜测或选择其他项目。
  parameter_file <- file.path(output_dir, "JTK_analysis_parameters.rds")
  parameters <- if (file.exists(parameter_file)) readRDS(parameter_file) else {
    if (!nzchar(legacy_file) || !is.finite(legacy_fdr)) stop("旧结果缺少参数记录；请在本章参数入口填写 legacy_file 和 legacy_fdr")
    list(fdr_cutoff = legacy_fdr, rhythmic_file = legacy_file)
  }
  samples <- read.delim(file.path(output_dir, "JTK_sample_order.tsv"), check.names = FALSE)
  log_tpm <- read_result_table(file.path(output_dir, "JTK_input.tsv"), row_names = TRUE)
  result <- read_result_table(file.path(output_dir, "JTK_results.tsv"))
  rhythmic <- read_result_table(file.path(output_dir, parameters$rhythmic_file))
  plot_output_dir <- file.path(output_dir, "plots", parameter_tag(top = top_genes, facets = facet_columns))
  claim <- begin_result_stage(plot_output_dir,
    list(top_genes = top_genes, facet_columns = facet_columns, plot_width = plot_width,
      plot_height = plot_height, plot_dpi = plot_dpi, analysis = parameters),
    list(samples = samples, expression = log_tpm, results = result, rhythmic = rhythmic), variant_label)
  plot_output_dir <- claim$path
  id_column <- grep("CycID", names(result), value = TRUE)[1]
  period_column <- grep("^(PER|Period)", names(result), value = TRUE)[1]
  ids <- head(if (nrow(rhythmic)) rhythmic[[id_column]] else result[[id_column]], top_genes)
  caption <- if (nrow(rhythmic)) paste("BH <", parameters$fdr_cutoff, "with a positive period; one-window candidates") else
    "No BH-significant positive-period genes; leading candidates only"
  profiles <- log_tpm[ids, , drop = FALSE] |> rownames_to_column("gene_id") |>
    pivot_longer(-gene_id, names_to = "sample_id", values_to = "log_expression") |>
    left_join(samples[c("sample_id", "time_hour", "replicate")], by = "sample_id")
  plot <- ggplot(profiles, aes(time_hour, log_expression, group = gene_id)) +
    geom_point(color = "#216B87", alpha = 0.55, size = 1.3) +
    stat_summary(fun = mean, geom = "line", color = "#B7444F", linewidth = 0.8) +
    facet_wrap(~gene_id, scales = "free_y", ncol = facet_columns) +
    scale_x_continuous(breaks = sort(unique(samples$time_hour))) +
    labs(x = "Sampling time (h)", y = "log2(TPM + 1)", caption = caption) + theme_classic(base_size = 10)
  ggsave(file.path(plot_output_dir, "JTK_top_profiles.pdf"), plot, width = plot_width, height = plot_height)
  ggsave(file.path(plot_output_dir, "JTK_top_profiles.png"), plot, width = plot_width, height = plot_height, dpi = plot_dpi)
  period_plot <- if (nrow(rhythmic)) {
    ggplot(rhythmic, aes(factor(.data[[period_column]]))) + geom_bar(fill = "#216B87") +
      labs(x = "Estimated period (h)", y = "Candidate genes") + theme_classic(base_size = 12)
  } else {
    ggplot() + annotate("text", x = 0, y = 0, label = "No BH-significant positive-period genes") + theme_void()
  }
  ggsave(file.path(plot_output_dir, "JTK_period_distribution.pdf"), period_plot, width = 7, height = 5)
  ggsave(file.path(plot_output_dir, "JTK_period_distribution.png"), period_plot, width = 7, height = 5, dpi = plot_dpi)
  write.table(data.frame(gene_id = ids), file.path(plot_output_dir, "displayed_genes.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(profiles, file.path(plot_output_dir, "displayed_profiles.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  finish_result_dir(claim)
  invisible(list(output_dir = output_dir, plot_output_dir = plot_output_dir))
}
