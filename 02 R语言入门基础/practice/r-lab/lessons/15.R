# 数据调查小镇 · 第 15 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(dplyr))
records <- read.csv("data/observations.csv", stringsAsFactors = FALSE)
# 本数据的重复是完全相同的重复导入；distinct() 删除整行重复。
clean <- distinct(records)
summary <- clean |>
  group_by(site_id) |>
  summarise(n_records = n(), n_valid = sum(!is.na(temperature_c)),
            mean_c = round(mean(temperature_c, na.rm = TRUE), 2), .groups = "drop")
print(c(raw_rows = nrow(records), unique_rows = nrow(clean)))
print(as.data.frame(summary))
