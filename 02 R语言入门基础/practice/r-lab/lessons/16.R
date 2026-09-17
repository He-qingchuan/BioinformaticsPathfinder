# 数据调查小镇 · 第 16 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(dplyr))
records <- read.csv("data/observations.csv", stringsAsFactors = FALSE) |> distinct()
sites <- read.csv("data/sites.csv", stringsAsFactors = FALSE)
stopifnot(!anyDuplicated(sites$site_id))
joined <- left_join(records, sites, by = "site_id", relationship = "many-to-one")
print(c(before = nrow(records), after = nrow(joined)))
print(head(select(joined, record_id, site_id, site_name), 3))
print(nrow(anti_join(records, sites, by = "site_id")))
# 少一个地点时，左连接保留记录，但补入的资料缺失。
incomplete <- left_join(records, sites[1:2, ], by = "site_id", relationship = "many-to-one")
print(sum(is.na(incomplete$site_name)))
