# 文件用途｜第 08 章：规范已有 Trinity 表的样本列并汇总定量概览。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：本文件运行入口没有形参，输入按下方读取语句来自项目文件。重新加载定义后直接调用，不需寻找额
#   外赋值段；文件编辑不会自动更新已经打开的 R 会话。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_matrix_summary：规范已有 Trinity 表的样本列并汇总定量概览。
# 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
# 返回/写出与边界：写通用 counts/TPM/TMM 表、库级汇总与图，保留原 Trinity 输出；不重新定量，主要产物为
#   文件。
run_matrix_summary <- function() {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  library(ggplot2)
  library(jsonlite)
  samples <- read_samples()
  # 三种表使用同一批基因/样本，但数值尺度不同：counts 用于差异建模，TPM 用于时间输入，TMM 用于样本关系和
  #   热图，不能互相改后缀冒充。
  matrix_suffixes <- c("counts.matrix", "TPM.not_cross_norm", "TMM.EXPR.matrix")
  for (suffix in matrix_suffixes) {
    path <- file.path("3Salmon/quanti", paste0("genes.gene.", suffix))
    # 首列 ID 按文本保留，其余表达值按数值读取。
    matrix <- read_result_table(path, row_names = TRUE)
    names(matrix) <- sub("\\.quant$", "", names(matrix))
    stopifnot(setequal(names(matrix), samples$sample_id), !anyDuplicated(rownames(matrix)))
    matrix <- matrix[, samples$sample_id, drop = FALSE]
    stopifnot(all(is.finite(as.matrix(matrix))), all(as.matrix(matrix) >= 0))
    # 通用入口保留同一行列集合，原始 Trinity 输出仍保留供核对。
    write.table(cbind(gene_id = rownames(matrix), matrix),
                file.path("3Salmon/quanti", paste0("gene.", suffix)),
                sep = "\t", quote = FALSE, row.names = FALSE)
  }
  counts <- as.data.frame(read_expression(project_result("COUNT_MATRIX", "3Salmon/quanti/gene.counts.matrix"), read_samples()), check.names = FALSE)
  tpm <- as.data.frame(read_expression(project_result("TPM_MATRIX", "3Salmon/quanti/gene.TPM.not_cross_norm"), read_samples()), check.names = FALSE)
  stopifnot(identical(dimnames(counts), dimnames(tpm)))
  # 文库量统计使用估计 fragments 的列和，表达基因数使用 TPM>1；图中除以 1e6 仅将单位换为百万。
  summary <- data.frame(sample_id = samples$sample_id, estimated_fragments = colSums(counts),
                        genes_TPM_gt1 = colSums(tpm > 1))
  mapping <- do.call(rbind, lapply(samples$sample_id, function(id) {
    info <- fromJSON(file.path("3Salmon", paste0(id, ".quant"), "aux_info/meta_info.json"))
    data.frame(sample_id = id, num_processed = info$num_processed,
               num_mapped = info$num_mapped, percent_mapped = info$percent_mapped,
               library_types = paste(info$library_types, collapse = ";"))
  }))
  write.table(summary, "3Salmon/quanti/matrix_summary.tsv", sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(mapping, "3Salmon/quanti/mapping_summary.tsv", sep = "\t", quote = FALSE, row.names = FALSE)

  overview <- ggplot(summary, aes(factor(sample_id, levels = samples$sample_id), estimated_fragments / 1e6)) +
    geom_col(fill = "#216B87") + coord_flip() +
    labs(x = NULL, y = "Estimated fragments (millions)", title = "Library-level quantified fragments") +
    theme_classic(base_size = 11)
  ggsave("3Salmon/quanti/matrix_overview.png", overview, width = 9, height = 7, dpi = 180)
  ggsave("3Salmon/quanti/matrix_overview.pdf", overview, width = 9, height = 7)
  print(dim(counts))
}
