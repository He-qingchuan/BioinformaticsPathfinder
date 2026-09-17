# 文件用途｜第 17 章：过滤 TPM 后准备保留重复的等间隔 JTK 输入。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_jtk_input：过滤 TPM 后准备保留重复的等间隔 JTK 输入。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# tpm_threshold（默认 0.5）：非负 TPM；先计算所有时期各组内中位数，保留其中最大值严格大于阈值的基因，
#   再按 cycle_use 选周期时点；最终仍保留各重复列。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存全部时期过滤表、JTK_sample_order.tsv/JTK_input.tsv；要求至少四个等间隔时期且重
#   复数相同、每时点至少两个。
run_jtk_input <- function(tpm_threshold = 0.5,
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：按全部时期中位数 TPM 过滤，再选择等间隔时期；重复列不合并。
  # 参数：tpm_threshold 改变进入检验的基因集合，需与后面的统计结果对应。
  output_dir <- file.path("10Time_Series/JTK_CYCLE", paste0("input_tpm", tpm_threshold))
  stopifnot(length(tpm_threshold) == 1, is.finite(tpm_threshold), tpm_threshold >= 0)
  library(tidyverse)
  samples_all <- read_samples(use_time = "time", cycle = TRUE)
  ordered_groups(samples_all, require_time = TRUE)
  gene_tpm <- as.data.frame(read_expression(project_result("TPM_MATRIX", "3Salmon/quanti/gene.TPM.not_cross_norm"), read_samples()), check.names = FALSE)
  stopifnot(!anyDuplicated(rownames(gene_tpm)), all(samples_all$sample_id %in% names(gene_tpm)))
  design_all <- samples_all |> distinct(timepoint, time_hour) |> arrange(time_hour)
  stopifnot(nrow(design_all) == n_distinct(samples_all$timepoint), all(is.finite(design_all$time_hour)),
            !anyDuplicated(design_all$time_hour))
  median_by_time <- vapply(design_all$timepoint, function(group) {
    ids <- samples_all$sample_id[samples_all$timepoint == group]
    apply(gene_tpm[, ids, drop = FALSE], 1, median)
  }, numeric(nrow(gene_tpm)))
  rownames(median_by_time) <- rownames(gene_tpm)
  keep_gene <- apply(median_by_time, 1, max) > tpm_threshold
  samples <- samples_all |> filter(toupper(as.character(cycle_use)) == "TRUE") |>
    arrange(time_hour, replicate)
  time_grid <- sort(unique(samples$time_hour))
  if (length(time_grid) < 4 || any(!is.finite(time_grid)) ||
      length(unique(round(diff(time_grid), 10))) != 1) {
    stop("cycle_use=TRUE 必须至少包含四个等间隔时期，请修改入口样本表而不是重写中间代码")
  }
  replicate_counts <- table(samples$time_hour)
  stopifnot(length(unique(replicate_counts)) == 1, all(replicate_counts >= 2))
  log_tpm <- log2(as.matrix(gene_tpm[keep_gene, samples$sample_id, drop = FALSE]) + 1)
  stopifnot(nrow(log_tpm) > 0, all(is.finite(log_tpm)))
  claim <- begin_result_stage(output_dir, list(tpm_threshold = tpm_threshold),
    list(expression = gene_tpm, samples = samples_all), variant_label)
  output_dir <- claim$path
  write.table(data.frame(gene_id = rownames(median_by_time), median_by_time, retained = keep_gene, check.names = FALSE),
                file.path(output_dir, "prefilter_all_timepoints.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(samples, file.path(output_dir, "JTK_sample_order.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(data.frame(CycID = rownames(log_tpm), log_tpm, check.names = FALSE),
                file.path(output_dir, "JTK_input.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  cat("过滤时期:", paste(design_all$timepoint, collapse = ", "), "\n")
  cat("周期检验时期:", paste(time_grid, collapse = ", "), "；保留基因:", nrow(log_tpm), "\n")
  finish_result_dir(claim)
  invisible(list(output_dir = output_dir))
}
