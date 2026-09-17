# 文件用途｜第 10 章：合并真实 DESeq2 结果并按门槛标记 up/down/ns。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_de_summary：合并真实 DESeq2 结果并按门槛标记 up/down/ns。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# fdr_cutoff（默认 as.numeric(Sys.getenv("FDR_CUTOFF"))）：数值阈值，通常 0.05，范围 (0,1]；控制当前步
#   骤的校正 P 值筛选，调小更严格。各比较/富集本体分别校正，不代表全项目共同做一次 BH。
# logfc_cutoff（默认 as.numeric(Sys.getenv("LOG2FC_CUTOFF"))）：非负数；绝对 log2FoldChange 门槛，1 对
#   应两倍变化。调大要求更大效应量；在汇总/绘图中修改不会重新拟合 DESeq2。
# analysis_dir（默认 project_result("DE_ANALYSIS_DIR", "5DESeq2/DE_analysis")）：字符路径；已有 DESeq2
#   原始统计文件所在目录。这里只读并汇总，不重新拟合模型，也不自动选取最新目录。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存 de_result.tsv/RData、DE_summary.tsv 与图，不可见返回 output_dir/analysis_dir；
#   不重新拟合模型。
run_de_summary <- function(fdr_cutoff = as.numeric(Sys.getenv("FDR_CUTOFF")),
  logfc_cutoff = as.numeric(Sys.getenv("LOG2FC_CUTOFF")),
  analysis_dir = project_result("DE_ANALYSIS_DIR", "5DESeq2/DE_analysis"),
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：读取合并所需文件与统一阈值；FDR_CUTOFF/LOG2FC_CUTOFF 决定后续方向标记。
  # 只调整显著性划分时重做本汇总和下游，不需要重新拟合未改变的模型。
  library(tidyverse)
  readRenviron("0script/project.env")
  contrasts <- read_contrasts() |>
    filter(toupper(as.character(enabled)) == "TRUE")
  output_dir <- file.path("5DESeq2", parameter_tag(padj = fdr_cutoff, lfc = logfc_cutoff))
  files <- list.files(analysis_dir, pattern = "DE_results$", recursive = TRUE, full.names = TRUE)
  if (!length(files)) stop("所选 DE_ANALYSIS_DIR 没有 DE_results；请明确指定实际分析目录")
  claim <- begin_result_stage(output_dir, list(fdr_cutoff = fdr_cutoff, logfc_cutoff = logfc_cutoff),
    c(list(contrasts = contrasts), setNames(as.list(files), basename(files))), variant_label)
  output_dir <- claim$path

  # 功能：按实验组/参照组定位一个真实结果文件，不把下划线当作可靠分隔符。
  # files 显式传入；必须唯一匹配，不能悄悄选中其他比较。
  # 接口｜read_one_contrast：按真实实验组和参照组找到唯一统计结果。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # contrast_id（必填，无默认值）：一个比较 ID 字符串；按它精确选取传入数据或对应保存目录。此标识不按下
  #   划线拆分组名，输入来源以本函数说明为准。
  # test_group（必填，无默认值）：字符组名；比较的实验组，来自样本表/比较表，正 log2FC 表示其表达高于
  #   reference_group。
  # reference_group（必填，无默认值）：字符组名；差异方向的参照组，必须来自样本表，正 log2FC 表示实验组
  #   高于该组。生成 baseline 类比较时必须明确填写。
  # files（必填，无默认值）：字符路径向量；扫描得到的 DESeq2 结果文件，按实验组和参照组精确定位唯一文件
  #   ，不能悄悄选第一个。
  # 返回/写出与边界：返回加入 gene_id/contrast_id/sampleA/sampleB 的 data.frame；文件不唯一或统计列缺失
  #   报错。
  read_one_contrast <- function(contrast_id, test_group, reference_group, files) {
    # 以明确的组名标记匹配，不把 contrast_id 拆成可能含下划线的片段。
    token <- paste0(".", test_group, "_vs_", reference_group, ".")
    candidate <- files[vapply(basename(files), function(x) grepl(token, x, fixed = TRUE), logical(1))]
    if (length(candidate) != 1) stop("无法唯一找到比较: ", contrast_id)
    result <- read_result_table(candidate, row_names = TRUE) |>
      rownames_to_column("gene_id")
    stopifnot(all(c("baseMean", "log2FoldChange", "lfcSE", "stat", "pvalue", "padj") %in% names(result)),
              !anyDuplicated(result$gene_id))
    result$contrast_id <- contrast_id
    result$sampleA <- test_group
    result$sampleB <- reference_group
    result
  }

  # 功能：合并结果并按入口 FDR/log2FC 阈值标记方向，不重新拟合 DESeq2。
  # 修改阈值后重做本段及下游集合/富集；P 值和效应量仍取原模型结果。
  de_result <- pmap_dfr(contrasts[c("contrast_id", "test_group", "reference_group")],
    read_one_contrast, files = files) |>
    mutate(direction = case_when(
      !is.na(padj) & padj <= fdr_cutoff & log2FoldChange >= logfc_cutoff ~ "up",
      !is.na(padj) & padj <= fdr_cutoff & log2FoldChange <= -logfc_cutoff ~ "down",
      TRUE ~ "ns"
    )) |>
    relocate(gene_id, contrast_id, sampleA, sampleB)
  write.table(de_result, file.path(output_dir, "de_result.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  save(de_result, file = file.path(output_dir, "de_result.RData"))
  summary <- tidyr::expand_grid(contrast_id = contrasts$contrast_id, direction = c("up", "down")) |>
    left_join(de_result |> filter(direction != "ns") |> count(contrast_id, direction),
              by = c("contrast_id", "direction")) |>
    mutate(n = replace_na(n, 0L))
  write.table(summary, file.path(output_dir, "DE_summary.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  plot <- ggplot(summary, aes(factor(contrast_id, levels = contrasts$contrast_id), n, fill = direction)) +
    geom_col(position = "dodge") + coord_flip() +
    scale_fill_manual(values = c(up = "#C65D37", down = "#216B87")) +
    labs(x = NULL, y = "Significant genes", fill = "Direction") + theme_classic(base_size = 11)
  ggsave(file.path(output_dir, "DE_summary.pdf"), plot, width = 10, height = 7)
  ggsave(file.path(output_dir, "DE_summary.png"), plot, width = 10, height = 7, dpi = 180)
  finish_result_dir(claim)
  invisible(list(output_dir = output_dir, analysis_dir = analysis_dir))
}
