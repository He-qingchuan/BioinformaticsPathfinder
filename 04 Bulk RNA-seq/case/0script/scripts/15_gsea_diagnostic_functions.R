# 文件用途｜第 15 章：按保存的排序、基因集和随机状态复算 fgsea 并核对统计。
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
# 接口｜diagnose_saved_GSEA：按保存的排序、基因集和随机状态复算 fgsea 并核对统计。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# route（必填，无默认值）：字符 main 或 diamond；分别从配置的模式/非模式 GSEA 根目录定位结果，不是直接
#   传文件路径。诊断会复算底层 fgsea 以核对已保存统计。
# contrast_id（必填，无默认值）：一个已有比较 ID 字符串；与 route/ranking 拼成保存对象的读取目录，不在
#   此函数读取样本表、比较表或差异表。
# ranking（必填，无默认值）：单个排序名 log2FoldChange 或 stat，用于定位保存目录；不从差异表重建排序，
#   使用保存的 geneList/geneSets 复算底层 fgsea 做诊断核对。
# annotation（必填，无默认值）：注释对象名称，如 GO_BP、GO_MF、GO_CC、GO_ALL 或 KEGG；必须是所选目录已
#   经保存的对象。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：返回诊断 data.frame，另存底层结果、警告与一致性表；会进行诊断重算，但不覆盖原 GSEA
#   对象或改其阈值，不一致时报错保留证据。
diagnose_saved_GSEA <- function(route, contrast_id, ranking, annotation, variant_label = "") {
  stopifnot(route %in% c("main", "diamond"), packageVersion("DOSE") == "4.4.0")
  # 来源由 project.env 明确指定；不能根据修改时间挑选另一套参数的统计结果。
  # 配置来源 GSEA_RESULT_ROOT：案例 9Enrichment_Analysis/GSEA；空模板 9Enrichment_Analysis/GSEA/fdr0.05_gs10-500_top10-20；实际以 project.env 为准。
  root <- if (route == "main") project_result("GSEA_RESULT_ROOT", "9Enrichment_Analysis/GSEA") else
    # 配置来源 NONMODEL_GSEA_RESULT_ROOT：案例 9Enrichment_Analysis/OrgDb/diamond/GSEA；空模板 9Enrichment_Analysis/OrgDb/diamond/GSEA/fdr0.05_gs10-500_top10-20；实际以 project.env 为准。
    project_result("NONMODEL_GSEA_RESULT_ROOT", "9Enrichment_Analysis/OrgDb/diamond/GSEA")
  directory <- file.path(root, contrast_id, ranking)
  cached <- readRDS(file.path(directory, "GSEA_results.rds"))
  claim <- claim_result_dir(file.path(directory, "diagnostics", annotation),
    effective_parameters(diagnose_saved_GSEA, environment(), "variant_label"),
    list(statistical_object = file.path(directory, "GSEA_results.rds")), variant_label)
  if (claim$reuse) return(invisible(claim$path))
  object <- cached$results[[annotation]]$raw
  stopifnot(!is.null(object))
  parameters <- object@params
  warning_messages <- character()
  set.seed(cached$seed)
  set.seed(.Random.seed) # 与本机 DOSE 4.4.0 的 seed=TRUE 分支一致，不是另选有利种子。
  # 这一段实际重新运行底层 fgsea，以保存的排序、基因集、参数和随机状态核对旧统计；不是仅加载图片。不改原
  #   始 GSEA 对象或为了显著性反复选种子。
  backend <- withCallingHandlers(fgsea::fgsea(
    pathways = object@geneSets, stats = object@geneList,
    minSize = parameters$minGSSize, maxSize = parameters$maxGSSize,
    eps = parameters$eps, gseaParam = parameters$exponent, nproc = 0,
    BPPARAM = BiocParallel::SerialParam()),
    warning = function(w) warning_messages <<- c(warning_messages, conditionMessage(w)))
  backend <- as.data.frame(backend)
  backend$leadingEdge <- vapply(backend$leadingEdge, function(ids) paste(ids, collapse = "/"), character(1))
  output_dir <- claim$path
  write.table(backend, file.path(output_dir, paste0(annotation, "_backend.tsv")),
                sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(if (length(warning_messages)) unique(warning_messages) else "No warning returned.",
                file.path(output_dir, paste0(annotation, "_warnings.txt")))
  original <- read.delim(file.path(directory, paste0(annotation, "_all_tests.tsv")), check.names = FALSE)
  matching <- backend[match(original$ID, backend$pathway), ]
  same <- !anyNA(matching$pathway) && all(vapply(
    list(c("pvalue", "pval"), c("p.adjust", "padj"), c("enrichmentScore", "ES"), c("NES", "NES")),
    function(columns) isTRUE(all.equal(original[[columns[1]]], matching[[columns[2]]],
                                       tolerance = 1e-10, check.attributes = FALSE)), logical(1)))
  check <- data.frame(route, contrast_id, ranking, annotation, returned_sets = nrow(backend),
    nonfinite_pvalue = sum(!is.finite(backend$pval)),
    finite_pvalue_without_error_estimate = sum(is.finite(backend$pval) & !is.finite(backend$log2err)),
    original_statistics_match = same, fgsea_version = as.character(packageVersion("fgsea")))
  write.table(check, file.path(output_dir, paste0(annotation, "_check.tsv")),
                sep = "\t", quote = FALSE, row.names = FALSE)
  print(check)
  if (!same) stop("诊断重算与已保存统计不一致；保留两份记录并检查版本、输入与随机状态，不覆盖原结果")
  finish_result_dir(claim)
  invisible(check)
}
