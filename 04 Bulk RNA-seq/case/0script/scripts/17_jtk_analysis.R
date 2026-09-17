# 文件用途｜第 17 章：用指定 MetaCycle 1.2.1 的 JTK 检验周期。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_jtk_analysis：用指定 MetaCycle 1.2.1 的 JTK 检验周期。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# input_dir（默认 project_result("JTK_INPUT_DIR", "10Time_Series/JTK_CYCLE")）：字符路径；含
#   JTK_input.tsv 与 JTK_sample_order.tsv 的已完成输入目录。修改过滤阈值后指向对应目录，不能只改周期参数
#   却沿用不明输入。
# minper（默认 20）：正数，单位小时；请求检验的最短周期。实际模板按采样间隔离散化，需查看
#   JTK_period_design.tsv，而不把请求值视为全部已检验周期。
# maxper（默认 28）：正数（小时），不小于 minper；请求最长周期，还受时间点数和间隔限制。增加范围不能补
#   出缺失的时间点或更多采样周期。
# fdr_cutoff（默认 0.05）：数值 (0,1]；周期候选要求 BH.Q 严格小于此阈值，并同时要求估计周期为有限正数
#   ；显著但周期无效的基因另存诊断表。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存实际周期模板、完整结果、有效候选及无效周期诊断；正周期且 BH.Q 严格达标才入候选
#   ，不把请求周期范围冒充实际模板。
run_jtk_analysis <- function(input_dir = project_result("JTK_INPUT_DIR", "10Time_Series/JTK_CYCLE"),
  minper = 20,
  maxper = 28,
  fdr_cutoff = 0.05,
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：用指定 MetaCycle/JTK 对已准备的输入检验周期；输出完整结果和筛选表。
  # minper/maxper 为请求小时范围，实际模板另存，不能把请求上限当成已检验上限。
  library(tidyverse)
  library(MetaCycle)
  readRenviron("0script/project.env")
  stopifnot(packageVersion("MetaCycle") == "1.2.1")
  set.seed(as.integer(Sys.getenv("RANDOM_SEED")))
  stopifnot(is.finite(minper), is.finite(maxper), minper > 0, maxper >= minper,
            fdr_cutoff > 0, fdr_cutoff <= 1)

  # 功能：核对离散周期模板，并调用 meta2d；保持重复列的顺序和指定 JTK 方法。
  samples <- read.delim(file.path(input_dir, "JTK_sample_order.tsv"), check.names = FALSE)
  input_file <- file.path(input_dir, "JTK_input.tsv")
  output_dir <- file.path("10Time_Series/JTK_CYCLE", parameter_tag(period = c(minper, maxper), fdr = fdr_cutoff))
  claim <- begin_result_stage(output_dir, list(minper = minper, maxper = maxper, fdr_cutoff = fdr_cutoff,
    # 配置来源 RANDOM_SEED：示例/模板默认 20260907；实际以 project.env 为准。
    seed = Sys.getenv("RANDOM_SEED"), MetaCycle = as.character(packageVersion("MetaCycle")),
    input_id_reading = "text_inDF"),
    list(expression = input_file, samples = samples), variant_label)
  output_dir <- claim$path
  # 保存本次真正采用的输入；这样绘图不依赖随后被更换的入口表。
  stopifnot(file.copy(input_file, file.path(output_dir, "JTK_input.tsv"), overwrite = FALSE))
  write.table(samples, file.path(output_dir, "JTK_sample_order.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  time_grid <- sort(unique(samples$time_hour))
  interval <- unique(diff(time_grid))
  supported_max <- min(maxper, length(time_grid) * interval)
  if (supported_max < minper || round(supported_max / interval) < 2) {
    stop("当前采样不足以检验指定周期范围，请重新考虑实验设计")
  }
  # 与 MetaCycle 1.2.1 的 runJTK 一致：按采样间隔 round，而不是向内取整。
  candidate_periods <- seq(max(2, round(minper / interval)), round(supported_max / interval)) * interval
  write.table(data.frame(requested_min = minper, requested_max = maxper,
                         sampling_interval = interval, effective_max = max(candidate_periods),
                         candidate_periods = paste(candidate_periods, collapse = ",")),
                file.path(output_dir, "JTK_period_design.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  # 从已校验的表传入同一组数值，避免 MetaCycle 的默认文件读取将 001 变为 1。
  # inDF 只改变读入方式，仍运行指定的 JTK 方法和同一采样参数。
  jtk_input <- read_result_table(input_file)
  stopifnot(identical(names(jtk_input)[-1], samples$sample_id),
            !anyDuplicated(jtk_input[[1]]))
  jtk_run <- MetaCycle::meta2d(infile = input_file, outdir = output_dir, filestyle = "txt",
    inDF = jtk_input,
    timepoints = samples$time_hour, minper = minper, maxper = maxper, cycMethod = "JTK",
    analysisStrategy = "selfUSE", outputFile = FALSE, outIntegration = "noIntegration",
    adjustPhase = "predictedPer", parallelize = FALSE)
  saveRDS(jtk_run, file.path(output_dir, "JTK_result_object.rds"))

  # 功能：将完整结果与“BH 达标且周期有效”的候选分开，保留无效周期诊断。
  # 改阈值只影响筛选，不强行为 PER=0 的基因填入一个正周期。
  jtk_result <- as.data.frame(jtk_run$JTK)
  q_column <- grep("BH.Q", names(jtk_result), value = TRUE)[1]
  period_column <- grep("^(PER|Period)", names(jtk_result), value = TRUE)[1]
  id_column <- grep("CycID", names(jtk_result), value = TRUE)[1]
  stopifnot(!anyNA(c(q_column, period_column, id_column)))
  jtk_result <- jtk_result[order(jtk_result[[q_column]], jtk_result[[id_column]]), , drop = FALSE]
  significant <- is.finite(jtk_result[[q_column]]) & jtk_result[[q_column]] < fdr_cutoff
  valid_period <- is.finite(jtk_result[[period_column]]) & jtk_result[[period_column]] > 0
  rhythmic <- jtk_result[significant & valid_period, , drop = FALSE]
  invalid_period <- jtk_result[significant & !valid_period, , drop = FALSE]
  write.table(jtk_result, file.path(output_dir, "JTK_results.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  threshold_tag <- gsub(".", "", format(fdr_cutoff, scientific = FALSE, trim = TRUE), fixed = TRUE)
  rhythmic_file <- paste0("JTK_rhythmic_BH", threshold_tag, ".tsv")
  write.table(rhythmic, file.path(output_dir, rhythmic_file), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(invalid_period, file.path(output_dir, "JTK_significant_invalid_period.tsv"),
                sep = "\t", quote = FALSE, row.names = FALSE)
  summary <- data.frame(tested = nrow(jtk_result), BH005_positive_period = nrow(rhythmic),
                         BH005_invalid_period = nrow(invalid_period))
  names(summary)[2:3] <- paste0("BH", threshold_tag, c("_positive_period", "_invalid_period"))
  write.table(summary, file.path(output_dir, "JTK_summary.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  saveRDS(list(fdr_cutoff = fdr_cutoff, rhythmic_file = rhythmic_file, minper = minper, maxper = maxper),
    file.path(output_dir, "JTK_analysis_parameters.rds"))
  finish_result_dir(claim)
  invisible(list(output_dir = output_dir))
}
