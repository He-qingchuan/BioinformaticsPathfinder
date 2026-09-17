# 文件用途｜第 08 章：区分 GTF 映射、输入 FASTA 和 Salmon 目标三个范围。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：本文件运行入口没有形参，输入按下方读取语句来自项目文件。重新加载定义后直接调用，不需寻找额
#   外赋值段；文件编辑不会自动更新已经打开的 R 会话。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_reference_accounting：区分 GTF 映射、输入 FASTA 和 Salmon 目标三个范围。
# 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
# 返回/写出与边界：写 reference_scope_summary.tsv 及逐转录本范围表；仅核账，不能把参考范围差异等同于表
#   达缺失。
run_reference_accounting <- function() {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  mapping <- read.delim("1database/genome/tx2gene.tsv", check.names = FALSE)
  reference <- readLines(gzfile("1database/genome/transcripts.fa.gz"), warn = FALSE)
  reference_ids <- sub("[[:space:]].*$", "", substring(reference[startsWith(reference, ">")], 2))
  samples <- read_samples()
  quant <- read.delim(file.path("3Salmon", paste0(samples$sample_id[1], ".quant"), "quant.sf"), check.names = FALSE)
  stopifnot(!anyDuplicated(reference_ids), all(reference_ids %in% mapping$transcript_id),
            all(quant$Name %in% reference_ids))
  # 三个范围分别计转录本和去重基因；GTF 中存在但未纳入 cDNA 的记录不等于测得的零表达，索引目标去重也需独
  #   立解释。
  scope <- data.frame(
    scope = c("GTF_mapping", "input_transcript_FASTA", "Salmon_quantified_targets"),
    transcripts = c(nrow(mapping), length(reference_ids), nrow(quant)),
    genes = c(length(unique(mapping$gene_id)),
      length(unique(mapping$gene_id[match(reference_ids, mapping$transcript_id)])),
      length(unique(mapping$gene_id[match(quant$Name, mapping$transcript_id)]))))
  mapping$in_transcript_FASTA <- mapping$transcript_id %in% reference_ids
  mapping$in_Salmon_targets <- mapping$transcript_id %in% quant$Name
  write.table(scope, "3Salmon/quanti/reference_scope_summary.tsv", sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(mapping, "3Salmon/quanti/transcript_reference_accounting.tsv", sep = "\t", quote = FALSE, row.names = FALSE)
  print(scope)
}
