# 文件用途｜第 16 章：按真实小时汇总组均值并准备聚类 log2 表。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_time_input：按真实小时汇总组均值并准备聚类 log2 表。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# tpm_threshold（默认 1）：非负 TPM；先按样本表分组求重复均值，保留至少一个时期均值严格大于阈值的基因
#   ，再取 log2(TPM+1)。不是周期入口的中位数过滤。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存组均值、过滤和 log2 输入及来源；不直接聚类，过滤改变后需明确选择新
#   TIME_INPUT_FILE。
run_time_input <- function(tpm_threshold = 1,
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：从各时期重复计算平均 TPM，生成聚类输入；不改变原始 TPM 矩阵。
  # 参数：tpm_threshold 为表达过滤阈值，过滤在取 log 和行标准化之前。
  # 输出：10Time_Series 下的均值、log2 输入、方差和时间设计表。
  library(tidyverse)
  readRenviron("0script/project.env")
  samples <- read_samples(use_time = "time")
  ordered_groups(samples, require_time = TRUE)
  gene_tpm <- as.data.frame(read_expression(project_result("TPM_MATRIX", "3Salmon/quanti/gene.TPM.not_cross_norm"), read_samples()), check.names = FALSE)
  stopifnot(!anyDuplicated(rownames(gene_tpm)), all(samples$sample_id %in% names(gene_tpm)))
  time_design <- samples |> distinct(timepoint, time_hour) |> arrange(time_hour)
  stopifnot(nrow(time_design) == n_distinct(samples$timepoint), all(is.finite(time_design$time_hour)),
            !anyDuplicated(time_design$time_hour))
  time_levels <- time_design$timepoint
  gene_exp_avg <- vapply(time_levels, function(group) {
    rowMeans(gene_tpm[, samples$sample_id[samples$timepoint == group], drop = FALSE])
  }, numeric(nrow(gene_tpm)))
  rownames(gene_exp_avg) <- rownames(gene_tpm)
  stopifnot(length(tpm_threshold) == 1, is.finite(tpm_threshold), tpm_threshold >= 0)
  keep <- apply(gene_exp_avg, 1, max) > tpm_threshold
  exps_log <- log2(gene_exp_avg[keep, , drop = FALSE] + 1)
  gene_variance <- apply(exps_log, 1, var)
  stopifnot(all(is.finite(gene_variance)))
  exps_log <- exps_log[gene_variance > 0, , drop = FALSE]
  gene_variance <- gene_variance[gene_variance > 0]
  # output_root：本次计算/绘图的输出根目录；与 project.env 中读取既有结果的 *_RESULT_ROOT 区分。
  output_root <- file.path("10Time_Series", paste0("input_tpm", tpm_threshold))
  claim <- begin_result_stage(output_root, list(tpm_threshold = tpm_threshold),
    list(expression = gene_tpm, samples = samples), variant_label)
  output_root <- claim$path
  write.table(data.frame(gene_id = rownames(gene_exp_avg), gene_exp_avg, check.names = FALSE),
              file.path(output_root, "mean_TPM.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(data.frame(gene_id = rownames(exps_log), exps_log, check.names = FALSE),
              file.path(output_root, "clustering_input_log2.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(data.frame(gene_id = names(gene_variance), variance_before_standardisation = gene_variance),
              file.path(output_root, "gene_variance.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(time_design, file.path(output_root, "time_design.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  finish_result_dir(claim)
  invisible(list(output_root = output_root))
}
