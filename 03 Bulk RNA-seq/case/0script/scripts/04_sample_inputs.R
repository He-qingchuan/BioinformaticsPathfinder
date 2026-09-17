# 文件用途｜第 04 章：把导出的双端下载记录按 accession 配成样本草表；根据正式样本表生成选定策略的比较
#   表。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜prepare_sra_samples：把导出的双端下载记录按 accession 配成样本草表。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# metadata_file（默认 "0script/sra_explorer_metadata.tsv"）：字符路径；已经从 SRA Explorer 导出的 Full
#   Metadata 表。本函数只读本地表，不查询网站、不下载 FASTQ。
# filename_column（默认 "FastQ nice filename"）：字符列名；选择实际下载脚本采用的文件名列。nice 文件名
#   用 FastQ nice filename，原始文件名用 FastQ filename；必须与磁盘一致。
# output_file（默认 "0script/samples.draft.tsv"）：字符路径；待保存的表格位置。样本草表不是正式表，核
#   实分组与重复后才采用；已有文件按候选表规则处理。
# 返回/写出与边界：不可见返回草表并写候选 TSV；group/replicate 留待核实。单端、混入 orphan、重复文件或
#   配对冲突报错。
prepare_sra_samples <- function(metadata_file = "0script/sra_explorer_metadata.tsv",
                                filename_column = "FastQ nice filename",
                                output_file = "0script/samples.draft.tsv") {
  # 功能：按 accession 将导出的 R1/R2 配成一行，自动提取 ID 和文件名。
  # filename_column 必须与实际执行的下载脚本命名一致：nice 名或原始名任选其一。
  # 分组/重复不能从文件顺序推断，草表留空待核实；不会写入正式 samples.tsv。
  source("0script/tools/metadata.R", local = TRUE)
  metadata <- read_input_table(metadata_file)
  require_columns(metadata, c("Accession", filename_column), "SRA Explorer Full Metadata")
  if (!nrow(metadata)) input_error("元数据没有 FASTQ 记录")
  filenames <- metadata[[filename_column]]
  if (anyDuplicated(filenames) || any(grepl("[/\\\\]", filenames)))
    input_error("下载文件名重复或带路径；请核对导出文件，不要合并重复行冒充样本")
  original <- if ("FastQ filename" %in% names(metadata)) metadata[["FastQ filename"]] else filenames
  mate_pattern <- "[_\\.]R?([12])(?:_001)?\\.(?:fastq|fq)\\.gz$"
  if (anyNA(original) || any(!grepl(mate_pattern, original, perl = TRUE)))
    input_error("无法明确识别双端文件；本流程需要 R1/R2，不自动丢弃 orphan 或把单端当双端")
  mates <- sub(paste0(".*", mate_pattern), "\\1", original, perl = TRUE)
  runs <- unique(metadata$Accession)
  check_technical_id(runs, "Accession：")
  result <- do.call(rbind, lapply(runs, function(run) {
    rows <- which(metadata$Accession == run)
    if (length(rows) != 2L || !setequal(mates[rows], c("1", "2")))
      input_error("运行 ", run, " 不是唯一的一对 R1/R2；核对技术重复和文件类型后再整理")
    title <- if ("Title" %in% names(metadata)) unique(na.omit(metadata$Title[rows])) else character()
    if (length(title) > 1L) input_error("同一 accession 的样本标题冲突：", run)
    data.frame(sample_id = run, group = "", replicate = "", srr = run,
      read1 = filenames[rows[mates[rows] == "1"]], read2 = filenames[rows[mates[rows] == "2"]],
      source_title = if (length(title)) title else "", check.names = FALSE)
  }))
  write_generated_table(result, output_file)
  message("已配对 ", nrow(result), " 个运行。核实实验条件后补充 group/replicate；不要把草表直接视为通过检查。")
  invisible(result)
}

# 接口｜prepare_comparisons：根据正式样本表生成选定策略的比较表。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# comparison_mode（默认 "baseline"）：字符策略；baseline 为各组对指定参照，adjacent 为相邻真实时间，
#   baseline_and_adjacent 合并去重。其他自选比较在 contrasts.tsv 明确填写，不提供自动 all_pairs 选项。
# reference_group（默认 ""）：字符组名；差异方向的参照组，必须来自样本表，正 log2FC 表示实验组高于该组
#   。生成 baseline 类比较时必须明确填写。
# samples_file（默认 "0script/samples.tsv"）：字符路径；正式样本表，按列名而非固定列序读取。必需列与
#   FASTQ/矩阵入口差别见附4。
# 返回/写出与边界：不可见返回比较表并打印；写入正式空位或 .generated.tsv 候选，不覆盖已有正式表。
prepare_comparisons <- function(comparison_mode = "baseline", reference_group = "",
                               samples_file = "0script/samples.tsv") {
  # 功能：从正式样本表生成比较表；正 log2FC = test_group 高于 reference_group。
  # baseline 必须指定真实参照；adjacent 按真实小时排序；已有正式表仅生成候选。
  source("0script/tools/metadata.R", local = TRUE)
  readRenviron("0script/project.env")
  samples <- read_samples(samples_file)
  contrasts <- generate_contrasts(samples, strategy = comparison_mode, reference = reference_group)
  write_generated_table(contrasts, "0script/contrasts.tsv")
  print(contrasts, row.names = FALSE)
  invisible(contrasts)
}
