#!/usr/bin/env Rscript
# 功能：按列名读取已校验样本表，向 Bash 提供正确顺序的字段；不保存或改写样本表。
# 调用：Rscript 0script/tools/sample_columns.R sample_id read1 read2 [--nul]。位置参数是需要的列名，不
#   是列号。
# --nul：字段用 NUL 字节分隔，供 xargs -0 安全接收含空格文件名；省略按 TSV 输出，无表头。
# 从项目根目录运行；读取 samples.tsv，按是否请求 read1/read2 决定 fastq/matrix 字段校验。写标准输出，
#   不另存一份样本表。
# 本文件顶层执行命令，不是供 source 后再单独调用的函数库。

source("0script/tools/metadata.R")
args <- commandArgs(TRUE)
nul <- "--nul" %in% args
columns <- setdiff(args, "--nul")
if (!length(columns)) stop("请指定需要的列，例如 sample_id read1 read2")
samples <- read_samples(entry = if (any(c("read1", "read2") %in% columns)) "fastq" else "matrix")
require_columns(samples, columns, "样本表")
if (nul) {
  # Linux 命令行的二进制标准输出；file("stdout", "wb") 会误建名为 stdout 的文件。
  connection <- file("/dev/stdout", "wb", raw = TRUE)
  for (i in seq_len(nrow(samples))) for (field in columns)
    writeBin(c(charToRaw(as.character(samples[[field]][i])), as.raw(0)), connection)
  close(connection)
} else {
  write.table(samples[columns], stdout(), sep = "\t", quote = FALSE,
              row.names = FALSE, col.names = FALSE, na = "NA")
}
