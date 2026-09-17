# 文件用途｜第 18 章：核实选出的代表蛋白、转录本和基因一一对应。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：本文件运行入口没有形参，输入按下方读取语句来自项目文件。重新加载定义后直接调用，不需寻找额
#   外赋值段；文件编辑不会自动更新已经打开的 R 会话。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_representative_validation：核实选出的代表蛋白、转录本和基因一一对应。
# 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
# 返回/写出与边界：保存 validated_representatives.tsv、覆盖/选择核对信息；使用真实身份映射，不把人/鼠
#   蛋白 ID 当转录本 ID。
run_representative_validation <- function() {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  library(tidyverse)
  org_dir <- "9Enrichment_Analysis/OrgDb"
  map <- read.delim(file.path(org_dir, "representatives/longest_mapid.tsv"), check.names = FALSE)
  names(map)[1:2] <- c("transcript_id", "gene_id")
  stopifnot(nrow(map) > 0, !anyDuplicated(map$transcript_id), !anyDuplicated(map$gene_id))
  gtf <- read.delim("1database/genome/annotation.gtf.gz", header = FALSE,
                    sep = "\t", quote = "", comment.char = "#")
  exons <- gtf[gtf$V3 == "exon", , drop = FALSE]
  exons$transcript_id <- sub('.*transcript_id "([^"]+)".*', '\\1', exons$V9)
  exons$gene_id <- sub('.*gene_id "([^"]+)".*', '\\1', exons$V9)
  protein_ids <- readLines(file.path(org_dir, "representatives/protein_transcript_ids.txt"), warn = FALSE)
  exons <- exons[exons$transcript_id %in% protein_ids, , drop = FALSE]
  # 外显子坐标为包含两端的区间，因此长度 V5-V4+1；先去重复外显子，再逐转录本求成熟长度，在有明确蛋白对应
  #   的候选中核对最长者。
  lengths <- exons |> distinct(V1, V4, V5, V7, transcript_id, gene_id) |>
    mutate(exon_length = V5 - V4 + 1) |> group_by(gene_id, transcript_id) |>
    summarise(mature_transcript_length = sum(exon_length), .groups = "drop")
  maxima <- lengths |> group_by(gene_id) |> summarise(maximum_length = max(mature_transcript_length), .groups = "drop")
  selected <- map |> left_join(lengths, by = c("transcript_id", "gene_id")) |> left_join(maxima, by = "gene_id")
  stopifnot(!anyNA(selected$mature_transcript_length), all(selected$mature_transcript_length == selected$maximum_length))
  stopifnot(setequal(selected$gene_id, unique(lengths$gene_id)))
  headers <- readLines(file.path(org_dir, "representative_proteins.fa"), warn = FALSE)
  ids <- sub("^>", "", headers[startsWith(headers, ">")])
  stopifnot(!anyDuplicated(ids), setequal(ids, selected$gene_id))
  write.table(selected, file.path(org_dir, "representatives/validated_representatives.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  cat("代表基因/蛋白数:", length(ids), "\n")
}
