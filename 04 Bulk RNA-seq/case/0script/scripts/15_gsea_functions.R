# 文件用途｜第 15 章：以完整有效基因排序进行 GO/KEGG GSEA。
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
source("0script/scripts/14_ora_functions.R", local = TRUE)

# 接口｜save_gsea_result：从 GSEA 对象保存结果表、点图及 TopN/Top1 曲线。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# object（必填，无默认值）：已完成的 enrichResult/gseaResult 对象；结果表、统计量和条目成员均来自上游
#   分析。空对象按下面分支给出空结果提示。
# title（必填，无默认值）：字符图标题；用于标明比较或本体，不参与统计或条目排序。
# prefix（必填，无默认值）：字符输出路径前缀，不含 .png/.pdf 扩展名；辅助函数为同一张图保存两种格式。
# draw_dotplot（默认 TRUE）：TRUE/FALSE；是否保存 GSEA 的点图；不控制富集曲线，也不重新检验通路。
# refresh_layout_only（默认 FALSE）：TRUE/FALSE；内部图形刷新开关，具体跳过哪些图由下方分支决定；不能
#   把 TRUE 当成只读模式。
# term_num（默认 c(10, 20)）：正整数向量；每种图最多展示的富集条目数，如 c(10,20) 各出 Top10/Top20，只
#   取已有达标条目，不强行补足。要避免重算请选择重绘入口；完整分析入口改此值仍会运行相应分析。
# pvalue_tables（默认 c(FALSE, TRUE)）：逻辑向量；控制 Top1 富集曲线的无/有 P 值表版本，c(FALSE,TRUE)
#   两版，logical() 不画 Top1。多条目 TopN 由 term_num 独立控制。
# dpi（默认 180）：正数，单位像素/英寸；控制 PNG 像素密度，不改变图幅的英寸数或统计结果。
# 返回/写出与边界：写 TSV/PNG/PDF；无可展示结果时写状态提示并返回，Top1 表格开关与 TopN 分开。完整 RDS
#   由外层分析函数保存。
save_gsea_result <- function(object, title, prefix, draw_dotplot = TRUE, refresh_layout_only = FALSE,
                              term_num = c(10, 20), pvalue_tables = c(FALSE, TRUE), dpi = 180) {
  stopifnot(length(term_num) > 0, all(is.finite(term_num)), all(term_num >= 1), all(term_num == floor(term_num)),
            length(draw_dotplot) == 1, is.logical(draw_dotplot), !is.na(draw_dotplot),
            is.logical(pvalue_tables), !anyNA(pvalue_tables), dpi > 0)
  result <- as.data.frame(object)
  assert_fresh_files(paste0(prefix, ".tsv"))
  write.table(result, paste0(prefix, ".tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  if (!nrow(result)) {
    writeLines("当前阈值下没有显著基因集。", paste0(prefix, "_NO_SIGNIFICANT_TERMS.txt"))
    return(invisible(NULL))
  }
  order <- order(result$p.adjust, result$pvalue, result$ID)
  result <- result[order, , drop = FALSE]
  # 接口｜curve_title：为多条目 GSEA 曲线组合可读标题。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # ids（必填，无默认值）：字符条目 ID 向量；当前曲线要展示的已保存富集条目，用于找到名称并组合标题。
  # 返回/写出与边界：返回一个字符标题，名称取自外层 result 表，回退行为以现有对象内容为准；不写文件。
  curve_title <- function(ids) {
    if (length(ids) != 1) return(title)
    index <- match(ids, result$ID)
    paste(title, paste(ids, stringr::str_wrap(result$Description[index], 65)), sep = "\n")
  }
  # 仅修改绘图副本；多曲线图的长图例移到图外，避免覆盖曲线或被图幅裁掉。
  display_object <- object
  display_object@result$Description <- stringr::str_wrap(display_object@result$Description, 55)
  # 接口｜format_curve：对已构造 GSEA 曲线调整标题与图例排版。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # plot（必填，无默认值）：已经构造好的 ggplot/grob 等绘图对象；本函数格式化或保存它，不从 FASTQ 重新计
  #   算。
  # number_of_terms（必填，无默认值）：正整数；本幅 GSEA 曲线中的条目数，决定布局/标题空间，不改变通路检
  #   验。
  # 返回/写出与边界：返回格式化绘图对象，number_of_terms 只影响布局；不改运行富集分数。
  format_curve <- function(plot, number_of_terms) {
    stopifnot(inherits(plot, "gglist"), length(plot) == 3)
    plot[[1]] <- plot[[1]] + theme(
      plot.margin = margin(t = 16, r = 8, b = 4, l = 8),
      plot.title = element_text(size = 12, lineheight = 1.1, margin = margin(b = 8)),
      legend.position = if (number_of_terms > 1) "right" else "none",
      legend.justification = "center", legend.text = element_text(size = 8),
      legend.key.height = grid::unit(0.35, "cm"), legend.key.width = grid::unit(0.45, "cm"))
    plot
  }
  # 接口｜save_pair：把 GSEA 的一个绘图对象保存为两种格式。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # plot（必填，无默认值）：已经构造好的 ggplot/grob 等绘图对象；本函数格式化或保存它，不从 FASTQ 重新计
  #   算。
  # stem（必填，无默认值）：字符文件名主干，不含 .png/.pdf；与所选输出目录拼接，不代表另一组分析参数。
  # width（默认 12）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
  # height（默认 9）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
  # 返回/写出与边界：在给定主干路径保存 PDF 和 PNG，dpi 使用外层设置；不是一次新 GSEA 检验。
  save_pair <- function(plot, stem, width = 12, height = 9) {
    assert_fresh_plot(paste0(prefix, "_", stem))
    ggsave(paste0(prefix, "_", stem, ".pdf"), plot, width = width, height = height)
    ggsave(paste0(prefix, "_", stem, ".png"), plot, width = width, height = height, dpi = dpi)
  }
  for (current_term_num in term_num) {
    ids <- head(result$ID, current_term_num)
    colors <- if (length(ids) == 1) "#216B87" else grDevices::hcl.colors(length(ids), "Dark 3")
    curves <- enrichplot::gseaplot2(display_object, geneSetID = ids, title = curve_title(ids),
                                    color = colors, pvalue_table = FALSE)
    save_pair(format_curve(curves, length(ids)), paste0("top", current_term_num, "_curves"),
                14, if (length(ids) > 10) 12 else 10)
    if (draw_dotplot) {
      dots <- enrichplot::dotplot(object, showCategory = current_term_num, x = "NES", color = "p.adjust", label_format = 45) +
        ggtitle(title)
      height <- enrichment_plot_height(dots)
      if (!refresh_layout_only || height > 8) {
        save_pair(dots, paste0("top", current_term_num, "_dotplot"), 10, height)
      }
    }
  }
  for (show_table in pvalue_tables) {
    one <- enrichplot::gseaplot2(display_object, geneSetID = result$ID[1], title = curve_title(result$ID[1]),
                                color = "#216B87", pvalue_table = show_table)
    save_pair(format_curve(one, 1), paste0("top1_pvalue_table_", show_table))
  }
}

# 接口｜plot_GSEA：以完整有效基因排序进行 GO/KEGG GSEA。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# de_result（必填，无默认值）：差异结果 data.frame；必需 gene_id、contrast_id、pvalue，以及
#   ranking_column 指定的 log2FoldChange 或 stat 列。取有限排序值且 pvalue 有限的完整排序，不先按显著性
#   筛基因。
# contrast_id（必填，无默认值）：一个比较 ID 字符串；按它精确选取传入数据或对应保存目录。此标识不按下
#   划线拆分组名，输入来源以本函数说明为准。
# ranking_column（必填，无默认值）：单个列名 log2FoldChange 或 stat；取全部具有效排序值的基因，按降序
#   形成命名向量，不先筛显著差异基因。
# OrgDb_name（必填，无默认值）：已加载的 OrgDb 数据库对象，不是任意包名字字符串。主线来自实际物种的注
#   释包，非模式支线来自第 18 章自建数据库。
# keyType（必填，无默认值）：字符键类型；OrgDb 用它理解输入 gene_id，必须在该数据库 keytypes() 中存在
#   且能匹配实际 ID。
# organism_name（必填，无默认值）：字符物种代码；模式 KEGG 使用 ath/hsa/mmu 等真实代码，非模式自建通路
#   路线不靠它替代 TERM2GENE。
# output_root（默认 "9Enrichment_Analysis/GSEA"）：字符路径；本步骤输出根目录，函数再按比较/参数建立子
#   目录。通常沿用；试算可选新目录，但后续读取位置不会自动更新。
# fdr_cutoff（默认 0.05）：数值阈值，通常 0.05，范围 (0,1]；控制当前步骤的校正 P 值筛选，调小更严格。
#   各比较/富集本体分别校正，不代表全项目共同做一次 BH。
# kegg_terms（默认 NULL）：两列通路—基因对应表或 NULL；非模式通路富集使用的 TERM2GENE。NULL 走相应模式
#   物种 KEGG 路线，不自动生成自建注释。
# kegg_names（默认 NULL）：两列通路—名称表或 NULL；供自建 KEGG 结果展示用的 TERM2NAME，不决定基因成员
#   。缺名称不能伪造生物学描述。
# seed（默认 20260907）：整数随机种子；用于需要随机过程的步骤，保持相同有助于复现，不是采样时间。改变
#   种子可能改变聚类、GSEA 或标签布局，需保留独立结果。
# term_num（默认 c(10, 20)）：正整数向量；每种图最多展示的富集条目数，如 c(10,20) 各出 Top10/Top20，只
#   取已有达标条目，不强行补足。要避免重算请选择重绘入口；完整分析入口改此值仍会运行相应分析。
# ontologies（默认 c("BP", "MF", "CC", "ALL")）：字符向量；BP 生物过程、MF 分子功能、CC 细胞组分、ALL
#   合并本体。可同时分析；改变本体会改变检验的条目集合，不只是换标题。
# include_kegg（默认 TRUE）：TRUE/FALSE；FALSE 跳过 KEGG。模式物种路线使用匹配物种/ID 类型，非模式路线
#   使用保存的通路对应表；不能借用另一物种的注释。
# minGSSize（默认 10）：正整数；与输入/背景匹配后的基因集中允许的最少基因数。提高会排除较小条目，改变
#   参与检验的条目集合。
# maxGSSize（默认 500）：正整数，且不小于 minGSSize；允许的最大基因集规模。降低会排除过大的条目，改变
#   检验范围。
# simplify_cutoff（默认 0.75）：0–1 数值；GO 语义相似性去冗余门槛，不是 P 值。越低越容易将相似条目合并
#   ；原始 raw 结果仍单独保留，KEGG 不做这项 GO 简化。
# draw_dotplot（默认 TRUE）：TRUE/FALSE；是否保存 GSEA 的点图；不控制富集曲线，也不重新检验通路。
# pvalue_tables（默认 c(FALSE, TRUE)）：逻辑向量；控制 Top1 富集曲线的无/有 P 值表版本，c(FALSE,TRUE)
#   两版，logical() 不画 Top1。多条目 TopN 由 term_num 独立控制。
# plot_dpi（默认 180）：正数，单位像素/英寸；PNG 的像素密度。相同英寸下越大像素越多、文件通常越大；PDF
#   的矢量图形不靠此值提高清晰度。
# kegg_keytype（默认 "kegg"）：字符 ID 类型；传给模式物种 KEGG 接口，如 kegg。不同于 OrgDb 的 keyType
#   ；须与真实输入基因 ID 匹配，不会自动把 TAIR 改成人类 ID。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存排序、完整检验、阈值筛选、去冗余对象及曲线；不足有效输入或注释不匹配会按检查中
#   止，不预筛为仅显著基因。
plot_GSEA <- function(de_result, contrast_id, ranking_column, OrgDb_name, keyType, organism_name,
                      output_root = "9Enrichment_Analysis/GSEA", fdr_cutoff = 0.05,
                      kegg_terms = NULL, kegg_names = NULL, seed = 20260907,
                      term_num = c(10, 20), ontologies = c("BP", "MF", "CC", "ALL"), include_kegg = TRUE,
                      minGSSize = 10, maxGSSize = 500, simplify_cutoff = 0.75,
                      draw_dotplot = TRUE, pvalue_tables = c(FALSE, TRUE), plot_dpi = 180,
                      kegg_keytype = "kegg", variant_label = "") {
  stopifnot(length(term_num) > 0, all(is.finite(term_num)), all(term_num >= 1), all(term_num == floor(term_num)),
            length(ontologies) > 0, all(ontologies %in% c("BP", "MF", "CC", "ALL")),
            length(include_kegg) == 1, is.logical(include_kegg), !is.na(include_kegg),
            fdr_cutoff > 0, fdr_cutoff <= 1, minGSSize >= 1, maxGSSize >= minGSSize,
            simplify_cutoff >= 0, simplify_cutoff <= 1, length(seed) == 1, is.finite(seed))
  # 1. 只排除不可排序或没有有限检验 P 值的基因；并列值按 ID 稳定排列。
  current <- de_result[de_result$contrast_id == contrast_id, , drop = FALSE]
  stopifnot(nrow(current) > 0, ranking_column %in% names(current), !anyDuplicated(current$gene_id))
  current <- current[is.finite(current[[ranking_column]]) & is.finite(current$pvalue), , drop = FALSE]
  current <- current[order(-current[[ranking_column]], current$gene_id), , drop = FALSE]
  geneList <- setNames(current[[ranking_column]], current$gene_id)
  if (length(geneList) < 100) stop("可排序基因少于 100，请核对输入与映射")
  output_dir <- file.path(output_root,
    parameter_tag(fdr = fdr_cutoff, gs = c(minGSSize, maxGSSize), top = term_num), contrast_id, ranking_column)
  claim <- claim_result_dir(output_dir,
    effective_parameters(plot_GSEA, environment(), c("de_result", "OrgDb_name", "kegg_terms", "kegg_names", "output_root", "variant_label")),
    list(de_result = current, annotation = annotation_fingerprint(OrgDb_name),
      kegg_terms = kegg_terms, kegg_names = kegg_names), variant_label)
  if (claim$reuse) return(invisible(claim$path))
  output_dir <- claim$path
  write.table(data.frame(gene_id = names(geneList), rank_value = as.numeric(geneList)),
              file.path(output_dir, "ranking.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(paste("排序指标:", ranking_column, "；并列值按 gene_id 排序，不添加随机噪声。"),
              file.path(output_dir, "ranking_method.txt"))
  set.seed(seed)
  # 2. 保持 BH、eps=0 和固定随机行为；不为得到更小 P 值反复挑选种子。
  go_results <- setNames(lapply(ontologies, function(ont) {
    gseGO(geneList = geneList, OrgDb = OrgDb_name, keyType = keyType, ont = ont,
           minGSSize = minGSSize, maxGSSize = maxGSSize, eps = 0, pvalueCutoff = 1,
           pAdjustMethod = "BH", verbose = FALSE, seed = TRUE, BPPARAM = BiocParallel::SerialParam())
  }), paste0("GO_", ontologies))
  kegg <- if (!include_kegg) NULL else if (is.null(kegg_terms)) {
    gseKEGG(geneList = geneList, organism = organism_name, keyType = kegg_keytype,
             minGSSize = minGSSize, maxGSSize = maxGSSize, eps = 0, pvalueCutoff = 1,
             pAdjustMethod = "BH", verbose = FALSE, seed = TRUE, BPPARAM = BiocParallel::SerialParam())
  } else {
    GSEA(geneList = geneList, TERM2GENE = kegg_terms, TERM2NAME = kegg_names,
           minGSSize = minGSSize, maxGSSize = maxGSSize, eps = 0, pvalueCutoff = 1,
           pAdjustMethod = "BH", verbose = FALSE, seed = TRUE, BPPARAM = BiocParallel::SerialParam())
  }
  results <- c(go_results, if (include_kegg) list(KEGG = kegg) else list())
  saved <- list()
  for (name in names(results)) {
    object <- results[[name]]
    if (is.null(object)) {
      writeLines("没有满足映射和大小条件的基因集。", file.path(output_dir, paste0(name, "_NO_TESTABLE_TERMS.txt")))
      next
    }
    write.table(object@result, file.path(output_dir, paste0(name, "_all_tests.tsv")),
                sep = "\t", quote = FALSE, row.names = FALSE)
    table <- object@result
    keep <- is.finite(table$p.adjust) & is.finite(table$pvalue) &
      table$p.adjust <= fdr_cutoff & table$pvalue <= fdr_cutoff
    raw <- object
    raw@result <- table[keep, , drop = FALSE]
    simplified <- if (name != "KEGG" && nrow(raw@result)) {
      clusterProfiler::simplify(raw, cutoff = simplify_cutoff, by = "p.adjust", select_fun = min)
    } else raw
    saved[[name]] <- list(raw = raw, simplified = simplified)
    for (style in if (name == "KEGG") "raw" else c("raw", "simplified")) {
      save_gsea_result(saved[[name]][[style]], paste(contrast_id, ranking_column, name),
                        file.path(output_dir, paste0(name, "_", style)),
                        term_num = term_num, draw_dotplot = draw_dotplot,
                        pvalue_tables = pvalue_tables, dpi = plot_dpi)
    }
  }
  saveRDS(list(results = saved, geneList = geneList, ranking_column = ranking_column, seed = seed),
           file.path(output_dir, "GSEA_results.rds"))
  finish_result_dir(claim)
}
