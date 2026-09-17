# 数据调查小镇 · 第 13 节
# 在 r-lab 项目根目录运行；输出只写入 results。
# 安装只做一次；加载发生在每次新会话。setup.R 是单独的安装入口。
suppressPackageStartupMessages(library(dplyr))
x <- c(26, 28, 30)
print(round(mean(x), digits = 1))
print(x |> mean() |> round(digits = 1))
print(dplyr::filter(data.frame(temperature = x), temperature >= 28))
