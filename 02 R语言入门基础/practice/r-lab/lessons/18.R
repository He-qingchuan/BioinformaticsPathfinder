# 数据调查小镇 · 第 18 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(stringr))
records <- read.csv("data/observations.csv", stringsAsFactors = FALSE)
print(unique(records$note))
records$note <- str_to_lower(str_trim(records$note))
records$date <- as.Date(str_replace_all(records$date, "/", "-"), format = "%Y-%m-%d")
print(unique(records$note))
print(range(records$date))
print(sum(is.na(records$date)))
print(as.integer(as.Date("2026-06-08") - as.Date("2026-06-01")))
