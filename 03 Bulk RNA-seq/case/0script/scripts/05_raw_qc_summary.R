# 文件用途｜第 05 章：汇总双端 FastQC ZIP 中的模块状态和质量范围。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_raw_qc_summary：汇总双端 FastQC ZIP 中的模块状态和质量范围。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# report_dir（默认 "2data/rawdata/qc"）：字符路径；已有 FastQC ZIP 的目录。读取其中的 fastqc_data.txt
#   ，不重新扫描测序文件。
# 返回/写出与边界：写 2data/rawdata/raw_qc_summary.tsv；不可见返回 report_dir。读取失败中止，红黄标记
#   不自动删样本。
run_raw_qc_summary <- function(report_dir = "2data/rawdata/qc") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：读取已有 FastQC ZIP 内的结构化统计，汇总每个 mate 的质量与模块状态。
  # 不重新扫描 FASTQ；输出 raw_qc_summary.tsv，红黄标记不作为自动删样本命令。
  samples <- read_samples()

  # 功能：从一个 FastQC ZIP 读取基本统计及指定模块，返回一个 mate 的一行诊断。
  # filename 为原 FASTQ 名，report_dir 是 ZIP 所在目录；不读取 FASTQ 内容。
  # 接口｜read_fastqc：读取一个样本的一端 FastQC 结构化报告。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # filename（必填，无默认值）：一个原 FASTQ 文件名字符串；用它推导 FastQC ZIP 及其内部成员名，不要求在
  #   此解压 FASTQ。
  # sample_id（必填，无默认值）：单个样本 ID 字符串；与样本表一致，用来标记汇总行，不根据文件顺序重命名。
  # mate（必填，无默认值）：字符 R1 或 R2；标明双端测序的哪一端，不是一个额外的生物学重复。
  # report_dir（默认 "2data/rawdata/qc"）：字符路径；已有 FastQC ZIP 的目录。读取其中的 fastqc_data.txt
  #   ，不重新扫描测序文件。
  # 返回/写出与边界：返回一行 data.frame，含 sample_id、mate、reads 数、质量范围及模块状态；不修改 ZIP。
  read_fastqc <- function(filename, sample_id, mate, report_dir = "2data/rawdata/qc") {
    stem <- sub("\\.(fastq|fq)\\.gz$", "", filename)
    path <- file.path(report_dir, paste0(stem, "_fastqc.zip"))
    member <- paste0(stem, "_fastqc/fastqc_data.txt")
    connection <- unz(path, member)
    text <- readLines(connection, warn = FALSE)
    close(connection)
    # 接口｜module：截取当前 FastQC 文本的一个模块。
    # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
    # name（必填，无默认值）：FastQC 模块完整名称，如 Basic Statistics；必须在当前 ZIP 的文本中唯一出现。
    # 返回/写出与边界：返回 status 和 lines 的 list；模块起点必须唯一。text 来自外层 read_fastqc，不是额外
    #   参数。
    module <- function(name) {
      start <- which(startsWith(text, paste0(">>", name, "\t")))
      stopifnot(length(start) == 1)
      end <- which(seq_along(text) > start & text == ">>END_MODULE")[1]
      list(status = strsplit(text[start], "\t", fixed = TRUE)[[1]][2],
           lines = text[seq.int(start + 1, end - 1)])
    }
    basic <- module("Basic Statistics")$lines
    # 接口｜value：从 Basic Statistics 取一个字段。
    # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
    # key（必填，无默认值）：Basic Statistics 中的字段名，如 Total Sequences；取制表符后的原始文本，数值转
    #   换由调用者完成。
    # 返回/写出与边界：返回字段值字符向量；basic 来自外层函数，不在这里做数值推断。
    value <- function(key) sub("^[^\t]+\t", "", basic[startsWith(basic, paste0(key, "\t"))])
    quality <- module("Per base sequence quality")
    q <- read.delim(text = paste(quality$lines[-1], collapse = "\n"), header = FALSE)
    data.frame(sample_id = sample_id, mate = mate, file = filename,
      encoding = value("Encoding"), total_reads = as.numeric(value("Total Sequences")),
      sequence_length = value("Sequence length"),
      minimum_position_mean_quality = min(q[[2]]), maximum_position_mean_quality = max(q[[2]]),
      base_quality_status = quality$status,
      gc_status = module("Per sequence GC content")$status,
      adapter_status = module("Adapter Content")$status,
      overrepresented_status = module("Overrepresented sequences")$status)
  }

  # 功能：对样本表中的每个 R1/R2 调用读取函数，并保存逐 mate 诊断表。
  diagnostics <- do.call(rbind, lapply(seq_len(nrow(samples)), function(i) {
    rbind(read_fastqc(filename = samples$read1[i], sample_id = samples$sample_id[i], mate = "R1", report_dir = report_dir),
          read_fastqc(filename = samples$read2[i], sample_id = samples$sample_id[i], mate = "R2", report_dir = report_dir))
  }))
  write.table(diagnostics, "2data/rawdata/raw_qc_summary.tsv", sep = "\t", quote = FALSE, row.names = FALSE)
  print(table(diagnostics$base_quality_status))
  invisible(list(report_dir = report_dir))
}
