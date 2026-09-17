# 文件用途｜共用工具接口：统一抛出输入规范错误；以文本保护 ID 并严格读取 TSV/CSV。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：由编号分析脚本显式传入本工具的参数；每个接口的输入、返回和副作用见函数前注释。不通过修改工
#   具内部代码来切换样本或物种。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜input_error：统一抛出输入规范错误。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# ...（必填，无默认值）：任意数量的报错文本片段，按传入顺序交给 stop；无统计参数。
# 返回/写出与边界：用 stop 中止，返回值不存在；不自动修复或删改输入表。
input_error <- function(...) stop(paste0(...), call. = FALSE)

# 接口｜read_input_table：以文本保护 ID 并严格读取 TSV/CSV。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# path（必填，无默认值）：本地 TSV/CSV 输入表路径；按首行判断分隔符，初始全部按文本读以保护 ID。
# allow_first_blank（默认 FALSE）：TRUE/FALSE；是否允许输入首列表头为空（兼容矩阵行名）。不允许其他列
#   空表头，不给重复 ID 自动改名。
# allow_implicit_rownames（默认 FALSE）：TRUE/FALSE；仅对明确的旧结果格式允许数据行比表头多一列的隐式
#   行名，普通输入表不要随意启用。
# 返回/写出与边界：返回 data.frame；缺文件、坏表头、重复列名、行宽异常等时报错，不改变原文件。
read_input_table <- function(path, allow_first_blank = FALSE, allow_implicit_rownames = FALSE) {
  if (!file.exists(path)) input_error("未找到输入表：", path)
  header <- readLines(path, n = 1L, warn = FALSE, encoding = "UTF-8")
  if (!length(header)) input_error("输入表为空：", path)
  separator <- if (grepl("\t", header, fixed = TRUE)) "\t" else ","
  widths <- count.fields(path, sep = separator, quote = '\"', comment.char = "",
                         blank.lines.skip = TRUE)
  # Trinity/R 的部分结果把基因写在行名，表头比数据少一列。
  # 只在显式读取结果行名时接受；普通样本表/矩阵的行宽检查不放松。
  implicit <- allow_implicit_rownames && length(widths) > 1L &&
    all(widths[-1][!is.na(widths[-1])] == widths[1] + 1L)
  if (!implicit && any(widths[!is.na(widths)] != widths[1])) input_error("表格行列数不一致：", path)
  arguments <- list(file = path, header = !implicit, sep = separator, quote = '\"',
                  comment.char = "", check.names = FALSE, colClasses = "character",
                  na.strings = c("", "NA", "N/A"), fileEncoding = "UTF-8-BOM",
                  stringsAsFactors = FALSE, fill = FALSE)
  if (implicit) {
    arguments$skip <- 1L
    arguments$col.names <- c("gene_id", scan(text = header, what = "", sep = separator, quote = '\"', quiet = TRUE))
  }
  # 表格读取先保留文本字段，避免数字样本/基因 ID 丢失前导零；行宽与表头须先明确，不能依靠 R 自动补齐。
  x <- do.call(read.table, arguments)
  if (allow_first_blank && !nzchar(names(x)[1])) names(x)[1] <- "gene_id"
  if (any(!nzchar(names(x))) || anyDuplicated(names(x))) input_error("表头为空或重名：", path)
  x[] <- lapply(x, function(z) ifelse(is.na(z), NA_character_, trimws(z)))
  x
}

# 功能：读取已保存的结果，技术 ID 保持文本，统计列恢复数值类型。
# row_names=TRUE 时第一列作为行名，兼容 Trinity 的空首列表头。
# 不能让纯数字基因 ID 变成行号，或让 001 在读回时变为 1。
# 接口｜read_result_table：读取已有结果并保留文本 ID。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# path（必填，无默认值）：已有结果 TSV/CSV 路径；在保留 ID 文本的基础上恢复其他数值列，兼容明确的旧行
#   名格式。
# row_names（默认 FALSE）：TRUE/FALSE；TRUE 把第一列文本 ID 用作 R 行名，FALSE 保留为普通列。首列 ID
#   不自动转换成数字。
# id_columns（默认 c("gene_id", "contrast_id", "CycID")）：字符列名向量；结果表中应保持文本的 ID 列。
#   其他列再尝试恢复数值，避免把 001 读成 1。
# 返回/写出与边界：返回 data.frame，按 row_names 决定首列去向；其他非 ID 列尝试类型转换，不写文件。
read_result_table <- function(path, row_names = FALSE,
                              id_columns = c("gene_id", "contrast_id", "CycID")) {
  x <- read_input_table(path, allow_first_blank = TRUE, allow_implicit_rownames = row_names)
  keep_text <- intersect(id_columns, names(x))
  if (row_names) keep_text <- union(keep_text, names(x)[1])
  for (field in setdiff(names(x), keep_text)) {
    x[[field]] <- type.convert(x[[field]], as.is = TRUE)
  }
  if (row_names) {
    require_columns(x, names(x)[1], "结果首列 ID")
    if (anyDuplicated(x[[1]])) input_error("结果首列 ID 重复：", path)
    rownames(x) <- x[[1]]
    x <- x[-1]
  }
  x
}

# 接口｜require_columns：检查必需列是否齐全且值非空。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# x（必填，无默认值）：带列名的 data.frame；核对必需列存在且其各行值非缺失/非空，不改变列顺序或删除额
#   外列。
# columns（必填，无默认值）：字符列名向量；本次要求存在的字段，允许表中有额外列，但缺少任一必需列会报
#   错。
# label（必填，无默认值）：字符说明；用于报错时指出正在检查哪个输入，不改变实际列名。
# 返回/写出与边界：缺列或必需列含缺失/空值时抛错并指出行；成功不修改 x，额外列允许保留。
require_columns <- function(x, columns, label) {
  missing <- setdiff(columns, names(x))
  if (length(missing)) input_error(label, "缺少必填列：", paste(missing, collapse = ", "))
  for (field in columns) {
    bad <- which(is.na(x[[field]]) | !nzchar(x[[field]]))
    if (length(bad)) input_error(label, "第 ", paste(bad + 1L, collapse = ","),
                                  " 行的 ", field, " 缺失")
  }
}

# 接口｜check_technical_id：校验安全的样本/组/比较技术 ID。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# x（必填，无默认值）：样本、组或比较的技术 ID 字符向量；只能使用约定的安全字符，不用于限制基因 ID 为
#   非数字。
# label（必填，无默认值）：字符说明；用于报错时指出正在检查哪个输入，不改变实际列名。
# 返回/写出与边界：非法或保留名称报错；成功不修改输入。基因 ID 不使用此限制，不以此删除版本号。
check_technical_id <- function(x, label) {
  good <- !is.na(x) & grepl("^[A-Za-z0-9][A-Za-z0-9_.-]*$", x)
  # ID 按字符读取；仍避免纯数字/逻辑保留值进入第三方脚本后被自动改名。
  reserved <- toupper(x) %in% c("TRUE", "FALSE", "T", "F", "NA", "NAN", "INF")
  numeric_id <- !is.na(suppressWarnings(as.numeric(x))) | grepl("^0[xX][0-9a-fA-F]+$", x)
  bad <- which(!good | reserved | numeric_id)
  if (length(bad)) input_error(label, "第 ", paste(bad + 1L, collapse = ","),
    " 行 ID 不合法；使用 sample_001、T0 等字母/数字/点/下划线/短横线组合，不能含路径")
}

# 接口｜read_samples：把项目样本表读成统一下游接口。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# path（默认 "0script/samples.tsv"）：样本表路径；通常 0script/samples.tsv，可为规范 TSV/CSV。一个样本
#   只占一行，额外列允许保留。
# entry（默认 Sys.getenv("DATA_ENTRY", "matrix")）：字符 fastq 或 matrix；决定输入检查需要 FASTQ 文件
#   列还是已有表达矩阵，不自动转换数据尺度。
# use_time（默认 "auto"）：auto、time 或 group；time 强制要求真实时间，group 只用分组，auto 允许无时间
#   项目。时间缺失不能用列顺序伪造小时数。
# cycle（默认 FALSE）：TRUE/FALSE；TRUE 要求样本表明确提供 cycle_use 且至少选中一个样本；等间隔/重复设
#   计由周期入口再核对。
# check_files（默认 FALSE）：TRUE/FALSE；是否核对样本声明的 FASTQ 文件存在。FALSE 只跳过文件存在检查，
#   不跳过样本字段校验。
# raw_dir（默认 "2data/rawdata"）：字符目录；FASTQ 原文件所在位置，read1/read2 只填其中的文件名，不在
#   每行重复写完整路径。
# 返回/写出与边界：返回保留额外列的标准化表及 cycle_supplied 属性；校验样本唯一、重复/组/时间一致，按
#   需查文件，不从样本名猜生物学分组。
read_samples <- function(path = "0script/samples.tsv", entry = Sys.getenv("DATA_ENTRY", "matrix"),
                         use_time = "auto", cycle = FALSE, check_files = FALSE,
                         raw_dir = "2data/rawdata") {
  if (!entry %in% c("matrix", "fastq")) input_error("entry 必须是 matrix 或 fastq")
  if (!use_time %in% c("auto", "time", "group")) input_error("use_time 必须是 auto/time/group")
  x <- read_input_table(path)
  if (!nrow(x)) input_error("样本表没有样本")
  # group 是对外分组列，内部统一到 timepoint；若两列同时存在必须一致，不能静默选其中一列覆盖矛盾。
  if ("group" %in% names(x)) {
    if ("timepoint" %in% names(x) && !identical(x$group, x$timepoint))
      input_error("group 与 timepoint 内容冲突；请在入口保留唯一分组定义")
    x$timepoint <- x$group
  }
  require_columns(x, c("sample_id", "timepoint", "replicate"), "样本表")
  check_technical_id(x$sample_id, "样本表 sample_id：")
  check_technical_id(x$timepoint, "样本表 timepoint：")
  if (anyDuplicated(x$sample_id)) input_error("sample_id 重复：", x$sample_id[duplicated(x$sample_id)][1])
  if (any(!grepl("^[1-9][0-9]*$", x$replicate))) input_error("replicate 必须是实际组内重复的正整数编号")
  x$replicate <- suppressWarnings(as.integer(x$replicate))
  if (anyNA(x$replicate) || anyDuplicated(x[c("timepoint", "replicate")]))
    input_error("replicate 超出整数范围，或同组重复编号重复")
  cycle_supplied <- "cycle_use" %in% names(x)
  if (cycle && !cycle_supplied) input_error("周期分析须在原表明确提供 cycle_use，不能默认推断")
  defaults <- list(gsm = NA_character_, srr = NA_character_, read1 = NA_character_,
                   read2 = NA_character_, time_hour = NA_character_, cycle_use = "FALSE")
  for (field in names(defaults)) if (!field %in% names(x)) x[[field]] <- defaults[[field]]
  if (entry == "fastq") {
    require_columns(x, c("read1", "read2"), "双端样本表")
    files <- c(x$read1, x$read2)
    if (anyDuplicated(files)) input_error("同一 FASTQ 被多个样本或两端重复使用")
    if (any(grepl("[/\\\\\t\r\n]", files)) || any(!grepl("\\.(fastq|fq)\\.gz$", files)))
      input_error("read1/read2 应为 rawdata 下的 .fastq.gz/.fq.gz 文件名，不含目录")
    if (check_files && any(!file.exists(file.path(raw_dir, files))))
      input_error("缺少 FASTQ：", paste(files[!file.exists(file.path(raw_dir, files))], collapse = ", "))
  }
  hour_text <- x$time_hour
  x$time_hour <- suppressWarnings(as.numeric(hour_text))
  if (any(!is.na(hour_text) & !is.finite(x$time_hour))) input_error("time_hour 必须为真实、有限的数值小时")
  if (anyNA(x$time_hour) && !all(is.na(x$time_hour))) input_error("time_hour 部分缺失，请补齐时间或另用完整普通分组表")
  if (use_time == "time" && anyNA(x$time_hour)) input_error("时间分析需要所有样本的 time_hour")
  times <- split(x$time_hour, x$timepoint)
  if (any(vapply(times, function(z) length(unique(z)) != 1L, logical(1))))
    input_error("同组样本对应多个 time_hour，请核对组别与真实时间")
  flags <- toupper(x$cycle_use)
  if (anyNA(flags) || any(!flags %in% c("TRUE", "FALSE"))) input_error("cycle_use 只能为 TRUE/FALSE，不能空缺")
  x$cycle_use <- flags == "TRUE"
  if (any(x$cycle_use) && anyNA(x$time_hour)) input_error("纳入周期分析的样本必须提供真实时间")
  if (cycle && !any(x$cycle_use)) input_error("cycle_use 未选中任何样本")
  if (use_time == "group" && cycle) input_error("普通分组不能执行周期分析")
  standard <- c("sample_id", "timepoint", "replicate", "gsm", "srr", "read1", "read2", "time_hour", "cycle_use")
  x <- x[c(standard, setdiff(names(x), standard))]
  attr(x, "cycle_supplied") <- cycle_supplied
  x
}

# 接口｜ordered_groups：获得稳定的分组展示顺序。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# samples（必填，无默认值）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# require_time（默认 FALSE）：TRUE/FALSE；TRUE 强制完整、无冲突的真实小时顺序；FALSE 在无时间时按样本
#   表分组首次出现顺序。
# 返回/写出与边界：返回字符组名向量；完整真实时间优先按小时，无时间则按出现顺序，require_time 时拒绝不
#   完整或冲突时间。
ordered_groups <- function(samples, require_time = FALSE) {
  design <- unique(samples[c("timepoint", "time_hour")])
  if (require_time && (anyNA(design$time_hour) || anyDuplicated(design$time_hour)))
    input_error("相邻/时间分析需要每组唯一的真实时间；并列时间或多条件请明确分层，比较可改用自定义表")
  if (all(is.finite(design$time_hour))) design <- design[order(design$time_hour), , drop = FALSE]
  as.character(design$timepoint)
}

# 接口｜sample_order：取得组内按重复编号排列的样本顺序。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# samples（必填，无默认值）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# 返回/写出与边界：返回按顺序排列的 sample_id 字符向量（不是行号）；分组顺序来自 ordered_groups，不修
#   改样本表。
sample_order <- function(samples) {
  samples$sample_id[order(match(samples$timepoint, ordered_groups(samples)), samples$replicate)]
}

# 接口｜align_expression：核对矩阵与样本表并统一列顺序。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# matrix（必填，无默认值）：数值表达矩阵；行是基因、列是样本，保留原始行列名，不通过截断 ID 来匹配。
# samples（必填，无默认值）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# 返回/写出与边界：返回重排后的矩阵；样本集合不同报错，不静默删列或补零。
align_expression <- function(matrix, samples) {
  if (is.null(colnames(matrix)) || anyDuplicated(colnames(matrix)) ||
      !setequal(colnames(matrix), samples$sample_id))
    input_error("矩阵样本列须与 sample_id 一一对应；不能缺失、重名或含未声明样本")
  # 严格确认样本集合完全一致后才按样本表重排列；不能将缺失样本自动补零，也不能默默丢掉多余样本。
  matrix[, samples$sample_id, drop = FALSE]
}

# 接口｜read_expression：校验表达矩阵数值与 ID 并对齐样本。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# path（必填，无默认值）：已有基因表达表路径；第一列为唯一 gene_id，其余列按 sample_id 对齐，不能含负
#   数、非有限值或全零样本。
# samples（必填，无默认值）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# 返回/写出与边界：返回非负有限数值矩阵；拒绝重复基因或全零样本。通过此检查不证明 counts/TPM/TMM 尺度
#   填对，仍要核实来源。
read_expression <- function(path, samples) {
  x <- read_input_table(path, allow_first_blank = TRUE)
  if (ncol(x) < 2L || !nrow(x)) input_error("矩阵需要基因列及样本数值列：", path)
  genes <- x[[1]]
  if (anyNA(genes) || any(!nzchar(genes)) || anyDuplicated(genes)) input_error("矩阵基因 ID 缺失或重复：", path)
  mat <- as.matrix(x[-1]); suppressWarnings(storage.mode(mat) <- "double")
  if (any(!is.finite(mat)) || any(mat < 0)) input_error("矩阵含缺失、非数值、负值或无穷值：", path)
  rownames(mat) <- genes
  mat <- align_expression(mat, samples)
  if (any(colSums(mat > 0) == 0)) input_error("矩阵包含全零样本列：", path)
  mat
}

# 接口｜normalize_contrasts：规范比较表并核对组名和比较方向。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# x（必填，无默认值）：待核对的比较 data.frame；列描述比较 ID、实验组、参照组和 enabled；规范后与样本
#   表核对组名。
# samples（必填，无默认值）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# 返回/写出与边界：返回规范比较表；拒绝重复 ID、自比或不存在的组，不推断额外协变量。
normalize_contrasts <- function(x, samples) {
  require_columns(x, c("test_group", "reference_group"), "比较表")
  if (!nrow(x)) input_error("比较表没有比较")
  if (!"contrast_id" %in% names(x)) x$contrast_id <- paste0(x$test_group, "_vs_", x$reference_group)
  if (!"comparison_type" %in% names(x)) x$comparison_type <- "custom"
  if (!"enabled" %in% names(x)) x$enabled <- "TRUE"
  require_columns(x, c("contrast_id", "comparison_type", "enabled"), "比较表")
  check_technical_id(x$contrast_id, "比较表 contrast_id：")
  if (anyDuplicated(x$contrast_id)) input_error("contrast_id 重复或自动名称碰撞；请显式指定不同名称")
  if (any(!x$test_group %in% samples$timepoint) || any(!x$reference_group %in% samples$timepoint) ||
      any(x$test_group == x$reference_group)) input_error("比较表包含未知分组或自己与自己比较")
  flags <- toupper(as.character(x$enabled))
  if (any(!flags %in% c("TRUE", "FALSE"))) input_error("enabled 只能为 TRUE/FALSE")
  x$enabled <- flags == "TRUE"
  if (anyDuplicated(x[x$enabled, c("test_group", "reference_group")])) input_error("启用的同方向比较重复")
  standard <- c("contrast_id", "test_group", "reference_group", "comparison_type", "enabled")
  x[c(standard, setdiff(names(x), standard))]
}

# 接口｜read_contrasts：读取正式比较表并应用统一校验。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# path（默认 "0script/contrasts.tsv"）：正式比较表路径；不存在时报错，不在读取过程中暗中生成新的比较。
# samples（默认 read_samples()）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# 返回/写出与边界：返回规范比较 data.frame；不在读取过程中覆盖或自动重建正式表。
read_contrasts <- function(path = "0script/contrasts.tsv", samples = read_samples()) {
  normalize_contrasts(read_input_table(path), samples)
}

# 接口｜generate_contrasts：由标准样本表生成一套明确策略的比较。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# samples（必填，无默认值）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# strategy（默认 "baseline"）：字符比较策略；baseline、adjacent 或 baseline_and_adjacent。含 baseline
#   时指定 reference，adjacent 需真实时间；任意自选比较直接在正式比较表中定义。
# reference（默认 ""）：字符参照组；须为样本表已有组，用于 baseline 类比较；不从字符串字母序擅自猜对照
#   组。
# 返回/写出与边界：返回含启用状态的比较表；相邻比较按真实小时且合并策略去重。返回表仍须核实实验意义。
generate_contrasts <- function(samples, strategy = "baseline", reference = "") {
  if (!strategy %in% c("baseline", "adjacent", "baseline_and_adjacent"))
    input_error("strategy 可选 baseline、adjacent、baseline_and_adjacent")
  groups <- ordered_groups(samples, require_time = strategy != "baseline")
  if (length(groups) < 2L) input_error("至少需要两个分组才能生成比较")
  out <- data.frame(test_group = character(), reference_group = character(), comparison_type = character())
  if (strategy != "adjacent") {
    if (!length(reference) || !nzchar(reference) || !reference %in% groups)
      input_error("请明确 reference 基准组；不会默认把表中第一组当作对照")
    out <- data.frame(test_group = setdiff(groups, reference), reference_group = reference, comparison_type = "baseline")
  }
  if (strategy != "baseline") out <- rbind(out, data.frame(
    test_group = groups[-1], reference_group = groups[-length(groups)], comparison_type = "adjacent"))
  pair <- paste(out$test_group, out$reference_group, sep = "\t")
  repeated <- duplicated(pair) | duplicated(pair, fromLast = TRUE)
  out$comparison_type[repeated] <- "baseline_and_adjacent"
  # 合并基准/相邻策略时去除完全相同的方向对，不把反向比较视为同一个方向。
  normalize_contrasts(out[!duplicated(pair), , drop = FALSE], samples)
}

# 接口｜write_generated_table：原子保存新表或不覆盖正式文件的候选表。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# x（必填，无默认值）：待写 data.frame；以 TSV 保存，quote=FALSE、row.names=FALSE，不附加行序号。
# path（必填，无默认值）：期望正式文件路径；已存在则改写到 .generated.tsv 候选，候选相同可复用、不同报
#   错，不覆盖正式表。
# 返回/写出与边界：不可见返回实际写入/复用路径；已存在不同候选报错。临时文件在同目录，重命名成功后才作
#   为完成。
write_generated_table <- function(x, path) {
  # 正式表存在时只输出候选；不会覆盖人工编辑。候选已有不同内容同样拒绝覆盖。
  target <- if (file.exists(path)) sub("\\.tsv$", ".generated.tsv", path) else path
  if (identical(target, path) && file.exists(path)) input_error("输出应使用 .tsv：", path)
  dir.create(dirname(target), recursive = TRUE, showWarnings = FALSE)
  scratch <- tempfile("table-", tmpdir = dirname(target))
  on.exit(unlink(scratch), add = TRUE)
  write.table(x, scratch, sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
  if (file.exists(target)) {
    if (identical(unname(tools::md5sum(scratch)), unname(tools::md5sum(target)))) return(invisible(target))
    input_error("候选表已存在且内容不同：", target, "；请先核对或另选输出名")
  }
  if (!file.rename(scratch, target)) input_error("无法保存：", target)
  message("已生成：", target)
  invisible(target)
}
