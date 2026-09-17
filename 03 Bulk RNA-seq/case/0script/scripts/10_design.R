# 文件用途｜第 10 章：把规范样本/比较表转换为 Trinity DESeq2 设计文件。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：本文件运行入口没有形参，输入按下方读取语句来自项目文件。重新加载定义后直接调用，不需寻找额
#   外赋值段；文件编辑不会自动更新已经打开的 R 会话。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_design：把规范样本/比较表转换为 Trinity DESeq2 设计文件。
# 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
# 返回/写出与边界：写 samples.txt、contrasts.txt 与设计记录；不运行差异检验，不擅自添加批次/交互模型。
run_design <- function() {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  samples <- read_samples()
  contrasts <- read_contrasts()
  contrasts <- contrasts[toupper(as.character(contrasts$enabled)) == "TRUE", , drop = FALSE]
  counts <- as.data.frame(read_expression(project_result("COUNT_MATRIX", "3Salmon/quanti/gene.counts.matrix"), read_samples()), check.names = FALSE)
  stopifnot(nrow(contrasts) > 0, !anyDuplicated(contrasts$contrast_id),
            !anyDuplicated(samples$sample_id), setequal(names(counts), samples$sample_id))
  stopifnot(all(contrasts$test_group %in% samples$timepoint),
            all(contrasts$reference_group %in% samples$timepoint),
            all(contrasts$test_group != contrasts$reference_group))
  stopifnot(all(grepl("^[A-Za-z0-9][A-Za-z0-9_.-]*$", samples$sample_id)),
            all(grepl("^[A-Za-z0-9][A-Za-z0-9_.-]*$", samples$timepoint)),
            all(grepl("^[A-Za-z0-9][A-Za-z0-9_.-]*$", contrasts$contrast_id)))
  stopifnot(!anyDuplicated(contrasts[c("test_group", "reference_group")]),
            all(is.finite(as.matrix(counts))), all(as.matrix(counts) >= 0))
  # 独立重复要求针对真正参与比较的组；矩阵必须是未归一化 counts。这里仍是既定 ~ group 模型，不自动适配批
  #   次或配对设计。
  used_groups <- unique(c(contrasts$test_group, contrasts$reference_group))
  if (any(table(samples$timepoint)[used_groups] < 2)) stop("当前 DESeq2 路线要求组内至少两个独立重复")
  design_dir <- Sys.getenv("DE_DESIGN_DIR", "5DESeq2/design")
  claim <- begin_result_stage(design_dir, list(model = "~ group", minimum_replicates = 2),
    list(samples = samples, contrasts = contrasts, counts = counts))
  write.table(samples[c("timepoint", "sample_id")], file.path(design_dir, "samples.txt"),
              sep = "\t", quote = FALSE, row.names = FALSE, col.names = FALSE)
  write.table(contrasts[c("test_group", "reference_group")], file.path(design_dir, "contrasts.txt"),
              sep = "\t", quote = FALSE, row.names = FALSE, col.names = FALSE)
  finish_result_dir(claim)
}
