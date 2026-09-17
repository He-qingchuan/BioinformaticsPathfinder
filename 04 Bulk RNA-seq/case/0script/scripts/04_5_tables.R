# 文件用途｜第 04 章：按所选章节检查样本、比较、矩阵、时间及注释入口；将单项检查转换成带状态的报告记录。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 改参方式：在同编号 MD 的参数入口赋值，再执行下面的具名调用；函数默认值只在该形参未传入时使用。编辑文
#   件不会刷新内存中的旧函数/旧变量，需重新 source/赋值。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。
# 本文件也有 Rscript 入口：位置参数依次为 fastq/matrix 与逗号分隔章节，标准输出 JSON；source 时不进入
#   该命令行分支。

# 接口｜check_preparation_tables：按所选章节检查样本、比较、矩阵、时间及注释入口。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# entry（必填，无默认值）：字符 fastq 或 matrix；决定输入检查需要 FASTQ 文件列还是已有表达矩阵，不自动
#   转换数据尺度。
# chapters（必填，无默认值）：整数向量；本次选择检查的第 05–20 章，仅检查这些章节所需材料与依赖，不运
#   行分析。
# 返回/写出与边界：返回 checks 与 samples 的 list，供 Python 转成报告；内部单项失败记为 FAIL，不修复输
#   入、不运行统计。
check_preparation_tables <- function(entry, chapters) {
  source("0script/tools/metadata.R", local = TRUE)
  readRenviron("0script/project.env")
  checks <- list(); matrices <- list(); samples <- NULL
  # 接口｜check：将单项检查转换成带状态的报告记录。
  # 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
  # name（必填，无默认值）：本检查项的显示名称，写入报告的 check 字段。
  # action（必填，无默认值）：无参数函数；执行一个只读检查并返回说明文本，抛出的错误被转换成 FAIL 项而非
  #   终止整份报告。
  # 返回/写出与边界：更新上层 checks list（闭包副作用）；action 报错被捕获为 FAIL，成功为 PASS。返回值不
  #   作为分析结果使用。
  check <- function(name, action) {
    tryCatch({
      detail <- action()
      checks[[length(checks)+1L]] <<- list(check=name,status="PASS",detail=as.character(detail))
    }, error=function(e) {
      checks[[length(checks)+1L]] <<- list(check=name,status="FAIL",detail=conditionMessage(e))
    })
  }
  check("样本表", function() {
    samples <<- read_samples(entry=entry, check_files=FALSE)
    paste(nrow(samples), "个样本；", length(unique(samples$timepoint)), "个组；按列名读取")
  })
  if (!is.null(samples)) {
    if (any(chapters %in% c(10:15,19:20))) check("比较表", function() {
      contrasts <- read_contrasts(samples=samples)
      contrasts <- contrasts[toupper(as.character(contrasts$enabled))=="TRUE",,drop=FALSE]
      if (!nrow(contrasts)) stop("没有启用的比较")
      groups <- unique(c(contrasts$test_group,contrasts$reference_group))
      if (10 %in% chapters && any(table(samples$timepoint)[groups] < 2L))
        stop("当前 DESeq2 两组模型至少需要每组两个独立重复；不能以均值替代创建重复")
      paste(nrow(contrasts), "个启用比较；正 log2FC = test_group 高于 reference_group；独立重复需结合实验记录核实")
    })
    # 没有选择第 08 章生成矩阵时，无论最初是 FASTQ 还是矩阵入口，
    # 下游都必须已有实际要读的矩阵；不能因 DATA_ENTRY=fastq 而漏检。
    if (!8 %in% chapters) {
      need <- unique(c(if (10 %in% chapters) "COUNT_MATRIX", if (any(c(9,13) %in% chapters)) "TMM_MATRIX",
                       if (any(c(16,17) %in% chapters)) "TPM_MATRIX"))
      for (key in need) local({
        field <- key
        check(field, function() {
          path <- Sys.getenv(field)
          if (!nzchar(path)) stop("请在 project.env 填写 ",field)
          values <- read_expression(path,samples)
          matrices[[field]] <<- path
          paste(nrow(values),"个基因 ×",ncol(values),"个样本；",path,
                "；数值结构通过，真实 counts/TPM/TMM 尺度仍须核对来源")
        })
      })
    }
    if (any(c(16,17) %in% chapters)) check("真实时间",function() {
      timed <- read_samples(entry=entry,use_time="time",cycle=17 %in% chapters)
      groups <- ordered_groups(timed,require_time=TRUE)
      if (length(groups)<3) stop("时间趋势至少准备三个真实时间点；两组比较请使用主线")
      if (17 %in% chapters) {
        selected <- timed[timed$cycle_use,,drop=FALSE]
        grid <- sort(unique(selected$time_hour)); intervals <- diff(grid)
        if (length(grid)<4 || length(unique(table(selected$time_hour)))!=1L || min(table(selected$time_hour))<2L ||
            max(abs(intervals-intervals[1]))>1e-8)
          stop("当前 JTK 入口要求至少四个等间隔时间点、各时点相同数量且至少两个重复")
      }
      paste("按真实小时排序：",paste(groups,collapse=", "),"；周期范围仍需在第 17 章按实验设计核实")
    })
  }
  # 只运行末端章节时要求现成结果；若本次包含生成步骤，不要求未来文件提前存在。
  if (any(c(11:15,19:20) %in% chapters) && !10 %in% chapters) check("既有差异结果",function() {
    path <- Sys.getenv("DE_RESULT_FILE")
    x <- read_result_table(path)
    require_columns(x,c("gene_id","contrast_id"),"差异结果")
    needed <- c("log2FoldChange","padj","pvalue")
    if (any(c(11,14,19) %in% chapters)) needed <- c(needed,"direction")
    if (any(c(15,20) %in% chapters)) needed <- c(needed,"stat")
    if (!all(needed %in% names(x))) stop("差异结果缺少统计列：",paste(setdiff(needed,names(x)),collapse=","))
    if (anyDuplicated(x[c("contrast_id","gene_id")])) stop("同一比较中基因 ID 重复")
    if ("direction" %in% needed && anyNA(match(x$direction,c("up","down","ns"))))
      stop("direction 只能为 up/down/ns；来源应是第 10 章实际阈值汇总")
    if (!is.null(samples)) {
      contrasts <- read_contrasts(samples=samples)
      enabled <- contrasts$contrast_id[toupper(as.character(contrasts$enabled))=="TRUE"]
      if (!all(enabled %in% x$contrast_id)) stop("差异结果未包含所有启用比较")
    }
    paste(nrow(x),"行；",path)
  })
  if (any(c(14,15) %in% chapters)) check("GO 注释配置",function() {
    package <- Sys.getenv("ORGDB_PACKAGE"); key <- Sys.getenv("ORGDB_KEYTYPE")
    if (!nzchar(package) || !requireNamespace(package,quietly=TRUE)) stop("缺少可用的 ORGDB_PACKAGE：",package)
    db <- get(package,envir=asNamespace(package))
    if (!key %in% AnnotationDbi::keytypes(db)) stop("ORGDB_KEYTYPE 不受该 OrgDb 支持：",key)
    if (length(matrices)) {
      genes <- read_input_table(matrices[[1]],allow_first_blank=TRUE)[[1]]
      mapped <- sum(genes %in% AnnotationDbi::keys(db,keytype=key))
      if (!mapped) stop("矩阵基因与所选 OrgDb/keyType 无匹配；需要核实/处理 ID，不能只改类型字符串")
      return(paste(package,key,"；",mapped,"/",length(genes),"个输入基因可映射，未匹配记录须结合来源检查"))
    }
    paste(package,key,"；上游尚未生成基因矩阵时，不能提前证明所有基因均可映射")
  })
  if (any(c(19,20) %in% chapters) && !18 %in% chapters) check("既有非模式注释",function() {
    marker <- "9Enrichment_Analysis/OrgDb/diamond/orgdb/custom_orgdb_package.txt"
    if (!file.exists(marker)) stop("缺少已完成的第 18 章 OrgDb：",marker)
    package <- trimws(readLines(marker,warn=FALSE)[1])
    if (is.na(package) || !nzchar(package) || !requireNamespace(package,quietly=TRUE))
      stop("标记存在，但记录的 OrgDb 包不可用：",package)
    paste(marker,package)
  })
  if (19 %in% chapters && !16 %in% chapters) check("既有时间聚类",function() {
    root <- Sys.getenv("TIME_RESULT_ROOT")
    objects <- list.files(root,pattern="^cluster_object\\.rds$",recursive=TRUE,full.names=TRUE)
    if (!length(objects)) stop("第 19 章模块分析需要已完成的第 16 章聚类：",root)
    paste(length(objects),"个聚类对象；实际 top_var_props / cluster_numbers / variant 仍按第 19 章逐项核对")
  })
  if (!any(c(16,17) %in% chapters)) checks[[length(checks)+1L]] <- list(check="时间/周期",status="NOT_SELECTED",detail="未选择，不要求时间列")
  if (!any(18:20 %in% chapters)) checks[[length(checks)+1L]] <- list(check="非模式支线",status="NOT_SELECTED",detail="未选择，不要求蛋白与 eggNOG 数据库")
  list(checks=checks,samples=if (is.null(samples)) list() else lapply(seq_len(nrow(samples)),function(i)as.list(samples[i,,drop=FALSE])))
}

if (sys.nframe()==0L) {
  args <- commandArgs(TRUE)
  result <- check_preparation_tables(args[1],as.integer(strsplit(args[2],",",fixed=TRUE)[[1]]))
  cat(jsonlite::toJSON(result,auto_unbox=TRUE,na="null",null="null"))
}
