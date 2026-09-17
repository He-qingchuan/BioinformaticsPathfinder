# 文件用途｜第 12 章：读取入口表并对所选比较调用火山图函数。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

source("0script/tools/metadata.R", local = TRUE)
source("0script/tools/outputs.R", local = TRUE)

# 原有核心函数：只处理明确传入的数据/参数；不读取案例全局变量。
# 接口｜plot_Volcano：绘制一个比较的多种火山图及标签版本。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# de_result（必填，无默认值）：合并差异 data.frame；本函数必需 gene_id、contrast_id、log2FoldChange、
#   padj 和 pvalue。只绘制效应量/padj/pvalue 都为有限值且 padj 在 0–1 的记录，不满足者另存。
# contrast_id（必填，无默认值）：一个比较 ID 字符串；在传入 de_result$contrast_id 中精确筛选。本函数不
#   再读比较表、不按下划线拆实验组和对照组。
# p_cutoff（默认 0.05）：数值阈值 (0,1]；火山图使用的 padj 门槛。与 logfc_cutoff 共同决定图中类别和标
#   签候选，不重新计算 P 值。
# logfc_cutoff（默认 1）：正数（必须 >0）；绝对 log2FC 门槛，1 为两倍变化。与 padj 门槛共同定义绘图类
#   别与标签候选，0 在此接口会被拒绝，不重新拟合 DESeq2。
# top_n（默认 5）：非负整数；火山图上调、下调各最多标注多少个基因，5 改为 10 表示每方向最多 10 个，0
#   不选标签。先达阈值再排序，不用非显著基因补足名额。
# output_root（默认 "7volcano"）：字符路径；本步骤输出根目录，函数再按比较/参数建立子目录。通常沿用；
#   试算可选新目录，但后续读取位置不会自动更新。
# methods（默认 c("enhanced", "classic", "gradient")）：字符向量；enhanced、classic、gradient 对应三种
#   火山图。可全部保留；展示风格不同但取自同一份检验结果。
# label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示候选基因标签，TRUE 显示，c(FALSE,TRUE)
#   保存两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
# label_size（默认 3）：正数；火山图基因标签字号，默认 3，传入相应绘图库标签设置。标签多时可调小或增大
#   图幅，不是 PNG 的 dpi。
# width（默认 10）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
# height（默认 8）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
# dpi（默认 180）：正数，单位像素/英寸；控制 PNG 像素密度，不改变图幅的英寸数或统计结果。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存绘图数据、被跳过的无效检验记录、标签表和 PNG/PDF；图上有限下界替换只发生在副本
#   ，不改原 padj。
plot_Volcano <- function(de_result, contrast_id, p_cutoff = 0.05, logfc_cutoff = 1,
                         top_n = 5, output_root = "7volcano",
                         methods = c("enhanced", "classic", "gradient"),
                         label_versions = c(FALSE, TRUE), label_size = 3,
                         width = 10, height = 8, dpi = 180, variant_label = "") {
  stopifnot(length(top_n) == 1, is.finite(top_n), top_n >= 0, top_n == floor(top_n),
            length(p_cutoff) == 1, is.finite(p_cutoff), p_cutoff > 0, p_cutoff <= 1,
            length(logfc_cutoff) == 1, is.finite(logfc_cutoff), logfc_cutoff > 0,
            length(methods) > 0, all(methods %in% c("enhanced", "classic", "gradient")),
            is.logical(label_versions), length(label_versions) > 0, !anyNA(label_versions),
            label_size > 0, width > 0, height > 0, dpi > 0)
  # 1. 选取比较，保留未画出的记录，避免把缺失检验值当成正常点。
  current <- de_result[de_result$contrast_id == contrast_id, , drop = FALSE]
  if (!nrow(current)) stop("没有找到比较: ", contrast_id)
  # 同一比较的 Top5、Top10 和不同阈值各有自己的图片/标签/数据目录。
  output_dir <- file.path(output_root, contrast_id,
    parameter_tag(top = top_n, padj = p_cutoff, lfc = logfc_cutoff))
  claim <- claim_result_dir(output_dir,
    parameters = list(top_n = top_n, p_cutoff = p_cutoff, logfc_cutoff = logfc_cutoff,
      methods = methods, label_versions = label_versions, label_size = label_size,
      width = width, height = height, dpi = dpi, function_code_sha256 = result_digest(body(plot_Volcano))),
    inputs = list(de_result = current), variant_label = variant_label)
  if (claim$reuse) return(invisible(claim$path))
  output_dir <- claim$path
  valid <- is.finite(current$log2FoldChange) & is.finite(current$padj) &
    is.finite(current$pvalue) & current$padj >= 0 & current$padj <= 1
  write.table(current[!valid, , drop = FALSE], file.path(output_dir, "not_plotted.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  current <- current[valid, , drop = FALSE]
  if (!nrow(current)) {
    writeLines("没有可绘制的有效检验结果。", file.path(output_dir, "NO_PLOTTABLE_GENES.txt"))
    finish_result_dir(claim)
    return(invisible(NULL))
  }
  # 2. 精确零 P 值只在绘图列设下界；原 padj 保留，统计排名仍用原值。
  positive <- current$padj[current$padj > 0]
  floor <- if (length(positive)) max(.Machine$double.xmin, min(positive) / 10) else 1e-300
  current$padj_plot <- pmax(current$padj, floor)
  current$minus_log10_padj <- -log10(current$padj_plot)
  current$plot_class <- case_when(
    current$padj <= p_cutoff & current$log2FoldChange >= logfc_cutoff ~ "Up",
    current$padj <= p_cutoff & current$log2FoldChange <= -logfc_cutoff ~ "Down",
    TRUE ~ "Not significant"
  )
  current$plot_class <- factor(current$plot_class, levels = c("Not significant", "Down", "Up"))
  # 3. 按 padj、绝对效应量、ID 排序；每个方向各取 top_n，不用非显著基因凑数。
  labels <- current |>
    filter(plot_class != "Not significant") |>
    arrange(padj, desc(abs(log2FoldChange)), gene_id) |>
    group_by(plot_class) |> slice_head(n = top_n) |> ungroup()
  write.table(labels[c("gene_id", "plot_class", "log2FoldChange", "padj")],
              file.path(output_dir, "labeled_genes.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write.table(current, file.path(output_dir, "plot_data.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  # 接口｜save_plot_pair：把当前绘图对象配对保存为 PDF 和 PNG。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # plot（必填，无默认值）：已经构造好的 ggplot/grob 等绘图对象；本函数格式化或保存它，不从 FASTQ 重新计
  #   算。
  # name（必填，无默认值）：当前图文件名主干；与该闭包内的输出目录拼接，分别补 .pdf/.png。
  # 返回/写出与边界：写两种同主干图片；返回值不是统计结果。内部目录/分辨率若未列为形参则来自外层函数闭包。
  save_plot_pair <- function(plot, name) {
    # 内部保存函数直接使用外层收到的图幅参数，不重新写死尺寸。
    ggsave(file.path(output_dir, paste0(name, ".pdf")), plot, width = width, height = height)
    ggsave(file.path(output_dir, paste0(name, ".png")), plot, width = width, height = height, dpi = dpi)
  }
  # 4. EnhancedVolcano 的四种颜色表示阈值组合，并非上调/下调四类。
  if ("enhanced" %in% methods) for (labeled in label_versions) {
    enhanced <- EnhancedVolcano(
      current, lab = current$gene_id,
      selectLab = if (labeled && nrow(labels)) labels$gene_id else "",
      x = "log2FoldChange", y = "padj_plot", title = gsub("_vs_", " vs ", contrast_id),
      ylab = "-log10 adjusted P",
      subtitle = "DESeq2: adjusted P and effect size",
      pCutoff = p_cutoff, FCcutoff = logfc_cutoff,
      pointSize = 1.5, labSize = label_size, colAlpha = 0.8,
      col = c("#AAAAAA", "#216B87", "#C77C3D", "#B44339"),
      legendLabels = c("Neither cutoff", "Fold change only", "Adjusted P only", "Both cutoffs"),
      boxedLabels = labeled, drawConnectors = labeled, max.overlaps = Inf,
      legendPosition = "right"
    )
    save_plot_pair(enhanced, paste0("volcano_enhanced_labels_", labeled))
  }
  # 5. 经典图与渐变图共享坐标、阈值和数据，展示风格不改变点的位置。
  common <- ggplot(current, aes(log2FoldChange, minus_log10_padj)) +
    geom_vline(xintercept = c(-logfc_cutoff, logfc_cutoff), linetype = "dashed", colour = "grey60") +
    geom_hline(yintercept = -log10(p_cutoff), linetype = "dashed", colour = "grey60") +
    labs(title = gsub("_vs_", " vs ", contrast_id), x = "log2 fold change", y = "-log10 adjusted P") +
    theme_classic(base_size = 12)
  classic <- common + geom_point(aes(colour = plot_class), size = 1.2, alpha = 0.75) +
    scale_colour_manual(values = c("Not significant" = "#AAAAAA", Down = "#216B87", Up = "#C65D37"), drop = FALSE) +
    labs(colour = NULL)
  gradient <- common +
    geom_point(aes(size = minus_log10_padj, shape = plot_class, colour = minus_log10_padj), alpha = 0.8) +
    scale_shape_manual(values = c("Not significant" = 1, Down = 6, Up = 2), drop = FALSE) +
    scale_colour_gradientn(colours = c("#39489F", "#39BBEC", "#FFA500", "#F38466", "#B81F25")) +
    scale_size_continuous(range = c(0.5, 4)) +
    guides(size = "none") + labs(colour = "-log10 adjusted P", shape = NULL) + theme_bw(base_size = 12)
  for (method in intersect(c("classic", "gradient"), methods)) {
    clean <- if (method == "classic") classic else gradient
    labeled <- clean + geom_text_repel(data = labels, aes(label = gene_id), size = label_size,
                                       max.overlaps = Inf, min.segment.length = 0, show.legend = FALSE)
    if (FALSE %in% label_versions) save_plot_pair(clean, paste0("volcano_", method, "_labels_FALSE"))
    if (TRUE %in% label_versions) save_plot_pair(labeled, paste0("volcano_", method, "_labels_TRUE"))
  }
  finish_result_dir(claim)
  invisible(list(data = current, labels = labels, output_dir = output_dir))
}

# 接口｜run_volcano：读取入口表并对所选比较调用火山图函数。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# comparison_ids（默认 NULL）：字符向量或 NULL；NULL 读取比较表中的全部启用比较，指定 ID 则只处理这些
#   比较。ID 必须与 contrasts.tsv 和差异表一致，不从文件名猜组名。
# top_n（默认 5）：非负整数；火山图上调、下调各最多标注多少个基因，5 改为 10 表示每方向最多 10 个，0
#   不选标签。先达阈值再排序，不用非显著基因补足名额。
# p_cutoff（默认 as.numeric(Sys.getenv("FDR_CUTOFF"))）：数值阈值 (0,1]；火山图使用的 padj 门槛。与
#   logfc_cutoff 共同决定图中类别和标签候选，不重新计算 P 值。
# logfc_cutoff（默认 as.numeric(Sys.getenv("LOG2FC_CUTOFF"))）：正数（必须 >0）；传给火山图核心函数的
#   绝对 log2FC 门槛，1 为两倍变化，0 会被拒绝。修改只改变图中分类/标签，不重拟合 DESeq2。
# methods（默认 c("enhanced", "classic", "gradient")）：字符向量；enhanced、classic、gradient 对应三种
#   火山图。可全部保留；展示风格不同但取自同一份检验结果。
# label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示候选基因标签，TRUE 显示，c(FALSE,TRUE)
#   保存两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
# label_size（默认 3）：正数；火山图基因标签字号，默认 3，传入相应绘图库标签设置。标签多时可调小或增大
#   图幅，不是 PNG 的 dpi。
# width（默认 10）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
# height（默认 8）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
# dpi（默认 180）：正数，单位像素/英寸；控制 PNG 像素密度，不改变图幅的英寸数或统计结果。
# output_root（默认 "7volcano"）：字符路径；本步骤输出根目录，函数再按比较/参数建立子目录。通常沿用；
#   试算可选新目录，但后续读取位置不会自动更新。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：每个比较分别保存图和来源记录，不重新拟合 DESeq2。函数默认值只在本次调用省略该参数时
#   生效。
run_volcano <- function(comparison_ids = NULL,
  top_n = 5,
  p_cutoff = as.numeric(Sys.getenv("FDR_CUTOFF")),
  logfc_cutoff = as.numeric(Sys.getenv("LOG2FC_CUTOFF")),
  methods = c("enhanced", "classic", "gradient"),
  label_versions = c(FALSE, TRUE),
  label_size = 3,
  width = 10,
  height = 8,
  dpi = 180,
  output_root = "7volcano",
  variant_label = "") {
  source("0script/tools/metadata.R", local = TRUE)
  source("0script/tools/outputs.R", local = TRUE)
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  # 功能：加载已有差异结果和比较表，不重新进行差异检验。
  # 输入：第 10 章 de_result.tsv、入口 contrasts.tsv。
  # 输出：内存中的 de_result、contrasts，供后续函数和调用共同使用。
  library(tidyverse)
  library(EnhancedVolcano)
  library(ggrepel)
  readRenviron("0script/project.env")
  set.seed(as.integer(Sys.getenv("RANDOM_SEED")))
  # 基因 ID 按文本保留，包括 NCBI 数字 ID；其余统计列仍正常读为数值。
  de_result <- read.delim(project_result("DE_RESULT_FILE", "5DESeq2/de_result.tsv"),
    check.names = FALSE, colClasses = c(gene_id = "character", contrast_id = "character"))
  contrasts <- read_contrasts() |>
    filter(toupper(as.character(enabled)) == "TRUE")
  stopifnot(nrow(contrasts) > 0)

  if (is.null(comparison_ids)) comparison_ids <- contrasts$contrast_id

  # 功能：为一个比较生成指定火山图，同时保存实际绘图数据和标签名单。
  # 输入：de_result 为完整合并表；contrast_id 必须存在于比较表/结果表。
  # 参数：top_n 按方向计数；methods 与 label_versions 控制输出组合。
  # 输出：output_root/contrast_id 下的 PDF、PNG、labeled_genes.tsv、plot_data.tsv。
  # 这里只处理绘图副本，不修改传入的差异结果。


  # 功能：把入口参数逐项传给函数，生成选定比较和样式。
  # top_n = top_n 的左侧是函数形参，右侧是入口变量；此处不再写死 5。
  stopifnot(all(comparison_ids %in% contrasts$contrast_id))
  for (id in comparison_ids) {
    plot_Volcano(de_result = de_result, contrast_id = id,
      p_cutoff = p_cutoff, logfc_cutoff = logfc_cutoff, top_n = top_n,
      methods = methods, label_versions = label_versions, label_size = label_size,
      width = width, height = height, dpi = dpi, output_root = output_root,
      variant_label = variant_label)
  }
  # 每个结果目录已保存 plot_data.tsv 和输入摘要；无需再覆盖根目录的旧 de_result.RData。
  invisible(list(output_root = output_root))
}
