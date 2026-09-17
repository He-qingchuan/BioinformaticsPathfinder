# 数据调查小镇 · 第 34 节
# 在 r-lab 项目根目录运行；输出只写入 results。
source("scripts/analyse.R")
result <- analyse_records("data/observations.csv", "results/first-week")
print(result$audit)
print(as.data.frame(result$summary))
