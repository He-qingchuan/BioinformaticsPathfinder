# 文件用途｜第 08 章：核对各样本定量目标一致并整理 Trinity 所需映射。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：本文件运行入口没有形参，输入按下方读取语句来自项目文件。重新加载定义后直接调用，不需寻找额
#   外赋值段；文件编辑不会自动更新已经打开的 R 会话。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_mapping：核对各样本定量目标一致并整理 Trinity 所需映射。
# 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
# 返回/写出与边界：写 gene_trans_map.tsv、quant_files.txt 和未定量参考转录本表；不把未进入参考的基因伪
#   装为零表达，后续从文件衔接。
run_mapping <- function() {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  samples <- read_samples()
  tx2gene <- read.delim("1database/genome/tx2gene.tsv", check.names = FALSE)
  stopifnot(!anyDuplicated(samples$sample_id), !anyDuplicated(tx2gene$transcript_id))
  quant_files <- file.path("3Salmon", paste0(samples$sample_id, ".quant"), "quant.sf")
  stopifnot(all(file.exists(quant_files)))
  # 汇总前确认每个样本 quant.sf 使用相同目标及顺序；否则不同索引/参考不能拼成看似完整的一张表达矩阵。
  transcript_sets <- lapply(quant_files, function(path) read.delim(path, check.names = FALSE)$Name)
  stopifnot(all(vapply(transcript_sets, identical, logical(1), transcript_sets[[1]])))
  present <- transcript_sets[[1]]
  missing <- setdiff(present, tx2gene$transcript_id)
  if (length(missing)) stop("定量转录本缺少 gene_id 映射: ", paste(head(missing), collapse = ", "))
  # 按真实定量 ID 匹配映射，再导出 Trinity 要求的 gene_id 在前、transcript_id 在后且无表头的格式。
  map <- tx2gene[match(present, tx2gene$transcript_id), c("gene_id", "transcript_id")]
  dir.create("3Salmon/quanti", recursive = TRUE, showWarnings = FALSE)
  write.table(map, "3Salmon/quanti/gene_trans_map.tsv", sep = "\t", quote = FALSE,
              col.names = FALSE, row.names = FALSE)
  write.table(tx2gene[!tx2gene$transcript_id %in% present, , drop = FALSE],
              "3Salmon/quanti/reference_transcripts_not_quantified.tsv", sep = "\t",
              quote = FALSE, row.names = FALSE)
  writeLines(quant_files, "3Salmon/quanti/quant_files.txt")
  cat("参考映射:", nrow(tx2gene), " 定量转录本:", nrow(map),
      " 定量基因:", length(unique(map$gene_id)), "\n")
}
