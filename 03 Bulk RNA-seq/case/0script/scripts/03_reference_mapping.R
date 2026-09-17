# 文件用途｜第 03 章：校验参考文件并生成实际 FASTA ID 对应的转录本—基因表。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_reference_mapping：校验参考文件并生成实际 FASTA ID 对应的转录本—基因表。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# reference_dir（默认 "1database/genome"）：字符路径；统一参考目录，包含 genome.fa.gz、
#   transcripts.fa.gz、annotation.gtf.gz。更换物种替换真实文件，不必改变这些通用名称。
# 返回/写出与边界：返回含 reference_dir 的不可见 list；写 tx2gene.tsv/reference_summary.tsv，遇参考冲
#   突停止，不改原始参考。
run_reference_mapping <- function(reference_dir = "1database/genome") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：校验参考压缩文件，从 GTF 属性提取转录本—基因关系。
  # 输出：tx2gene.tsv 与参考统计；不依赖属性字段的先后顺序。
  readRenviron("0script/project.env")
  reference_files <- file.path(reference_dir, c(
    "genome.fa.gz", "transcripts.fa.gz", "annotation.gtf.gz"
  ))
  # 主线不强制要求蛋白；第 18 章启动时才检查支线蛋白及身份映射。
  protein_file <- file.path(reference_dir, "proteins.fa.gz")
  if (file.exists(protein_file)) reference_files <- c(reference_files, protein_file)
  stopifnot(all(file.exists(reference_files)))
  for (path in reference_files) {
    status <- system2("gzip", c("-t", shQuote(path)))
    if (status != 0) stop("参考文件解压校验失败: ", path)
  }

  # 功能：按字段名提取属性，避免假定 gene_id 总在 transcript_id 前面。
  gtf <- read.delim(gzfile(file.path(reference_dir, "annotation.gtf.gz")),
                    header = FALSE, sep = "\t", quote = "", comment.char = "#",
                    stringsAsFactors = FALSE)
  stopifnot(ncol(gtf) == 9)
  # GTF 属性的顺序并不固定，分别提取 ID，避免依赖 gene_id 必须在前。
  # 接口｜get_attribute：按属性键从 GTF 第九列提取值。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # attributes（必填，无默认值）：GTF 第九列属性字符串向量；每行单独提取指定键，不假定属性顺序。
  # key（必填，无默认值）：单个 GTF 属性键字符串，如 transcript_id、gene_id；缺少这个键返回 NA，不根据属
  #   性位置猜值。
  # 返回/写出与边界：返回与输入等长的字符向量，键缺失为 NA；不写文件。
  get_attribute <- function(attributes, key) {
    pattern <- paste0('(?:^|;[[:space:]]*)', key, '[[:space:]]+"([^"]+)"')
    matched <- regexec(pattern, attributes, perl = TRUE)
    values <- regmatches(attributes, matched)
    vapply(values, function(x) if (length(x) == 2) x[2] else NA_character_, character(1))
  }
  feature_rows <- gtf$V3 %in% c("transcript", "exon", "CDS")
  attributes <- gtf$V9[feature_rows]
  tx2gene <- unique(data.frame(
    transcript_id = get_attribute(attributes, "transcript_id"),
    gene_id = get_attribute(attributes, "gene_id")
  ))
  tx2gene <- tx2gene[complete.cases(tx2gene), , drop = FALSE]
  tx2gene <- tx2gene[order(tx2gene$transcript_id), , drop = FALSE]
  stopifnot(nrow(tx2gene) > 0, !anyDuplicated(tx2gene$transcript_id))

  # 功能：只使用 GTF 明确提供的版本别名，不盲目删除点号。
  # cDNA 的 ID 有时带版本，而 GTF 分开保存 transcript_id/transcript_version。
  # 只用 GTF 明确给出的版本建立别名，不对任意 ID 删除点号或截断字符串。
  # 接口｜read_fasta_ids：分块读取压缩 FASTA 标题。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # path（必填，无默认值）：gzip FASTA 文件路径；读取标题行的第一个非空白字段为 ID，保留版本点号。
  # 返回/写出与边界：返回字符 ID 向量；空 ID 集或重复 ID 报错，退出时关闭连接。
  read_fasta_ids <- function(path) {
    connection <- gzfile(path, "rt")
    on.exit(close(connection))
    ids <- character()
    repeat {
      lines <- readLines(connection, n = 50000, warn = FALSE)
      if (!length(lines)) break
      ids <- c(ids, sub("[[:space:]].*$", "", substring(lines[startsWith(lines, ">")], 2)))
    }
    if (!length(ids) || anyDuplicated(ids)) stop("转录本 FASTA 的 ID 为空或重复")
    ids
  }
  fasta_ids <- read_fasta_ids(file.path(reference_dir, "transcripts.fa.gz"))
  version_rows <- unique(data.frame(transcript_id = get_attribute(attributes, "transcript_id"),
    gene_id = get_attribute(attributes, "gene_id"), version = get_attribute(attributes, "transcript_version")))
  version_rows <- version_rows[complete.cases(version_rows), , drop = FALSE]
  aliases <- transform(tx2gene, gtf_transcript_id = transcript_id)
  if (nrow(version_rows)) aliases <- unique(rbind(aliases, data.frame(
    transcript_id = paste0(version_rows$transcript_id, ".", version_rows$version),
    gene_id = version_rows$gene_id, gtf_transcript_id = version_rows$transcript_id)))
  if (anyDuplicated(aliases$transcript_id)) stop("参考中转录本版本对应存在冲突")
  missing_ids <- setdiff(fasta_ids, aliases$transcript_id)
  if (length(missing_ids)) stop("cDNA ID 无法与同版 GTF 明确对应；请核对来源或提供已核实的映射。示例：", paste(head(missing_ids), collapse = ", "))
  # 基因 ID 原样保留。进入 FASTA 的转录本使用实际 FASTA ID，其余 GTF 记录仍保留，
  # 这样第 08 章能区分“未纳入参考”和“索引去重”，不会把它们假装成零表达。
  fasta_mapping <- aliases[match(fasta_ids, aliases$transcript_id), , drop = FALSE]
  if (anyDuplicated(fasta_mapping$gtf_transcript_id)) stop("FASTA 多个 ID 对应同一 GTF 转录本，请核对版本重复")
  tx2gene$transcript_id[match(fasta_mapping$gtf_transcript_id, tx2gene$transcript_id)] <- fasta_mapping$transcript_id
  tx2gene <- tx2gene[order(tx2gene$transcript_id), , drop = FALSE]
  stopifnot(!anyDuplicated(tx2gene$transcript_id))

  # 功能：已有表只核对；不一致时输出候选并停止，不覆盖旧结果。
  # 同名派生表已经存在时只核对，不用新范围静默替换旧映射。
  # 范围不同则先输出候选并停止；明确采用新参考后还需重建索引及下游结果。
  # 接口｜write_reference_table：保护已有参考派生表并保存新表。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # table（必填，无默认值）：待保存的 data.frame；列名和行内容已经由当前步骤构造，写出时不附加 R 行号。
  # path（必填，无默认值）：参考派生 TSV 的目标路径；已有相同表则复用，不同则保留候选并中止。
  # 返回/写出与边界：已有相同内容时不可见返回路径；不同内容保存候选后报错；新表直接写出。后续不依赖普通
  #   写出分支的返回值。
  write_reference_table <- function(table, path) {
    if (file.exists(path)) {
      old <- read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
      if (isTRUE(all.equal(old, table, check.attributes = FALSE))) return(invisible(path))
      write_generated_table(table, path)
      stop("已有参考派生表与当前输入不一致；候选已保存，请核对并明确采用：", path)
    }
    write.table(table, path, sep = "\t", quote = FALSE, row.names = FALSE)
  }
  write_reference_table(tx2gene, file.path(reference_dir, "tx2gene.tsv"))
  reference_summary <- data.frame(
    feature = c("mapped_transcripts", "mapped_genes"),
    n = c(nrow(tx2gene), length(unique(tx2gene$gene_id)))
  )
  write_reference_table(reference_summary, file.path(reference_dir, "reference_summary.tsv"))
  print(reference_summary)
  invisible(list(reference_dir = reference_dir))
}
