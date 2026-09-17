# 文件用途｜第 09 章：从 TMM 表达查看相关性、PCA、样本树与表达基因数。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜run_sample_relationships：从 TMM 表达查看相关性、PCA、样本树与表达基因数。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# removeVar（默认 0.3）：0 到 1 之间且小于 1 的比例；在正方差基因中再去除低变异部分，0.3 指去掉低变异
#   的 30%，不是保留 30%。改变 PCA 使用的基因集合。
# correlation_method（默认 "pearson"）：字符值 pearson 或 spearman；前者衡量线性关系，后者按秩计算。本
#   函数对 log2(TMM+1) 计算样本相关，不更改原矩阵。
# correlation_orders（默认 c("clustered", "time_order")）：字符向量；clustered 按层次聚类排列，
#   time_order 按样本表的组/时间顺序排列。可同时保留，相关系数本身不因换序而变化。
# number_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不在相关性热图单元格写数字，TRUE 显示相关系
#   数；c(FALSE, TRUE) 保存两种。
# pca_x（默认 "PC1"）：主成分名称字符串，如 PC1；必须在本次 PCA 中存在，用作横轴，不能与 pca_y 相同。
# pca_y（默认 "PC2"）：主成分名称字符串，如 PC2；必须在本次 PCA 中存在，用作纵轴，更换它仅改变查看的投
#   影。
# label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示样本标签，TRUE 显示，c(FALSE,TRUE) 保存
#   两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
# encircle_versions（默认 c(FALSE, TRUE)）：逻辑向量；控制 PCA 分组包围线的无/有版本。包围线是视觉辅助
#   ，不是置信区间，也不构成组间显著性检验。
# expression_threshold（默认 1）：非负数，单位为输入 TMM 表达量；统计组平均表达量大于该值的基因数，不
#   是 P 值，也不是 TPM 门槛。
# output_dir（默认 "4SampleHeatmapPCA"）：字符路径；本函数保存结果的目录。是否拒绝同名文件或复用旧结果
#   以本函数下面的保存步骤为准，不代表自动选择最新结果。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存多种标签/排列图、相应统计表与来源清单；不可见返回 output_dir，不自动排除异常样
#   本。
run_sample_relationships <- function(removeVar = 0.3,
  correlation_method = "pearson",
  correlation_orders = c("clustered", "time_order"),
  number_versions = c(FALSE, TRUE),
  pca_x = "PC1",
  pca_y = "PC2",
  label_versions = c(FALSE, TRUE),
  encircle_versions = c(FALSE, TRUE),
  expression_threshold = 1,
  output_dir = "4SampleHeatmapPCA",
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：加载包并读取通用项目参数；随后集中设置本章分析和显示选项。
  library(tidyverse)
  library(pheatmap)
  library(PCAtools)
  library(RColorBrewer)
  readRenviron("0script/project.env")
  set.seed(as.integer(Sys.getenv("RANDOM_SEED")))

  # 功能：设置样本关系图参数；修改过滤比例会重做 PCA，修改标签只需重绘。
  stopifnot(removeVar >= 0, removeVar < 1, expression_threshold >= 0,
            correlation_method %in% c("pearson", "spearman"))

  # 功能：依据样本表统一矩阵顺序和分组颜色，显式检查重复名与缺失样本。
  # 组别时间全部为 NA 时按普通分组处理；不凭文件名推断时间。
  output_dir <- file.path(output_dir, parameter_tag(cor = correlation_method, removeVar = removeVar,
    axes = c(pca_x, pca_y), expr = expression_threshold))
  claim <- begin_result_stage(output_dir,
    list(removeVar = removeVar, correlation_method = correlation_method,
      correlation_orders = correlation_orders, number_versions = number_versions,
      pca_x = pca_x, pca_y = pca_y, label_versions = label_versions,
      encircle_versions = encircle_versions, expression_threshold = expression_threshold,
      # 配置来源 RANDOM_SEED：示例/模板默认 20260907；实际以 project.env 为准。
      seed = Sys.getenv("RANDOM_SEED")),
    # 配置来源 TMM_MATRIX：示例/模板默认 3Salmon/quanti/gene.TMM.EXPR.matrix；实际以 project.env 为准。
    list(expression = project_result("TMM_MATRIX", "3Salmon/quanti/gene.TMM.EXPR.matrix"), samples = "0script/samples.tsv"), variant_label)
  output_dir <- claim$path
  gene_exp <- as.data.frame(read_expression(project_result("TMM_MATRIX", "3Salmon/quanti/gene.TMM.EXPR.matrix"), read_samples()), check.names = FALSE)
  samples <- read_samples()
  stopifnot(!anyDuplicated(samples$sample_id), setequal(colnames(gene_exp), samples$sample_id))
  time_design <- unique(samples[c("timepoint", "time_hour")])
  stopifnot(!anyDuplicated(time_design$timepoint))
  is_time_series <- all(is.finite(time_design$time_hour))
  if (!is_time_series && !all(is.na(time_design$time_hour))) stop("组别时间必须全部有效，或普通项目全部为 NA")
  if (is_time_series) time_design <- time_design[order(time_design$time_hour), , drop = FALSE]
  group_colors <- setNames(scales::hue_pal()(nrow(time_design)), time_design$timepoint)
  samples$timepoint <- factor(samples$timepoint, levels = time_design$timepoint)
  samples <- samples[order(samples$timepoint, samples$replicate), , drop = FALSE]
  gene_exp <- gene_exp[, samples$sample_id, drop = FALSE]
  stopifnot(all(is.finite(as.matrix(gene_exp))), all(as.matrix(gene_exp) >= 0))
  sample_info <- data.frame(group = samples$timepoint, replicate = samples$replicate,
                            row.names = samples$sample_id)
  log_exp <- log2(as.matrix(gene_exp) + 1)

  # 功能：计算样本相关矩阵，保存聚类/固定顺序以及有/无数值的图。
  # output_dir 为输出目录；dpi 只影响 PNG，矩阵以完整精度保存。
  # 保存具体 plot 对象，避免 ggsave 默认保存了上一张图。
  # 接口｜save_plot_pair：把当前绘图对象配对保存为 PDF 和 PNG。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # plot（必填，无默认值）：已经构造好的 ggplot/grob 等绘图对象；本函数格式化或保存它，不从 FASTQ 重新计
  #   算。
  # stem（必填，无默认值）：字符文件名主干，不含 .png/.pdf；与所选输出目录拼接，不代表另一组分析参数。
  # width（默认 9）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
  # height（默认 7）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
  # output_dir（默认 "4SampleHeatmapPCA"）：字符路径；本函数保存结果的目录。是否拒绝同名文件或复用旧结果
  #   以本函数下面的保存步骤为准，不代表自动选择最新结果。
  # 返回/写出与边界：写两种同主干图片；返回值不是统计结果。内部目录/分辨率若未列为形参则来自外层函数闭包。
  save_plot_pair <- function(plot, stem, width = 9, height = 7, output_dir = "4SampleHeatmapPCA") {
    ggsave(file.path(output_dir, paste0(stem, ".pdf")), plot, width = width, height = height)
    ggsave(file.path(output_dir, paste0(stem, ".png")), plot, width = width, height = height, dpi = 180)
  }

  # 相关系数保留完整精度用于聚类，只在单元格文字中四舍五入。
  sample_cor <- cor(log_exp, method = correlation_method)
  stopifnot(all(is.finite(sample_cor)))
  write.table(cbind(sample_id = rownames(sample_cor), sample_cor),
              file.path(output_dir, "sample_correlation.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  variants <- expand.grid(order = correlation_orders, numbers = number_versions,
                           stringsAsFactors = FALSE)
  for (i in seq_len(nrow(variants))) {
    clustered <- variants$order[i] == "clustered"
    stem <- paste0("sample_correlation_", variants$order[i], "_numbers_", variants$numbers[i])
    for (extension in c("pdf", "png")) {
      pheatmap(sample_cor, color = colorRampPalette(brewer.pal(9, "YlOrRd"))(100),
               cluster_rows = clustered, cluster_cols = clustered,
               annotation_row = sample_info["group"], annotation_col = sample_info["group"],
               annotation_colors = list(group = group_colors), annotation_names_row = FALSE,
               display_numbers = variants$numbers[i], number_format = "%.2f",
               fontsize = 8, fontsize_number = 6, angle_col = 45, border_color = NA,
               filename = file.path(output_dir, paste0(stem, ".", extension)), width = 11, height = 10)
    }
  }

  # 接口｜draw_sample_tree：在当前设备绘制已有样本层次聚类树。
  # 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
  # 返回/写出与边界：无形参；使用外层 tree/samples 等对象，向当前图形设备绘图，不重新定义样本分组。
  draw_sample_tree <- function() {
    plot(hclust(dist(t(log_exp))), main = "Sample clustering", xlab = "", sub = "Euclidean distance: log2(TMM + 1)")
  }
  pdf(file.path(output_dir, "sample_cluster_tree.pdf"), width = 11, height = 7)
  draw_sample_tree(); dev.off()
  png(file.path(output_dir, "sample_cluster_tree.png"), width = 1980, height = 1260, res = 180)
  draw_sample_tree(); dev.off()

  # 功能：对非零方差行进行 PCA；center=TRUE、scale=FALSE 沿用已核对的分析口径。
  # 先去除完全无变化的行；不能在单位方差标准化之后再按方差挑选基因。
  variable <- apply(log_exp, 1, var) > 0
  stopifnot(sum(variable) > 2)
  pca_result <- PCAtools::pca(log_exp[variable, , drop = FALSE], metadata = sample_info,
                             removeVar = removeVar, center = TRUE, scale = FALSE)

  # 功能：绘制已有 PCA 对象，不重新计算 PCA；可选择坐标、标签、分组轮廓。
  # p 必须来自 PCAtools::pca；包围区域不是置信区间，ellipse 保持关闭。
  # 接口｜plot_pca：按指定主成分组合保存多套样本标签和包围线图。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # p（必填，无默认值）：PCAtools::pca 返回的分析对象，含旋转坐标和方差解释量。
  # group_colors（必填，无默认值）：带分组名称的颜色向量；名称须覆盖样本中的各组，以名称匹配而非按碰巧的
  #   颜色顺序。
  # x（默认 "PC1"）：横轴主成分名称，如 PC1。
  # y（默认 "PC2"）：纵轴主成分名称，如 PC2，不与 x 相同。
  # label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示样本标签，TRUE 显示，c(FALSE,TRUE) 保存
  #   两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
  # encircle_versions（默认 c(FALSE, TRUE)）：逻辑向量；控制 PCA 分组包围线的无/有版本。包围线是视觉辅助
  #   ，不是置信区间，也不构成组间显著性检验。
  # output_dir（默认 "4SampleHeatmapPCA"）：字符路径；本函数保存结果的目录。是否拒绝同名文件或复用旧结果
  #   以本函数下面的保存步骤为准，不代表自动选择最新结果。
  # 返回/写出与边界：循环保存对应 PNG/PDF；不重新拟合 PCA，主要副作用为输出图片。
  plot_pca <- function(p, group_colors, x = "PC1", y = "PC2",
                         label_versions = c(FALSE, TRUE), encircle_versions = c(FALSE, TRUE),
                         output_dir = "4SampleHeatmapPCA") {
    stopifnot(x %in% colnames(p$rotated), y %in% colnames(p$rotated), x != y,
              is.logical(label_versions), length(label_versions) > 0, !anyNA(label_versions),
              is.logical(encircle_versions), length(encircle_versions) > 0, !anyNA(encircle_versions))
    dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
    for (labeled in label_versions) {
      for (encircled in encircle_versions) {
        plot <- PCAtools::biplot(
          p, x = x, y = y, colby = "group", colkey = group_colors, colLegendTitle = "Group",
          lab = if (labeled) rownames(p$metadata) else NULL,
          hline = 0, vline = 0, encircle = encircled, encircleFill = encircled,
          ellipse = FALSE, max.overlaps = Inf, legendPosition = "right"
        )
        stem <- paste0("pca_labels_", labeled, "_encircle_", encircled)
        save_plot_pair(plot, stem, output_dir = output_dir)
      }
    }
    save_plot_pair(PCAtools::screeplot(p), "pca_variance", 8, 6, output_dir = output_dir)
  }

  # 功能：显式传入显示选项，并保存 PCA 得分和方差解释率。
  # 换坐标或样式试绘时将 output_dir 改为子目录，避免覆盖同名默认图。
  plot_pca(p = pca_result, group_colors = group_colors, x = pca_x, y = pca_y,
    label_versions = label_versions, encircle_versions = encircle_versions, output_dir = output_dir)
  write.table(cbind(sample_id = rownames(pca_result$rotated), pca_result$rotated),
              file.path(output_dir, "pca_scores.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(data.frame(component = names(pca_result$variance), percent = pca_result$variance),
              file.path(output_dir, "pca_variance.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)

  # 功能：按组计算平均 TMM 表达量，统计超过入口阈值的基因数。
  # 只有真实时间设计才画折线；普通分组保留柱状图。
  # 分组取均值依赖样本表，不拆解名字中的下划线。
  group_levels <- levels(samples$timepoint)
  gene_exp_avg <- vapply(group_levels, function(group) {
    rowMeans(gene_exp[, samples$sample_id[samples$timepoint == group], drop = FALSE])
  }, numeric(nrow(gene_exp)))
  rownames(gene_exp_avg) <- rownames(gene_exp)
  expressed_count <- data.frame(timepoint = factor(group_levels, levels = group_levels),
                                time_hour = time_design$time_hour, genes = colSums(gene_exp_avg > expression_threshold))
  write.table(expressed_count, file.path(output_dir, "expressed_gene_count.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  count_bar <- ggplot(expressed_count, aes(timepoint, genes, fill = timepoint)) +
    geom_col(show.legend = FALSE) +
    labs(x = "Group", y = paste("Genes with mean TMM expression >", expression_threshold)) + theme_classic(base_size = 12)
  save_plot_pair(count_bar, "expressed_gene_count_bar", 9, 5, output_dir = output_dir)
  if (is_time_series) {
    count_line <- ggplot(expressed_count, aes(time_hour, genes)) +
      geom_line(colour = "#216B87", linewidth = 0.8) + geom_point(colour = "#216B87", size = 2.5) +
      scale_x_continuous(breaks = time_design$time_hour) +
      labs(x = "Sampling time (h)", y = paste("Genes with mean TMM expression >", expression_threshold)) + theme_classic(base_size = 12)
    save_plot_pair(count_line, "expressed_gene_count_line", 9, 5, output_dir = output_dir)
  }
  save(gene_exp, gene_exp_avg, sample_info, pca_result, samples,
        file = file.path(output_dir, "gene_exp.RData"))
  summary <- data.frame(metric = c("min_pairwise_correlation", "max_pairwise_correlation", "PC1_percent", "PC2_percent"),
                        value = c(range(sample_cor[lower.tri(sample_cor)]), pca_result$variance[1:2]))
  write.table(summary, file.path(output_dir, "sample_relationship_summary.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  finish_result_dir(claim)
  invisible(list(output_dir = output_dir))
}
