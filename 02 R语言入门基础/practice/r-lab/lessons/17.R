# 数据调查小镇 · 第 17 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(tidyr))
wide <- read.csv("data/temperatures_wide.csv", stringsAsFactors = FALSE)
long <- pivot_longer(wide, cols = c(morning, afternoon), names_to = "period", values_to = "temperature_c")
print(as.data.frame(long))
back <- pivot_wider(long, names_from = period, values_from = temperature_c)
print(as.data.frame(back))
