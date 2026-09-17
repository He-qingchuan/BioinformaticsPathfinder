# 文件用途｜第 16 章：选择高变基因并运行指定 Mfuzz 聚类和可选模块富集。
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

# 接口｜save_time_plot：配对保存时间曲线对象。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# plot（必填，无默认值）：已经构造好的 ggplot/grob 等绘图对象；本函数格式化或保存它，不从 FASTQ 重新计
#   算。
# prefix（必填，无默认值）：字符输出路径前缀，不含 .png/.pdf 扩展名；辅助函数为同一张图保存两种格式。
# width（默认 14）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
# height（默认 8）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
# 返回/写出与边界：写同主干 PDF/PNG，使用既定曲线对象，不改变模块成员。
save_time_plot <- function(plot, prefix, width = 14, height = 8) {
  assert_fresh_plot(prefix)
  ggsave(paste0(prefix, ".pdf"), plot, width = width, height = height)
  ggsave(paste0(prefix, ".png"), plot, width = width, height = height, dpi = 160)
}
# 接口｜save_time_heatmap：在两种图形设备上调用同一个热图回调。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# draw_plot（必填，无默认值）：无参数绘图函数（回调）；在打开 PDF/PNG 设备后调用，须画同一份已准备对象
#   ，不把其返回值当成表达矩阵。
# prefix（必填，无默认值）：字符输出路径前缀，不含 .png/.pdf 扩展名；辅助函数为同一张图保存两种格式。
# width（必填，无默认值）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
# height（必填，无默认值）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
# dpi（默认 130）：正数，单位像素/英寸；控制 PNG 像素密度，不改变图幅的英寸数或统计结果。
# 返回/写出与边界：打开 PDF/PNG 后执行 draw_plot 并关闭设备；主要副作用为图片，不把闭包重新解释成分析
#   入口。
save_time_heatmap <- function(draw_plot, prefix, width, height, dpi = 130) {
  assert_fresh_plot(prefix)
  pdf(paste0(prefix, ".pdf"), width = width, height = height)
  tryCatch(draw_plot(), finally = dev.off())
  png(paste0(prefix, ".png"), width = width * dpi, height = height * dpi, res = dpi)
  tryCatch(draw_plot(), finally = dev.off())
}

# 接口｜cluster_heatmap_height：估算带/不带 GO 侧栏的时间热图高度。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# cluster_number（必填，无默认值）：正整数；当前图的模块数，用于布局高度估算，不在这个辅助函数中重新聚
#   类。
# add_go（默认 TRUE）：TRUE/FALSE；当前图是否带 GO 侧栏，参与自动画布高度计算。
# topn（默认 5）：正整数；当前辅助绘图函数每个模块最多展示的条目数，实际不足时不补出虚构条目。
# 返回/写出与边界：返回英寸高度；模块越多、GO 条目越多时按布局公式增加空间，不影响统计。
cluster_heatmap_height <- function(cluster_number, add_go = TRUE, topn = 5) {
  if (!add_go) return(15)
  # Top5 时每面板高 5 cm；增加条目时同时增高，避免文字挤在固定空间。
  panel_height <- max(5, topn)
  max(20, (panel_height * cluster_number + 0.5 * (cluster_number - 1)) / 2.54 + 2)
}

# 接口｜module_enrichment_BH：以所有聚类基因为背景计算各模块 GO 并做 BH。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# cm（必填，无默认值）：ClusterGVis::clusterData 保存的聚类 list；包含 wide.res 等成员，基因、模块和标
#   准化表达来自同一次已完成聚类。
# OrgDb_name（必填，无默认值）：已加载的 OrgDb 数据库对象，不是任意包名字字符串。主线来自实际物种的注
#   释包，非模式支线来自第 18 章自建数据库。
# Gene_id_type（必填，无默认值）：字符键类型；时间模块 GO 富集所用 OrgDb 的 ID 类型，含义同 keyType，
#   不能只改类型名称而不核实真实基因 ID。
# enrich_type（默认 "BP"）：单个 BP、MF、CC 或 ALL；指定模块 GO 富集的本体，改变时需要相应富集结果，不
#   能只重写图标题。
# minGSSize（默认 10）：正整数；与输入/背景匹配后的基因集中允许的最少基因数。提高会排除较小条目，改变
#   参与检验的条目集合。
# maxGSSize（默认 500）：正整数，且不小于 minGSSize；允许的最大基因集规模。降低会排除过大的条目，改变
#   检验范围。
# 返回/写出与边界：返回 tibble 长表，含 cluster、ID、Description、p.adjust 等；全部无条目时返回保留字
#   段的空表，校正先于 TopN 展示。
module_enrichment_BH <- function(cm, OrgDb_name, Gene_id_type, enrich_type = "BP",
                                 minGSSize = 10, maxGSSize = 500) {
  stopifnot(enrich_type %in% c("BP", "MF", "CC", "ALL"),
            minGSSize >= 1, maxGSSize >= minGSSize)
  background <- unique(cm$wide.res$gene)
  tables <- lapply(sort(unique(cm$wide.res$cluster)), function(id) {
    genes <- unique(cm$wide.res$gene[cm$wide.res$cluster == id])
    object <- clusterProfiler::enrichGO(gene = genes, universe = background,
      OrgDb = OrgDb_name, keyType = Gene_id_type, ont = enrich_type, pool = TRUE,
      pAdjustMethod = "BH", pvalueCutoff = 1, qvalueCutoff = 1,
      minGSSize = minGSSize, maxGSSize = maxGSSize, readable = FALSE)
    if (is.null(object) || !nrow(object@result)) return(NULL)
    object@result |> mutate(cluster = id, .before = 1)
  })
  result <- bind_rows(tables)
  if (!nrow(result)) return(tibble(cluster = integer(), ID = character(), Description = character(),
                                  pvalue = double(), p.adjust = double()))
  result |> arrange(cluster, p.adjust, ID)
}

# 接口｜make_enrichment_panels：从已校正模块富集表筛选和排列侧栏内容。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# enrichment_bh（必填，无默认值）：模块 GO 富集 data.frame；含 cluster、ID、Description、p.adjust 等列
#   ，使用已完成多重校正的结果而非未校正 P 值。
# cluster_ids（必填，无默认值）：模块 ID 向量；决定侧栏面板的顺序，必须对应当前热图模块，不能按字符排
#   序随意换位。
# topn（默认 5）：正整数；当前辅助绘图函数每个模块最多展示的条目数，实际不足时不补出虚构条目。
# fdr_cutoff（默认 0.05）：数值阈值，通常 0.05，范围 (0,1]；控制当前步骤的校正 P 值筛选，调小更严格。
#   各比较/富集本体分别校正，不代表全项目共同做一次 BH。
# 返回/写出与边界：返回以 C加模块ID 命名的 ggplot 列表；按 p.adjust 门槛与稳定排序取条目，无达标项明确
#   占位，不重做富集。
make_enrichment_panels <- function(enrichment_bh, cluster_ids, topn = 5, fdr_cutoff = 0.05) {
  stopifnot(length(topn) == 1, is.finite(topn), topn >= 1, topn == floor(topn),
            length(fdr_cutoff) == 1, is.finite(fdr_cutoff), fdr_cutoff > 0, fdr_cutoff <= 1)
  panels <- lapply(cluster_ids, function(id) {
    current <- enrichment_bh |> filter(cluster == id, is.finite(p.adjust), p.adjust <= fdr_cutoff) |>
      arrange(p.adjust, ID) |> slice_head(n = topn)
    if (!nrow(current)) {
      return(ggplot() + annotate("text", x = 0, y = 0, label = "No BH-significant term", size = 3) +
        xlim(-1, 1) + ylim(-1, 1) + labs(title = paste("Cluster", id)) + theme_void())
    }
    current |> mutate(score = -log10(pmax(p.adjust, .Machine$double.xmin)),
                       Description = forcats::fct_reorder(Description, score)) |>
      ggplot(aes(score, Description, fill = score)) + geom_col(show.legend = FALSE) +
      scale_fill_gradient(low = "#C7DFE8", high = "#216B87") +
      scale_y_discrete(labels = function(x) stringr::str_wrap(x, 32)) +
      labs(x = "-log10 BH-adjusted P", y = NULL, title = paste("Cluster", id)) + theme_bw(base_size = 10)
  })
  names(panels) <- paste0("C", cluster_ids)
  panels
}

# 接口｜render_cluster_variants：用已完成聚类/富集对象绘制多种曲线和热图。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# cm（必填，无默认值）：ClusterGVis::clusterData 保存的聚类 list；包含 wide.res 等成员，基因、模块和标
#   准化表达来自同一次已完成聚类。
# markGenes（必填，无默认值）：字符基因 ID 向量；在热图中显示的标签名单，应来自当前聚类的基因，不改变
#   模块分配。
# enrichment_bh（必填，无默认值）：模块 GO 富集 data.frame；含 cluster、ID、Description、p.adjust 等列
#   ，使用已完成多重校正的结果而非未校正 P 值。
# output_dir（必填，无默认值）：字符路径；本函数保存结果的目录。是否拒绝同名文件或复用旧结果以本函数下
#   面的保存步骤为准，不代表自动选择最新结果。
# layout_refresh_only（默认 FALSE）：TRUE/FALSE；内部兼容重排开关。TRUE 按本函数分支跳过部分已保存图，
#   只更新指定布局，不代表重新统计或全局禁止一切写入。
# enrichment_top_n（默认 5）：正整数；每个模块图上最多展示的 GO 条目数，不是标记基因数，只显示通过
#   enrichment_fdr 的条目。重绘入口可不重算；完整分析入口改此值仍会执行相应分析步骤。
# enrichment_fdr（默认 0.05）：数值 (0,1]；模块富集图取 p.adjust 不大于此值的 GO 条目，每个模块的检验
#   先完成 BH。没有达标条目时显示明确空结果提示。
# line_variants（默认 c("line1", "line2", "line3")）：字符向量；line1、line2、line3 对应三种
#   ClusterGVis 时间曲线展示，line3 不加模块中位数线；character() 跳过独立曲线，不改变聚类。
# label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示已选标记基因标签，TRUE 显示，c(FALSE,
#   TRUE) 保存两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
# go_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不附 GO 侧栏，TRUE 附上已有模块 GO 结果。不能用
#   TRUE 代替实际计算富集。
# label_size（默认 10）：正数；时间聚类热图中标记基因的字号，通常从 10 调整，经 genes.gp 传给绘图函数
#   ；不改变标签名单或聚类结果。
# heatmap_width（默认 NULL）：NULL 或正数（英寸）；NULL 根据是否有 GO 侧栏采用自动宽度，数值用于手动图
#   宽，不影响聚类或显著性。
# heatmap_height（默认 NULL）：NULL 或正数（英寸）；NULL 根据模块数和 GO 展示量估算高度，数值用于手动
#   图高。条目多时增高可减少拥挤。
# heatmap_dpi（默认 130）：正数，像素/英寸；时间热图 PNG 的输出密度，不改变行标准化、模块或 GO 筛选。
# 返回/写出与边界：保存所选 line/标签/GO 组合；只调展示不重新聚类，go_versions=FALSE 不读取 GO 侧栏输
#   入。
render_cluster_variants <- function(cm, markGenes, enrichment_bh, output_dir, layout_refresh_only = FALSE,
                                    enrichment_top_n = 5, enrichment_fdr = 0.05,
                                    line_variants = c("line1", "line2", "line3"),
                                    label_versions = c(FALSE, TRUE), go_versions = c(FALSE, TRUE),
                                    label_size = 10, heatmap_width = NULL, heatmap_height = NULL,
                                    heatmap_dpi = 130) {
  stopifnot(all(markGenes %in% cm$wide.res$gene),
            all(line_variants %in% c("line1", "line2", "line3")),
            is.logical(label_versions), length(label_versions) > 0, !anyNA(label_versions),
            is.logical(go_versions), length(go_versions) > 0, !anyNA(go_versions),
            label_size > 0, heatmap_dpi > 0)
  if (!is.null(heatmap_width)) stopifnot(length(heatmap_width) == 1, heatmap_width > 0)
  if (!is.null(heatmap_height)) stopifnot(length(heatmap_height) == 1, heatmap_height > 0)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  cluster_ids <- sort(unique(cm$wide.res$cluster))
  cluster_order <- seq_along(cluster_ids)
  colors <- c("#216B87", "#E0B45C", "#B7444F")
  if (!layout_refresh_only) {
    if ("line1" %in% line_variants) save_time_plot(visCluster(object = cm, plot.type = "line"), file.path(output_dir, "line1"))
    if ("line2" %in% line_variants) save_time_plot(visCluster(object = cm, plot.type = "line", ms.col = colors), file.path(output_dir, "line2"))
    if ("line3" %in% line_variants) save_time_plot(visCluster(object = cm, plot.type = "line", ms.col = colors, add.mline = FALSE),
                   file.path(output_dir, "line3"))
  }
  # 纯聚类没有富集表；未选 GO 面板时不读取不存在的富集列。
  panels <- if (any(go_versions)) make_enrichment_panels(enrichment_bh, cluster_ids,
    topn = enrichment_top_n, fdr_cutoff = enrichment_fdr) else NULL
  for (label in label_versions) {
    for (add_go in go_versions) {
      if (layout_refresh_only && !label && !(add_go && cluster_heatmap_height(length(cluster_ids), topn = enrichment_top_n) > 20)) next
      stem <- paste0("pheatmap", if (add_go) "_go" else "", if (label) "_markGenes" else "")
      # 接口｜draw_plot：在当前设备绘制外层准备好的聚类热图。
      # 参数：无显式形参；所需上层对象/输入见功能说明及下方读取语句。
      # 返回/写出与边界：无形参；读取外层 cm、标记名单、面板和排版参数等对象。只绘图，不在闭包中重新跑 Mfuzz。
      draw_plot <- function() {
        arguments <- list(object = cm, plot.type = "both", line.side = "left", column_names_rot = 45,
                           show_row_dend = FALSE, cluster.order = cluster_order)
        if (label && length(markGenes)) {
          arguments$markGenes <- markGenes
          arguments$genes.gp <- c("italic", label_size, "#23313F")
        }
        if (add_go) {
          arguments$gglist <- panels
          arguments$ggplot.panel.arg <- c(max(5, enrichment_top_n), 0.5, 11, "white", NA)
        }
        do.call(ClusterGVis::visCluster, arguments)
      }
      save_time_heatmap(draw_plot, file.path(output_dir, stem),
                         width = if (!is.null(heatmap_width)) heatmap_width else if (add_go) 17 else 11,
                         height = if (!is.null(heatmap_height)) heatmap_height else
                           cluster_heatmap_height(length(cluster_ids), add_go, topn = enrichment_top_n),
                         dpi = heatmap_dpi)
    }
  }
}

# 接口｜plot_Time_Series：选择高变基因并运行指定 Mfuzz 聚类和可选模块富集。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# top_var_prop（必填，无默认值）：单个比例 (0,1]；从过滤后的时间输入取方差最高部分，按 round(基因数×比
#   例) 选择。改变它影响聚类输入，不是去除比例。
# Clusters_num（必填，无默认值）：单个整数且至少 2；Mfuzz 模块数，必须小于选中基因数。改变它会重新分配
#   模块，不是每行图的面板数。
# markGenes_num（必填，无默认值）：非负整数；从本组合已选高变基因中优先标记的总数，不是每模块各 N 个，
#   0 不标记。只重绘用本章重绘入口；完整聚类入口改它仍可能执行整步。
# OrgDb_name（必填，无默认值）：已加载的 OrgDb 数据库对象，不是任意包名字字符串。主线来自实际物种的注
#   释包，非模式支线来自第 18 章自建数据库。
# enrich_type（必填，无默认值）：单个 BP、MF、CC 或 ALL；指定模块 GO 富集的本体，改变时需要相应富集结
#   果，不能只重写图标题。
# Gene_id_type（必填，无默认值）：字符键类型；时间模块 GO 富集所用 OrgDb 的 ID 类型，含义同 keyType，
#   不能只改类型名称而不核实真实基因 ID。
# organism_name（必填，无默认值）：字符物种代码；模式 KEGG 使用 ath/hsa/mmu 等真实代码，非模式自建通路
#   路线不靠它替代 TERM2GENE。
# input_file（默认 "10Time_Series/clustering_input_log2.tsv"）：字符路径；当前步骤使用的已准备输入文件
#   。时间聚类读取第 16 章输出的 log2 矩阵，不用原 counts 直接替代。
# output_root（默认 "10Time_Series"）：字符路径；本步骤输出根目录，函数再按比较/参数建立子目录。通常沿
#   用；试算可选新目录，但后续读取位置不会自动更新。
# seed（默认 20260907）：整数随机种子；用于需要随机过程的步骤，保持相同有助于复现，不是采样时间。改变
#   种子可能改变聚类、GSEA 或标签布局，需保留独立结果。
# enrichment_top_n（默认 5）：正整数；每个模块图上最多展示的 GO 条目数，不是标记基因数，只显示通过
#   enrichment_fdr 的条目。重绘入口可不重算；完整分析入口改此值仍会执行相应分析步骤。
# enrichment_fdr（默认 0.05）：数值 (0,1]；模块富集图取 p.adjust 不大于此值的 GO 条目，每个模块的检验
#   先完成 BH。没有达标条目时显示明确空结果提示。
# compatibility_top_n（默认 5）：正整数；原 ClusterGVis::enrichCluster 兼容展示表的 Top 数，独立于主图
#   BH 表的 enrichment_top_n。该兼容表不替代主图的多重校正结果。
# minGSSize（默认 10）：正整数；与输入/背景匹配后的基因集中允许的最少基因数。提高会排除较小条目，改变
#   参与检验的条目集合。
# maxGSSize（默认 500）：正整数，且不小于 minGSSize；允许的最大基因集规模。降低会排除过大的条目，改变
#   检验范围。
# line_variants（默认 c("line1", "line2", "line3")）：字符向量；line1、line2、line3 对应三种
#   ClusterGVis 时间曲线展示，line3 不加模块中位数线；character() 跳过独立曲线，不改变聚类。
# label_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不显示已选标记基因标签，TRUE 显示，c(FALSE,
#   TRUE) 保存两版。仅控制标签呈现，不改变点的位置、检验结果或模块成员。
# go_versions（默认 c(FALSE, TRUE)）：逻辑向量；FALSE 不附 GO 侧栏，TRUE 附上已有模块 GO 结果。不能用
#   TRUE 代替实际计算富集。
# label_size（默认 10）：正数；时间聚类热图中标记基因的字号，通常从 10 调整，经 genes.gp 传给绘图函数
#   ；不改变标签名单或聚类结果。
# heatmap_width（默认 NULL）：NULL 或正数（英寸）；NULL 根据是否有 GO 侧栏采用自动宽度，数值用于手动图
#   宽，不影响聚类或显著性。
# heatmap_height（默认 NULL）：NULL 或正数（英寸）；NULL 根据模块数和 GO 展示量估算高度，数值用于手动
#   图高。条目多时增高可减少拥挤。
# heatmap_dpi（默认 130）：正数，像素/英寸；时间热图 PNG 的输出密度，不改变行标准化、模块或 GO 筛选。
# include_module_enrichment（默认 TRUE）：TRUE/FALSE；是否计算聚类模块 GO 富集。FALSE 可只做聚类，并关
#   闭带 GO 注释的图，不能在未计算富集时把空白当无显著结果。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：保存输入子集、ClusterGVis 聚类对象、模块表、富集表及图；通过参数/输入清单保护结果，
#   不改原时间矩阵。
plot_Time_Series <- function(top_var_prop, Clusters_num, markGenes_num, OrgDb_name,
                              enrich_type, Gene_id_type, organism_name,
                              input_file = "10Time_Series/clustering_input_log2.tsv",
                              output_root = "10Time_Series", seed = 20260907,
                              enrichment_top_n = 5, enrichment_fdr = 0.05, compatibility_top_n = 5,
                              minGSSize = 10, maxGSSize = 500,
                              line_variants = c("line1", "line2", "line3"),
                              label_versions = c(FALSE, TRUE), go_versions = c(FALSE, TRUE),
                              label_size = 10, heatmap_width = NULL, heatmap_height = NULL,
                              heatmap_dpi = 130, include_module_enrichment = TRUE, variant_label = "") {
  stopifnot(length(top_var_prop) == 1, is.finite(top_var_prop), top_var_prop > 0, top_var_prop <= 1,
            length(Clusters_num) == 1, is.finite(Clusters_num), Clusters_num >= 2, Clusters_num == floor(Clusters_num),
            length(markGenes_num) == 1, is.finite(markGenes_num), markGenes_num >= 0, markGenes_num == floor(markGenes_num),
            compatibility_top_n >= 1, compatibility_top_n == floor(compatibility_top_n),
            enrichment_top_n >= 1, enrichment_top_n == floor(enrichment_top_n),
            enrichment_fdr > 0, enrichment_fdr <= 1, minGSSize >= 1, maxGSSize >= minGSSize,
            enrich_type %in% c("BP", "MF", "CC", "ALL"), length(seed) == 1, is.finite(seed))
  # 1. 读取第 2 节输入，不在函数内部悄悄更换文件或重新读取入口环境变量。
  exps_all <- read_result_table(input_file, row_names = TRUE)
  stopifnot(!anyDuplicated(rownames(exps_all)), ncol(exps_all) >= 3,
            all(is.finite(as.matrix(exps_all))))
  gene_variance <- apply(exps_all, 1, var)
  ranked_ids <- rownames(exps_all)[order(-gene_variance, rownames(exps_all))]
  keep_number <- min(length(ranked_ids), round(top_var_prop * length(ranked_ids)))
  if (keep_number <= Clusters_num) stop("高变基因数不足，请检查输入或降低模块数")
  selected_ids <- head(ranked_ids, keep_number)
  exps <- as.matrix(exps_all[selected_ids, , drop = FALSE])
  markGenes <- head(selected_ids, markGenes_num)
  if (!include_module_enrichment) go_versions <- FALSE
  parent_dir <- file.path(output_root, paste0("top_var_prop_", top_var_prop))
  output_dir <- file.path(parent_dir, paste0("Clusters_num_", Clusters_num))
  output_dir <- file.path(output_dir, parameter_tag(mark = markGenes_num, GOtop = enrichment_top_n, seed = seed))
  claim <- claim_result_dir(output_dir,
    effective_parameters(plot_Time_Series, environment(), c("OrgDb_name", "input_file", "output_root", "variant_label")),
    list(expression = input_file, annotation = annotation_fingerprint(OrgDb_name)), variant_label)
  if (claim$reuse) return(invisible(readRDS(file.path(claim$path, "cluster_object.rds"))))
  output_dir <- claim$path
  write.table(data.frame(gene_id = selected_ids, variance_before_standardisation = gene_variance[selected_ids]),
              file.path(output_dir, "selected_genes.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  writeLines(markGenes, file.path(output_dir, "marked_genes.txt"))
  # k 参考图与本次输入一起记录，不仅凭父目录旧文件存在就跳过。
  set.seed(seed)
  guide <- ClusterGVis::getClusters(exp = exps)
  save_time_plot(guide, file.path(output_dir, "Clusters_num"), width = 9, height = 7)
  # 2. 指定 Mfuzz，软件内部按行标准化；不先标准化再重新选高变基因。
  cm <- ClusterGVis::clusterData(exp = exps, cluster.method = "mfuzz", cluster.num = Clusters_num, seed = seed)
  saveRDS(cm, file.path(output_dir, "cluster_object.rds"))
  write.csv(cm$wide.res, file.path(output_dir, "cluster_metadata_df.csv"), row.names = FALSE)
  write.csv(cm$long.res, file.path(output_dir, "cluster_profiles_long.csv"), row.names = FALSE)
  # 保留原 enrichCluster 调用。该版本的展示表不包含完整 BH 信息，不能单靠这张表报告显著性。
  if (include_module_enrichment) {
    if (is.null(OrgDb_name)) stop("模块富集需要匹配的 OrgDb；纯聚类可关闭 include_module_enrichment")
    compatibility_result <- ClusterGVis::enrichCluster(object = cm, OrgDb = OrgDb_name, type = enrich_type,
    readable = TRUE, id.trans = TRUE, fromType = Gene_id_type, toType = "SYMBOL",
    organism = organism_name, pvalueCutoff = 0.05, topn = compatibility_top_n, seed = seed)
  write.csv(as.data.frame(compatibility_result), file.path(output_dir, "cluster_enrich_df.csv"), row.names = FALSE)
  # 3. 主图另做完整 BH 检验；显示多少条目不改变本表的统计量。
  enrichment_bh <- module_enrichment_BH(cm, OrgDb_name, Gene_id_type, enrich_type,
    minGSSize = minGSSize, maxGSSize = maxGSSize)
  write.table(enrichment_bh, file.path(output_dir, "cluster_enrichment_BH.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  } else {
    # 无官方注释仍可做同一 Mfuzz 聚类，不能把未检验写成无显著条目。
    enrichment_bh <- data.frame()
    go_versions <- FALSE
    writeLines("本次仅聚类，未启用官方 OrgDb 模块富集。", file.path(output_dir, "MODULE_ENRICHMENT_NOT_RUN.txt"))
  }
  writeLines(unique(cm$wide.res$gene), file.path(output_dir, "clustered_background.txt"))
  render_cluster_variants(cm, markGenes, enrichment_bh, output_dir,
    enrichment_top_n = enrichment_top_n, enrichment_fdr = enrichment_fdr,
    line_variants = line_variants, label_versions = label_versions, go_versions = go_versions,
    label_size = label_size, heatmap_width = heatmap_width, heatmap_height = heatmap_height,
    heatmap_dpi = heatmap_dpi)
  saveRDS(list(top_var_prop = top_var_prop, Clusters_num = Clusters_num, markGenes_num = markGenes_num,
    seed = seed, input_file = input_file, enrich_type = enrich_type, enrichment_top_n = enrichment_top_n,
    enrichment_fdr = enrichment_fdr, minGSSize = minGSSize, maxGSSize = maxGSSize),
    file.path(output_dir, "analysis_parameters.rds"))
  cat("完成:", output_dir, "；基因数:", nrow(exps), "\n")
  finish_result_dir(claim)
  invisible(cm)
}
