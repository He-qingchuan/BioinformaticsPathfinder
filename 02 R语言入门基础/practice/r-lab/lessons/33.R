# 数据调查小镇 · 第 33 节
# 在 r-lab 项目根目录运行；输出只写入 results。
records <- read.csv("data/observations.csv", stringsAsFactors = FALSE)
required <- c("record_id", "site_id", "date", "temperature_c")
stopifnot(all(required %in% names(records)))
stopifnot(is.numeric(records$temperature_c))
print(c(rows = nrow(records), missing_temperature = sum(is.na(records$temperature_c))))
dir.create("results", showWarnings = FALSE)
writeLines(capture.output(sessionInfo()), "results/session-info.txt")
print(file.exists("results/session-info.txt"))
