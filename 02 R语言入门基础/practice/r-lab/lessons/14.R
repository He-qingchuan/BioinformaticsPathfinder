# 数据调查小镇 · 第 14 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(dplyr))
records <- read.csv("data/observations.csv", stringsAsFactors = FALSE)
selected <- records |>
  filter(period == "afternoon", !is.na(temperature_c)) |>
  select(record_id, site_id, temperature_c) |>
  mutate(temperature_f = temperature_c * 9 / 5 + 32) |>
  arrange(desc(temperature_c))
print(head(selected, 5))
print(nrow(selected))
