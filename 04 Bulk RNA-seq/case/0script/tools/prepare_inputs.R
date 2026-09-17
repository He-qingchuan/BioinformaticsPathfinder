#!/usr/bin/env Rscript
# 功能：校验已有样本表，可生成规范候选表/比较表；不下载数据、不改统计模型。
# 调用：conda run -n rnaseq Rscript 0script/tools/prepare_inputs.R [选项]；工作目录为项目根目录。
# --samples：输入表路径，默认 0script/samples.tsv；--entry：fastq/matrix，缺省读 DATA_ENTRY。
# --strategy：baseline、adjacent、baseline_and_adjacent；--reference：baseline 类所需真实参照组。
# --matrix：指定一个需要核对的矩阵路径；重复提供时以后一个值为准，不是累加。省略时矩阵入口检查配置中已
#   有的矩阵。只检查结构，不把 TPM 转 counts。
# --check-only：仅校验，不生成正式或候选表；缺比较表会提示，不凭空推断对照组。
# 本文件顶层直接执行命令，不作为只定义函数的库 source。写出候选后仍需明确采用，不能把候选误认为正式输
#   入。

source("0script/tools/metadata.R")
if (file.exists("0script/project.env")) readRenviron("0script/project.env")
args <- commandArgs(TRUE)
options <- list(samples = "0script/samples.tsv", entry = Sys.getenv("DATA_ENTRY", "matrix"),
                strategy = "baseline",
                reference = "", matrix = "", `check-only` = FALSE)
i <- 1L
while (i <= length(args)) {
  key <- sub("^--", "", args[i])
  if (key == "check-only") { options[[key]] <- TRUE; i <- i + 1L; next }
  if (!key %in% names(options) || i == length(args))
    input_error("用法：Rscript 0script/tools/prepare_inputs.R [--samples 文件] [--entry matrix|fastq] [--strategy baseline|adjacent|baseline_and_adjacent] [--reference 组名] [--matrix 文件] [--check-only]")
  options[[key]] <- args[i + 1L]; i <- i + 2L
}
samples <- read_samples(options$samples, entry = options$entry, check_files = options$entry == "fastq")
if (options$`check-only`) {
  if (file.exists("0script/contrasts.tsv")) read_contrasts(samples = samples)
  cat("样本/已提供的比较表检查通过：", nrow(samples), "个文库；", length(unique(samples$timepoint)), "个组别。\n")
  if (!file.exists("0script/contrasts.tsv")) cat("尚无正式比较表；差异分析前需要生成并核对。\n")
  # 矩阵入口至少检查一个真实矩阵。按名称匹配列，不因列序不同而错误配组。
  if (nzchar(options$matrix)) {
    matrices <- options$matrix
  } else if (options$entry == "matrix") {
    configured <- Sys.getenv(c("COUNT_MATRIX", "TPM_MATRIX", "TMM_MATRIX"))
    matrices <- unique(configured[nzchar(configured) & file.exists(configured)])
    if (!length(matrices)) input_error("矩阵入口尚无可检查的矩阵；填写 project.env 的矩阵路径，或传入 --matrix 文件")
  } else matrices <- character()
  for (path in matrices) {
    values <- read_expression(path, samples)
    cat("矩阵检查通过：", path, "；", nrow(values), "个基因。\n")
  }
  cat("这项检查不替代参考/注释检查，也不能从数字自动识别 counts、TPM 或标准化值；请核对矩阵来源及当前步骤的尺度要求。\n")
  quit(status = 0L)
}
if (normalizePath(options$samples) != normalizePath("0script/samples.tsv", mustWork = FALSE)) {
  write_generated_table(samples, "0script/samples.tsv")
  # 若已有正式样本表，导入只形成候选，不能用候选样本自动改变正式比较。
  if (file.exists("0script/samples.generated.tsv")) {
    cat("样本候选表已生成；请先核对并明确采用，暂不生成与正式样本不一致的比较表。\n")
    quit(status = 0L)
  }
}
contrasts <- generate_contrasts(samples, options$strategy, options$reference)
print(contrasts, row.names = FALSE)
write_generated_table(contrasts, "0script/contrasts.tsv")
cat("正 log2FC = test_group 相对 reference_group 更高；候选表不会自动替代正式表。\n")
