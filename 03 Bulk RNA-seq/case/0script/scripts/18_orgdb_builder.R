# 文件用途｜第 18 章：统计代表基因在各类注释中的覆盖范围；把 eggNOG 注释整理成按基因 ID 查询的本地
#   OrgDb。
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

# 接口｜plot_annotation_coverage：统计代表基因在各类注释中的覆盖范围。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# method（默认 "diamond"）：字符路线名；当前非模式实现仅接受 diamond，不能填一个未实现的方法名称来切换
#   软件。
# width（默认 10）：正数，单位英寸；画布宽度。仅改变排版，PNG 像素宽约为 width × dpi。
# height（默认 6）：正数，单位英寸；画布高度。仅改变排版，PNG 像素高约为 height × dpi。
# dpi（默认 180）：正数，单位像素/英寸；控制 PNG 像素密度，不改变图幅的英寸数或统计结果。
# plot_output_dir（默认 NULL）：NULL 或字符路径；NULL 沿用注释 output 目录，给新路径可另存覆盖率图片。
#   注意覆盖率 TSV 仍写原注释 output 目录。
# 返回/写出与边界：写 annotation_coverage.tsv 和覆盖率 PDF/PNG；分母为所有代表基因。图片可另存但统计表
#   仍写原 output，当前函数不是防覆盖重绘接口。
plot_annotation_coverage <- function(method = "diamond", width = 10, height = 6, dpi = 180,
                                       plot_output_dir = NULL) {
  stopifnot(identical(method, "diamond"))
  route_dir <- file.path("9Enrichment_Analysis/OrgDb", method)
  output_dir <- file.path(route_dir, "output")
  representatives <- read.delim("9Enrichment_Analysis/OrgDb/representatives/validated_representatives.tsv")
  seeds <- read.delim(file.path(output_dir, "annotation.emapper.seed_orthologs"),
                      header = FALSE, comment.char = "#", quote = "")
  annotations <- read.delim(file.path(output_dir, "annotation.emapper.annotations"),
                            header = FALSE, comment.char = "#", quote = "")
  go_table <- read.delim(file.path(output_dir, "go_table.tsv"))
  ko_table <- read.delim(file.path(output_dir, "ko_table.tsv"))
  pathway_table <- read.delim(file.path(output_dir, "pathway_table.tsv"))
  package_name <- readLines(file.path(route_dir, "orgdb/custom_orgdb_package.txt"))
  sqlite <- list.files(file.path(route_dir, "orgdb/R_Library", package_name, "extdata"),
                       pattern = "sqlite$", full.names = TRUE)
  stopifnot(length(sqlite) == 1, all(annotations[[1]] %in% seeds[[1]]),
            all(seeds[[1]] %in% representatives$gene_id))
  db <- AnnotationDbi::loadDb(sqlite)
  usable_go <- AnnotationDbi::select(db, keys = representatives$gene_id,
                                    keytype = "GID", columns = "GO")
  # 覆盖率分母是全部代表基因；种子命中、注释记录、来源 GO、OrgDb 可用 GO、KO、通路分别计数，不能将搜索命
  #   中等同于拥有完整功能注释。
  coverage <- data.frame(
    annotation = c("Search seed hit", "Annotation record", "GO (source)",
                    "GO (OrgDb)", "KEGG KO", "KEGG pathway"),
    genes = c(n_distinct(seeds[[1]]), n_distinct(annotations[[1]]), n_distinct(go_table$GID),
              n_distinct(usable_go$GID[!is.na(usable_go$GO)]),
              n_distinct(ko_table$GID), n_distinct(pathway_table$GID)),
    total_representative_genes = nrow(representatives))
  coverage$percent <- 100 * coverage$genes / coverage$total_representative_genes
  write.table(coverage, file.path(output_dir, "annotation_coverage.tsv"),
              sep = "\t", quote = FALSE, row.names = FALSE)
  coverage$annotation <- factor(coverage$annotation, levels = rev(coverage$annotation))
  plot <- ggplot(coverage, aes(genes, annotation)) + geom_col(fill = "#216B87") +
    geom_text(aes(label = sprintf("%d (%.1f%%)", genes, percent)), hjust = -0.1, size = 3.5) +
    scale_x_continuous(limits = c(0, nrow(representatives) * 1.2)) +
    labs(x = "Genes", y = NULL, title = paste("Annotation coverage:", method)) +
    theme_classic(base_size = 12)
  if (is.null(plot_output_dir)) plot_output_dir <- output_dir
  dir.create(plot_output_dir, recursive = TRUE, showWarnings = FALSE)
  ggsave(file.path(plot_output_dir, "annotation_coverage.pdf"), plot, width = width, height = height)
  ggsave(file.path(plot_output_dir, "annotation_coverage.png"), plot, width = width, height = height, dpi = dpi)
}

# 接口｜build_orgdb：把 eggNOG 注释整理成按基因 ID 查询的本地 OrgDb。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# method（默认 "diamond"）：字符路线名；当前非模式实现仅接受 diamond，不能填一个未实现的方法名称来切换
#   软件。
# tax_id（必填，无默认值）：字符形式的真实 NCBI taxonomy ID；写入自建 OrgDb 元数据，不是排除供体的税号
#   。案例为 3702，换物种应核实后改本章入口。
# genus（必填，无默认值）：字符属名；自建 OrgDb 元数据及包命名使用，案例 Arabidopsis。须与真实物种一致
#   ，不是矩阵 gene_id 前缀。
# species（必填，无默认值）：字符种加词；自建 OrgDb 使用，如 thaliana，不是任意项目显示名。换物种与
#   genus、tax_id 一起核实。
# 返回/写出与边界：写 GO/KO/通路表，构建并安装本项目局部 R_Library 的 OrgDb，同时输出覆盖图和查询核对
#   ；通路名称查询失败保留 ID 和警告。
build_orgdb <- function(method = "diamond", tax_id, genus, species) {
  stopifnot(identical(method, "diamond"))
  org_dir <- "9Enrichment_Analysis/OrgDb"
  route_dir <- file.path(org_dir, method)
  output_dir <- file.path(route_dir, "output")
  path <- file.path(output_dir, "annotation.emapper.annotations")
  lines <- readLines(path, warn = FALSE)
  header <- lines[startsWith(lines, "#query")]
  stopifnot(length(header) == 1)
  columns <- strsplit(sub("^#", "", header), "\t", fixed = TRUE)[[1]]
  emapper <- read.delim(path, header = FALSE, comment.char = "#", quote = "", fill = TRUE,
                        check.names = FALSE, col.names = columns)
  stopifnot(nrow(emapper) > 0, !anyDuplicated(emapper$query))
  representatives <- read.delim(file.path(org_dir, "representatives/validated_representatives.tsv"))
  stopifnot(all(emapper$query %in% representatives$gene_id))
  # gene_info 包含所有输入代表基因，而不是只保留得到 GO 的基因。
  gene_info <- tibble(GID = representatives$gene_id) |>
    left_join(emapper |> transmute(GID = query, SYMBOL = Preferred_name, GENENAME = Description), by = "GID") |>
    mutate(SYMBOL = if_else(is.na(SYMBOL) | SYMBOL %in% c("", "-"), GID, SYMBOL),
            GENENAME = if_else(is.na(GENENAME) | GENENAME %in% c("", "-"), GID, GENENAME))
  # 分别拆分 GO、KO 和通路列表并去重，GO 以 IEA 表示自动注释证据。KO 与 map 通路是不同层次，不互相替代。
  go_table <- emapper |> transmute(GID = query, GO = GOs) |> separate_rows(GO, sep = ",") |>
    filter(str_detect(GO, "^GO:[0-9]{7}$")) |> mutate(EVIDENCE = "IEA") |> distinct()
  ko_table <- emapper |> transmute(GID = query, KO = KEGG_ko) |> separate_rows(KO, sep = ",") |>
    filter(str_detect(KO, "^ko:K[0-9]{5}$")) |> distinct()
  pathway_table <- emapper |> transmute(GID = query, PATHWAY = KEGG_Pathway) |>
    separate_rows(PATHWAY, sep = ",") |> filter(str_detect(PATHWAY, "^map[0-9]{5}$")) |> distinct()
  stopifnot(nrow(go_table) > 0)
  package_root <- file.path(route_dir, "orgdb")
  library_dir <- file.path(package_root, "R_Library")
  dir.create(library_dir, recursive = TRUE, showWarnings = FALSE)
  # 以全部代表基因为 gene_info 范围构建本地注释包；tax_id/genus/species 是目标物种元数据。安装到项目的
  #   R_Library，不混改全局物种包。
  package_source <- AnnotationForge::makeOrgPackage(
    gene_info = as.data.frame(gene_info), go = as.data.frame(go_table),
    ko = as.data.frame(ko_table), pathway = as.data.frame(pathway_table),
    version = "0.1.0", maintainer = "RNA-seq project <rnaseq@example.org>", author = "RNA-seq project",
    outputDir = package_root, tax_id = tax_id,
    genus = genus, species = species, goTable = "go"
  )
  install.packages(package_source, repos = NULL, type = "source", lib = library_dir)
  package_name <- read.dcf(file.path(package_source, "DESCRIPTION"), fields = "Package")[[1]]
  writeLines(package_name, file.path(package_root, "custom_orgdb_package.txt"))
  for (name in c("gene_info", "go_table", "ko_table", "pathway_table")) {
    write.table(get(name), file.path(output_dir, paste0(name, ".tsv")), sep = "\t", quote = FALSE, row.names = FALSE)
  }
  plot_annotation_coverage(method)
  # 通路名称只用于展示；网络失败时明确保留 ID，不伪造通路名称。
  pathway_ids <- sort(unique(pathway_table$PATHWAY))
  pathway_names <- tryCatch({
    raw <- KEGGREST::keggList("pathway")
    data.frame(PATHWAY = sub("^path:", "", names(raw)), NAME = unname(raw)) |>
      filter(PATHWAY %in% pathway_ids)
  }, error = function(e) {
    writeLines(conditionMessage(e), file.path(output_dir, "PATHWAY_NAME_LOOKUP_WARNING.txt"))
    data.frame(PATHWAY = pathway_ids, NAME = pathway_ids)
  })
  pathway_names <- tibble(PATHWAY = pathway_ids) |> left_join(pathway_names, by = "PATHWAY") |>
    mutate(NAME = if_else(is.na(NAME), PATHWAY, NAME))
  write.table(pathway_names, file.path(output_dir, "pathway_names.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  database_files <- list.files(file.path(library_dir, package_name, "extdata"), pattern = "sqlite$", full.names = TRUE)
  stopifnot(length(database_files) == 1)
  db <- AnnotationDbi::loadDb(database_files)
  stopifnot("GID" %in% keytypes(db), all(c("SYMBOL", "GO") %in% columns(db)))
  write.table(AnnotationDbi::select(db, head(keys(db, keytype = "GID")), keytype = "GID", columns = c("SYMBOL", "GO")),
              file.path(output_dir, "orgdb_query_check.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
}
