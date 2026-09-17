# 完整分析函数：读取一批观察记录，并明确区分三种资料设计。
# 使用：source("scripts/analyse.R"); analyse_records("data/observations.csv", "results/first-week")
# 只写入调用者指定的结果目录，不修改 data 中的输入。
analyse_records <- function(input, output) {
  for (pkg in c("dplyr", "ggplot2")) {
    if (!requireNamespace(pkg, quietly = TRUE)) stop("Missing package: ", pkg, "; run setup.R once.")
  }
  records <- read.csv(input, stringsAsFactors = FALSE, fileEncoding = "UTF-8")
  required <- c("record_id", "site_id", "date", "period", "temperature_c", "visitors", "note")
  if (!all(required %in% names(records))) stop("Missing required columns")
  if (!is.numeric(records$temperature_c)) stop("Temperature must be numeric")
  if (any(!is.finite(records$temperature_c) & !is.na(records$temperature_c))) stop("Non-finite temperature")
  clean <- dplyr::distinct(records)
  if (anyNA(clean$record_id) || any(clean$record_id == "") || anyDuplicated(clean$record_id)) stop("Conflicting or missing record IDs; inspect source records")
  clean$date <- as.Date(gsub("/", "-", clean$date), format = "%Y-%m-%d")
  if (anyNA(clean$date)) stop("Invalid date; inspect source records")
  clean$note <- tolower(trimws(clean$note))
  sites <- read.csv("data/sites.csv", stringsAsFactors = FALSE)
  if (anyDuplicated(sites$site_id)) stop("Site key is not unique")
  if (any(!clean$site_id %in% sites$site_id)) stop("Unknown site ID")
  clean <- dplyr::left_join(clean, sites, by = "site_id", relationship = "many-to-one")
  mean_or_na <- function(x) if (all(is.na(x))) NA_real_ else mean(x, na.rm = TRUE)
  summary <- clean |>
    dplyr::group_by(site_id, site_name) |>
    dplyr::summarise(n_records = dplyr::n(), n_valid = sum(!is.na(temperature_c)),
                     mean_c = round(mean_or_na(temperature_c), 3), .groups = "drop")
  audit <- c(raw = nrow(records), duplicate_rows = nrow(records) - nrow(clean),
             clean = nrow(clean), missing_temperature = sum(is.na(clean$temperature_c)))
  trial <- read.csv("data/shade_trial.csv")
  parks <- read.csv("data/independent_sites.csv")
  if (anyDuplicated(trial$unit_id) || anyDuplicated(parks$site_id)) stop("Inference units must be unique")
  if (anyNA(trial$drop_c) || anyNA(parks[, c("canopy_pct", "temperature_c")])) stop("Inference inputs contain missing measurements; review the analysis design")
  a <- trial$drop_c[trial$material == "A"]
  b <- trial$drop_c[trial$material == "B"]
  comparison <- t.test(b, a, var.equal = FALSE, alternative = "two.sided", conf.level = 0.95)
  model <- lm(temperature_c ~ canopy_pct, data = parks)
  dir.create(output, recursive = TRUE, showWarnings = FALSE)
  write.csv(clean, file.path(output, "clean.csv"), row.names = FALSE, na = "", fileEncoding = "UTF-8")
  write.csv(summary, file.path(output, "summary.csv"), row.names = FALSE, na = "", fileEncoding = "UTF-8")
  p <- ggplot2::ggplot(clean, ggplot2::aes(site_name, temperature_c)) +
    ggplot2::geom_boxplot(outlier.shape = NA, width = 0.5, na.rm = TRUE) +
    ggplot2::geom_point(position = ggplot2::position_jitter(width = 0.1, height = 0, seed = 34), colour = "#256187", alpha = 0.7, na.rm = TRUE) +
    ggplot2::labs(x = "Site", y = "Temperature (C)", title = "Observed records by site", subtitle = "Repeated observations: descriptive comparison only") + ggplot2::theme_minimal(base_size = 13)
  ggplot2::ggsave(file.path(output, "observations.png"), plot = p, width = 7.5, height = 4.8, dpi = 140)
  p <- ggplot2::ggplot(parks, ggplot2::aes(canopy_pct, temperature_c)) +
    ggplot2::geom_point(colour = "#256187") + ggplot2::geom_smooth(method = "lm", formula = y ~ x, colour = "#36866f") +
    ggplot2::labs(x = "Canopy cover (%)", y = "Temperature (C)", title = "Independent sites: association, not a causal estimate") + ggplot2::theme_minimal(base_size = 13)
  ggplot2::ggsave(file.path(output, "regression.png"), plot = p, width = 7.5, height = 4.8, dpi = 140)
  interval <- comparison$conf.int
  slope <- coef(model)[["canopy_pct"]]
  slope_ci <- confint(model)["canopy_pct", ]
  p_text <- format.pval(comparison$p.value, digits = 3, eps = 0.001)
  report <- c("# 数据调查小镇 · 分析简报", "", "全部输入均为原创模拟教学数据，不代表真实研究结论。", "",
    "## 观察记录", sprintf("输入 %s。原始 %d 行；删除 %d 条完全相同的重复导入后剩 %d 行，其中温度缺失 %d 条。", basename(input), audit[["raw"]], audit[["duplicate_rows"]], audit[["clean"]], audit[["missing_temperature"]]),
    "均值只使用有温度的记录；汇总表同时保留记录数与有效数。同一地点重复测量，因此这里只做描述，不把行数当作独立地点数。", "",
    "## 随机分组的独立装置实验", sprintf("A、B 各 %d、%d 个独立装置；预先比较降温量 B−A。Welch 双侧比较估计差值 %.3f °C，95%% 置信区间 [%.3f, %.3f] °C，p %s %s。", length(a), length(b), mean(b) - mean(a), interval[1], interval[2], if (grepl("<", p_text, fixed = TRUE)) "" else "=", p_text),
    "每个装置随机分组且只贡献一次结果。结论以独立性、连续测量及均值推断的近似条件为前提；效应和区间比一个显著性标签包含更多信息。", "",
    "## 地点级横断面资料", sprintf("另有 %d 个地点，各记录一次。冠层覆盖每增加 1 个百分点，模型预测的平均温度改变 %.4f °C；斜率 95%% 区间 [%.4f, %.4f]。", nrow(parks), slope, slope_ci[1], slope_ci[2]),
    "这里报告关联，不排除其他变量的影响。解释前检查残差的形状与离散程度；避免超出已有冠层覆盖范围外推。", "",
    "## 如何复现", "在 r-lab 项目中运行 scripts/analyse.R 定义函数，再用本批输入路径调用 analyse_records()。包与 R 版本见 session-info.txt。",
    "更换观察表只更新观察部分；固定的实验与横断面数据不会因此变成新的研究。")
  writeLines(enc2utf8(report), file.path(output, "report.md"), useBytes = TRUE)
  writeLines(capture.output(sessionInfo()), file.path(output, "session-info.txt"))
  invisible(list(audit = audit, summary = summary, test = comparison, model = model))
}
