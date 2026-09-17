# 数据调查小镇 · 第 36 节
# 在 r-lab 项目根目录运行；输出只写入 results。
source("scripts/analyse.R")
first <- analyse_records("data/observations.csv", "results/first-week")
next_week <- analyse_records("data/new_observations.csv", "results/next-week")
print(rbind(first_week = first$audit, new_records = next_week$audit))
print(as.data.frame(next_week$summary))
# 新观察表只更新观察部分；实验和横断面资料并没有重新采集。
