# 文件用途｜第 09 章：明确开启后保存独立的均值替代探索分支。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜replace_with_mean：在表达矩阵副本中用同组真实重复的逐基因均值替代一列。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# df（必填，无默认值）：原表达 data.frame；样本为列，逐基因均值替代在副本 df_new 上进行，调用者的原对
#   象不原地改写。
# target_col（必填，无默认值）：单个字符样本 ID；已由人工核实的待替代列，必须在矩阵和样本表中存在，不
#   能同时出现在 source_cols。
# source_cols（必填，无默认值）：字符向量；同组至少两个不同的真实重复 ID。逐基因取这些列的均值，不允许
#   把替代目标或重复列再当来源。
# samples（必填，无默认值）：标准化样本 data.frame；一行一个样本，含 sample_id、timepoint/group、
#   replicate，时间分析还用 time_hour/cycle_use。通常由 read_samples() 生成。
# 返回/写出与边界：返回新 data.frame，不修改传入的 df，不创建独立生物学重复；目标、来源或组别不符合要
#   求时报错。
replace_with_mean <- function(df, target_col, source_cols, samples) {
  stopifnot(length(target_col) == 1, target_col %in% names(df), length(source_cols) >= 2,
            !anyDuplicated(source_cols), !anyDuplicated(samples$sample_id),
            all(source_cols %in% names(df)), !target_col %in% source_cols)
  selected <- samples[match(c(target_col, source_cols), samples$sample_id), ]
  stopifnot(!anyNA(selected$sample_id), length(unique(selected$timepoint)) == 1)
  stopifnot(all(is.finite(as.matrix(df[, source_cols, drop = FALSE]))))
  df_new <- df
  df_new[[target_col]] <- rowMeans(df[, source_cols, drop = FALSE])
  df_new
}

# target_col：一个已核查的异常样本；source_cols：同组至少两个独立重复。
# run_exploratory：只有明确设为 TRUE 才执行；不是自动检测/修复异常值。
# variant_label：保留另一次探索的独立目录，不覆盖已有结果。
# 接口｜run_exploratory_rescue：明确开启后保存独立的均值替代探索分支。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# target_col（默认 ""）：单个字符样本 ID；已由人工核实的待替代列，必须在矩阵和样本表中存在，不能同时出
#   现在 source_cols。
# source_cols（默认 character()）：字符向量；同组至少两个不同的真实重复 ID。逐基因取这些列的均值，不允
#   许把替代目标或重复列再当来源。
# run_exploratory（默认 FALSE）：单个 TRUE/FALSE；FALSE 立即返回、不写文件。只有明确确认探索用途才设
#   TRUE；替代值不是新增的独立生物学重复。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：FALSE 返回不可见 NULL；TRUE 保存探索矩阵与限制说明并返回 output_dir，不进入正式
#   DESeq2、不覆盖原矩阵，仍需补充真实实验。
run_exploratory_rescue <- function(target_col = "", source_cols = character(),
                                   run_exploratory = FALSE, variant_label = "") {
  stopifnot(is.logical(run_exploratory), length(run_exploratory) == 1, !is.na(run_exploratory))
  if (!run_exploratory) return(invisible(NULL))
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  readRenviron("0script/project.env")
  samples <- read_samples()
  matrix_file <- project_result("TMM_MATRIX", "3Salmon/quanti/gene.TMM.EXPR.matrix")
  expression <- as.data.frame(read_expression(matrix_file, samples))
  exploratory <- replace_with_mean(expression, target_col, source_cols, samples)
  claim <- begin_result_stage("4SampleHeatmapPCA/exploratory",
    list(target_col = target_col, source_cols = source_cols, purpose = "exploration_only"),
    list(expression = matrix_file, samples = samples), variant_label)
  write.table(cbind(gene_id = rownames(exploratory), exploratory),
    file.path(claim$path, "mean_replaced_expression.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(c("仅供探索：均值替代不产生独立生物学重复，不进入正式 DESeq2。",
    "仍需补充独立实验、重测或真实重复；不能据此报告正式显著性。"), file.path(claim$path, "exploration_note.txt"))
  finish_result_dir(claim)
  invisible(list(output_dir = claim$path))
}
