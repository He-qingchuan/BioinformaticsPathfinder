# 数据调查小镇 · 第 11 节
# 在 r-lab 项目根目录运行；输出只写入 results。
records <- read.csv("data/observations.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")
print(dim(records))
print(head(records[, c("record_id", "site_id", "temperature_c")], 3))
dir.create("results", showWarnings = FALSE)
write.csv(records, "results/observations-copy.csv", row.names = FALSE, na = "", fileEncoding = "UTF-8")
roundtrip <- read.csv("results/observations-copy.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")
print(identical(names(records), names(roundtrip)))
saveRDS(records, "results/observations.rds")
print(identical(records, readRDS("results/observations.rds")))
