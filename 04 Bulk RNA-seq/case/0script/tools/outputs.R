# 文件用途｜共用工具接口：计算内存对象的稳定内容摘要；分别记录输入文件内容和内存对象的指纹。
# 运行位置：能看见 0script 的项目根目录。R 函数库通过 source 加载定义及共用依赖；调用函数才执行本文件
#   对应的分析/写出。
# 调用方式：由编号分析脚本显式传入本工具的参数；每个接口的输入、返回和副作用见函数前注释。不通过修改工
#   具内部代码来切换样本或物种。
# 接口说明：每个函数前列出用途、形参和输出；嵌套函数读取的外层变量属于闭包，不能误当成漏传的独立参数。
# 共用语法：source 载入脚本；readRenviron 读取配置；Sys.getenv 取文本，as.numeric/as.integer 转数值；
#   local=TRUE 表示定义放在当前调用环境。
# 表格/图形约定：write.table 的 sep="\t" 用 TSV、quote=FALSE 不另加引号、row.names=FALSE 不写 R 行号；
#   check.names=FALSE 保留原 ID。ggsave 的图幅按英寸，dpi 主要控制 PNG。

# 接口｜result_digest：计算内存对象的稳定内容摘要。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# x（必填，无默认值）：任意可序列化 R 对象；以 SHA256 标识其内容，不把它当外部文件路径读取。
# 返回/写出与边界：返回 SHA256 字符串；digest 包缺失时报错，不写结果目录。
result_digest <- function(x) {
  if (!requireNamespace("digest", quietly = TRUE)) stop("缺少 digest；按环境文档恢复依赖")
  digest::digest(x, algo = "sha256")
}

# 接口｜input_fingerprints：分别记录输入文件内容和内存对象的指纹。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# inputs（必填，无默认值）：命名 list；值可以是现存文件路径或内存对象。文件按内容 SHA256，其他值按对象
#   序列化指纹记录；不是只比较文件名。
# 返回/写出与边界：返回与 inputs 对应的 list；已有单个文件路径会读取全文件做 SHA256，其他值按 R 对象计
#   算，不写输入。
input_fingerprints <- function(inputs) {
  # 非空输入必须有唯一角色名（如 counts、annotation），换位置时仍能确认比较的是同一种输入。
  if (!is.list(inputs) || (length(inputs) && (is.null(names(inputs)) ||
      anyNA(names(inputs)) || any(!nzchar(names(inputs))) || anyDuplicated(names(inputs)))))
    stop("inputs 必须是角色名唯一且非空的命名 list")
  lapply(inputs, function(value) {
    if (is.character(value) && length(value) == 1L && !is.na(value) && file.exists(value))
      return(list(source = value, sha256 = digest::digest(file = value, algo = "sha256")))
    list(object_sha256 = result_digest(value))
  })
}

# 接口｜fingerprint_content：从指纹中取真正影响结果的内容，路径只留在来源记录中。
# fingerprint：input_fingerprints 返回的命名 list，或从旧清单读出的同结构 list。
# 返回：保留角色名和内容摘要的 list；格式不明、重复角色、非法 SHA256 均报错，不猜测兼容。
fingerprint_content <- function(fingerprint) {
  if (!is.list(fingerprint) || (length(fingerprint) && (is.null(names(fingerprint)) ||
      anyNA(names(fingerprint)) || any(!nzchar(names(fingerprint))) || anyDuplicated(names(fingerprint)))))
    stop("输入指纹角色记录不完整")
  lapply(fingerprint, function(item) {
    if (!is.list(item) || anyDuplicated(names(item))) stop("输入指纹格式不完整")
    if (setequal(names(item), c("source", "sha256"))) {
      if (!is.character(item$source) || length(item$source) != 1L ||
          is.na(item$source) || !nzchar(item$source)) stop("文件来源记录不完整")
      value <- item$sha256
      result <- list(sha256 = value)
    } else if (identical(names(item), "object_sha256")) {
      value <- item$object_sha256
      result <- item
    } else stop("未知的输入指纹格式")
    if (!is.character(value) || length(value) != 1L || is.na(value) ||
        !grepl("^[a-f0-9]{64}$", value)) stop("输入内容 SHA256 不完整")
    result
  })
}

# 接口｜checked_output_paths：校验清单的输出路径及摘要格式，防止空清单或目录外文件被当作完整结果。
# path：结果目录；outputs：至少一个 list(path=相对路径, sha256=摘要) 的列表。
# 返回：已确认在结果目录内、存在且不是目录的路径；路径重复、上跳或软链接逃逸均报错。
# 此处只验证路径/摘要格式；claim_result_dir 再逐一读取内容，finish_result_dir 据此登记新清单。
checked_output_paths <- function(path, outputs) {
  if (!is.list(outputs) || !length(outputs)) stop("结果清单未登记任何输出，拒绝复用")
  base <- normalizePath(path, mustWork = TRUE)
  relative <- vapply(outputs, function(item) {
    if (!is.list(item) || anyDuplicated(names(item)) ||
        !setequal(names(item), c("path", "sha256"))) stop("输出清单格式不完整")
    p <- item$path
    h <- item$sha256
    if (!is.character(p) || length(p) != 1L || is.na(p) || !nzchar(p) ||
        grepl("^/|^[A-Za-z]:|\\\\", p) ||
        any(strsplit(p, "/", fixed = TRUE)[[1]] %in% c("", ".", "..")))
      stop("结果输出必须是目录内的规范相对路径")
    if (!is.character(h) || length(h) != 1L || is.na(h) || !grepl("^[a-f0-9]{64}$", h))
      stop("输出 SHA256 不完整")
    p
  }, "")
  if (anyDuplicated(relative)) stop("结果清单有重复输出路径")
  targets <- file.path(path, relative)
  if (any(!file.exists(targets)) || any(dir.exists(targets))) stop("结果文件缺失或不是普通文件")
  resolved <- normalizePath(targets, mustWork = TRUE)
  if (any(!startsWith(resolved, paste0(base, "/")))) stop("结果输出指向目录之外，拒绝复用")
  targets
}

# 接口｜parameter_tag：把选定关键参数拼成可辨识的路径标签。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# ...（必填，无默认值）：命名参数值，如 padj=0.05、lfc=1；同一值向量用 - 拼接，各参数用 _ 拼接，返回路
#   径标签字符串，不创建目录。
# 返回/写出与边界：返回字符，不创建路径，也不保证所有影响结果的参数都已进入文件名；完整登记另由清单负
#   责。
parameter_tag <- function(...) {
  values <- list(...)
  paste(vapply(names(values), function(name) paste0(name, paste(values[[name]], collapse = "-")), ""), collapse = "_")
}

# 接口｜effective_parameters：从函数调用环境收集具名实参与函数体指纹。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# fun（必填，无默认值）：R 函数对象；从其 formals 获取具名参数，并记录函数体摘要，不把函数名称字符串当
#   对象传入。
# frame（必填，无默认值）：R environment；当前函数调用环境，通常 environment()。从这里取已赋值实参，不
#   搜索父环境补齐缺失值。
# omit（默认 character()）：字符向量；从参数记录中排除的形参名。大数据对象宜另作为 inputs 指纹记录，不
#   能借此隐去会影响分析的重要设置。
# 返回/写出与边界：返回参数 list；只读取当前 frame，排除 .../omit。标准 Rscript 不保留源码时纯注释不改
#   函数体指纹；keep.source=TRUE 的源码属性可能改变摘要，不能据此宣称算法变了。
effective_parameters <- function(fun, frame, omit = character()) {
  # 只记录函数的具名实参，不把临时统计对象误当成参数；大输入单独做指纹。
  keys <- setdiff(names(formals(fun)), c("...", omit))
  c(mget(keys, envir = frame, inherits = FALSE), list(function_code_sha256 = result_digest(body(fun))))
}

# 接口｜annotation_fingerprint：取得 OrgDb SQLite 来源路径供后续内容摘要。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# database（必填，无默认值）：OrgDb 对象或 NULL；用于获取对应 SQLite 数据库路径以记录来源，NULL 表示该
#   项无数据库。
# 返回/写出与边界：返回数据库文件路径，NULL 输入返回 NULL；此函数本身尚未计算数据库文件 SHA256。
annotation_fingerprint <- function(database) {
  if (is.null(database)) return(NULL)
  AnnotationDbi::dbfile(database)
}

# 接口｜assert_fresh_files：防止覆盖一个或多个明确目标文件。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# paths（必填，无默认值）：字符路径向量；预先检查的完整输出文件名，任一已存在即拒绝继续，避免只保住
#   PDF 却覆盖 PNG。
# 返回/写出与边界：任一目标存在即 stop，成功不写文件也不建目录。
assert_fresh_files <- function(paths) {
  old <- paths[file.exists(paths)]
  if (length(old)) stop("拒绝覆盖已有文件：", paste(old, collapse = ", "),
    "；请选择新的输出目录，完整图表一起另存。", call. = FALSE)
}

# 接口｜assert_fresh_plot：同时保护一张图的 PDF 与 PNG。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# prefix（必填，无默认值）：字符输出路径前缀，不含 .png/.pdf 扩展名；辅助函数为同一张图保存两种格式。
# 返回/写出与边界：检查两种扩展名，任一种已存在即拒绝；不绘图、不删图。
assert_fresh_plot <- function(prefix) {
  assert_fresh_files(paste0(prefix, c(".pdf", ".png")))
}

# 接口｜claim_result_dir：登记本次结果身份或确认完整旧结果可复用。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# path（必填，无默认值）：期望结果目录；可追加 __variant_label。已有非空目录必须有匹配且完整的清单和未
#   被修改的结果，否则拒绝覆盖。
# parameters（必填，无默认值）：命名 list；调用者明确登记的生效参数。只比较这里确实登记的值，不自动捕
#   获任意全局变量或全部软件版本。
# inputs（默认 list()）：命名 list；值可以是现存文件路径或内存对象。文件按内容 SHA256，其他值按对象序
#   列化指纹记录；不是只比较文件名。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：返回 path/manifest/identity/reuse；新建时写 incomplete 清单，复用时校验每个登记输出
#   的内容，冲突/缺失报错，不静默覆盖。
claim_result_dir <- function(path, parameters, inputs = list(), variant_label = "") {
  if (!requireNamespace("jsonlite", quietly = TRUE)) stop("缺少 jsonlite；按环境文档恢复依赖")
  if (!is.list(parameters) || (length(parameters) && (is.null(names(parameters)) ||
      anyNA(names(parameters)) || any(!nzchar(names(parameters))) || anyDuplicated(names(parameters)))))
    stop("parameters 必须是名称唯一且非空的命名 list")
  if (nzchar(variant_label)) {
    if (!grepl("^[A-Za-z0-9][A-Za-z0-9_.-]*$", variant_label)) stop("variant_label 不能含路径或空格")
    path <- paste0(path, "__", variant_label)
  }
  # 目录名只是简短提示，真实身份由已登记参数和输入内容指纹组成。外部种子等若未由调用者登记，不会自动进入
  #   这个检查。
  fingerprint <- input_fingerprints(inputs)
  content <- fingerprint_content(fingerprint)
  identity <- result_digest(list(identity_version = 2L, parameters = parameters, inputs = content))
  manifest <- file.path(path, "result_manifest.json")
  if (dir.exists(path) && length(list.files(path, all.files = TRUE, no.. = TRUE))) {
    if (!file.exists(manifest)) stop("结果目录已存在但无完整来源记录，拒绝覆盖：", path,
      "；请用 variant_label 或新的输出目录另存", call. = FALSE)
    previous <- jsonlite::fromJSON(manifest, simplifyVector = FALSE)
    version <- previous$identity_version
    if (is.null(version)) version <- 1L
    if (!is.list(previous) || anyDuplicated(names(previous)) ||
        !is.numeric(version) || length(version) != 1L || is.na(version) || !version %in% c(1, 2))
      stop("未知或损坏的结果清单版本，拒绝覆盖：", path, call. = FALSE)
    old_content <- fingerprint_content(previous$inputs)
    same_inputs <- identical(old_content, content)
    # JSON 只用来核对可读参数记录。身份摘要仍用本次原生 R 参数，不能把 JSON 的 list/数值类型当原对象。
    visible_parameters <- jsonlite::fromJSON(jsonlite::toJSON(parameters, auto_unbox = TRUE,
      null = "null"), simplifyVector = FALSE)
    same_parameters <- identical(previous$parameters, visible_parameters)
    expected <- identity
    legacy_expected <- character()
    if (version == 1L && same_inputs) {
      # 旧算法把路径计入摘要：仅在内存中换回清单记录的旧路径，证明参数/内容确实相同；绝不改写旧清单。
      legacy_inputs <- fingerprint
      for (name in names(legacy_inputs)) {
        if (!is.null(legacy_inputs[[name]]$source)) legacy_inputs[[name]]$source <- previous$inputs[[name]]$source
      }
      expected <- result_digest(list(parameters = parameters, inputs = legacy_inputs))
      # JSON 把中文统一读作 UTF-8；旧 R 文件路径也可能标作本地编码。仅对来源路径试这两种等价表示，
      # 必须重新得到原身份摘要才接受；不猜测原参数类型，也不放宽内容校验。
      native_path <- function(x) { x <- enc2native(x); Encoding(x) <- "unknown"; x }
      legacy_expected <- vapply(list(native_path, enc2utf8), function(encode) {
        encoded <- legacy_inputs
        for (name in names(encoded)) {
          if (!is.null(encoded[[name]]$source)) encoded[[name]]$source <- encode(encoded[[name]]$source)
        }
        result_digest(list(parameters = parameters, inputs = encoded))
      }, "")
    }
    same_identity <- is.character(previous$identity) && length(previous$identity) == 1L &&
      !is.na(previous$identity) && previous$identity %in% c(expected, legacy_expected)
    if (!same_inputs || !same_parameters || !same_identity ||
        !identical(previous$status, "complete"))
      stop("结果参数/输入不同，或上次输出未完成，拒绝覆盖：", path, call. = FALSE)
    # 匹配身份还不够：逐个核对登记输出的内容。缺图、手改 TSV 或不完整旧任务都会拒绝复用，保留旧文件供核实。
    targets <- checked_output_paths(path, previous$outputs)
    for (i in seq_along(targets)) {
      file <- previous$outputs[[i]]
      target <- targets[[i]]
      if (!file.exists(target) || !identical(digest::digest(file = target, algo = "sha256"), file$sha256))
        stop("结果文件缺失或已改变，不能作为完整结果复用：", target, call. = FALSE)
    }
    message("复用相同输入和生效参数的完整结果：", path)
    return(list(path = path, manifest = manifest, identity = identity, reuse = TRUE))
  }
  dir.create(path, recursive = TRUE, showWarnings = FALSE)
  record <- list(identity_version = 2L, identity = identity, status = "incomplete", parameters = parameters,
                 inputs = fingerprint, created = format(Sys.time(), tz = "UTC", usetz = TRUE))
  jsonlite::write_json(record, manifest, auto_unbox = TRUE, pretty = TRUE, null = "null")
  list(path = path, manifest = manifest, identity = identity, reuse = FALSE)
}

# 接口｜finish_result_dir：核对本次身份并把结果清单标记为完成。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# claim（必填，无默认值）：claim_result_dir()/begin_result_stage() 返回的 list；含 path、manifest、
#   identity、reuse，须使用本次返回的对象结束本次结果记录。
# 返回/写出与边界：不可见返回路径；登记目录内结果文件 SHA256，经临时清单重命名提交。空结果或身份改变报
#   错，不伪造成功。
finish_result_dir <- function(claim) {
  if (claim$reuse) return(invisible(claim$path))
  record <- jsonlite::fromJSON(claim$manifest, simplifyVector = FALSE)
  if (!identical(record$identity, claim$identity)) stop("结果目录被另一操作改变，不能标记完成")
  files <- list.files(claim$path, recursive = TRUE, full.names = FALSE, all.files = TRUE, no.. = TRUE)
  files <- files[files != "result_manifest.json" & !file.info(file.path(claim$path, files))$isdir]
  if (!length(files)) stop("没有任何结果文件，不能标记完成：", claim$path)
  # 完成前再遍历结果文件计算 SHA256。这里只提交本次产物清单，不回写历史任务的源码指纹或统计表。
  record$outputs <- lapply(files, function(x) list(path = x,
    sha256 = digest::digest(file = file.path(claim$path, x), algo = "sha256")))
  checked_output_paths(claim$path, record$outputs)
  record$status <- "complete"
  record$finished <- format(Sys.time(), tz = "UTC", usetz = TRUE)
  scratch <- tempfile("manifest-", tmpdir = claim$path)
  on.exit(unlink(scratch), add = TRUE)
  jsonlite::write_json(record, scratch, auto_unbox = TRUE, pretty = TRUE, null = "null")
  if (!file.rename(scratch, claim$manifest)) stop("无法更新结果清单")
  invisible(claim$path)
}

# 接口｜project_result：读取本项目显式选择的结果来源。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# key（必填，无默认值）：project.env 的结果位置字段名字符串，如 DE_RESULT_FILE；读取对应环境变量，不是
#   直接的路径。
# default（必填，无默认值）：字符备用路径；仅配置字段不存在时使用，显式空值报错，不自动选择最新结果。
# must_exist（默认 TRUE）：TRUE/FALSE；TRUE 要求配置的文件或目录已存在，FALSE 允许返回计划路径但不会替
#   你创建它。
# 返回/写出与边界：返回路径字符串；配置空值或必需文件不存在报错，不搜索最新结果，不跨项目回退。
project_result <- function(key, default, must_exist = TRUE) {
  # 仅接受明确配置，不选择最新目录，也不回退到其他项目的示例结果。
  if (file.exists("0script/project.env")) readRenviron("0script/project.env")
  path <- Sys.getenv(key, default)
  if (!nzchar(path)) stop(key, " 未配置结果来源")
  if (must_exist && !file.exists(path) && !dir.exists(path)) stop(key, " 指定的来源不存在：", path)
  path
}

# 接口｜begin_result_stage：为顶层执行单元提供结果复用保护。
# 参数（默认值以本函数签名为准；明确传参会覆盖默认值）：
# path（必填，无默认值）：当前执行单元的结果目录；通过 claim_result_dir 检查，已有完整匹配结果用专门条
#   件通知执行器复用并停止本单元。
# parameters（必填，无默认值）：命名 list；调用者明确登记的生效参数。只比较这里确实登记的值，不自动捕
#   获任意全局变量或全部软件版本。
# inputs（默认 list()）：命名 list；值可以是现存文件路径或内存对象。文件按内容 SHA256，其他值按对象序
#   列化指纹记录；不是只比较文件名。
# variant_label（默认 ""）：字符标签；空字符串为默认路径。给次要排版或另一方案另存时用 large_font 等简
#   短标签，仅允许字母数字及 . _ -，首位为字母数字；不能放路径或空格。
# 返回/写出与边界：新任务返回 claim；可复用时抛 rnaseq_result_reused 条件，CLI 将其视为正常跳过而非分
#   析失败，交互用户可读取已有结果。
begin_result_stage <- function(path, parameters, inputs = list(), variant_label = "") {
  # 顶层代码单元的入口保护。已有完整结果时终止本单元，不退出交互式 R。
  # 章节执行器把 rnaseq_result_reused 记录为正常复用；手动运行可直接读取已存对象。
  claim <- claim_result_dir(path, parameters, inputs, variant_label)
  if (claim$reuse) stop(structure(list(message = paste("已复用完整结果，跳过本执行单元：", claim$path), call = NULL),
    class = c("rnaseq_result_reused", "error", "condition")))
  claim
}
