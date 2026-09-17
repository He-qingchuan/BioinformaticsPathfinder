# 数据调查小镇 · 第 20 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(ggplot2))
trial <- read.csv("data/shade_trial.csv")
dir.create("results", showWarnings = FALSE)
p <- ggplot(trial, aes(x = drop_c)) + geom_histogram(binwidth = 0.5, boundary = 0, fill = "#669c9a", colour = "white") + labs(x = "Cooling (C)", y = "Number of units", title = "A histogram groups continuous measurements") + theme_minimal(base_size = 13)
ggsave("results/20-distribution.png", plot = p, width = 7.5, height = 4.8, dpi = 140)
p <- ggplot(trial, aes(x = material, y = drop_c)) + geom_boxplot(outlier.shape = NA, width = 0.45) + geom_point(position = position_jitter(width = 0.09, height = 0, seed = 20), colour = "#256187", alpha = 0.7) + labs(x = "Material", y = "Cooling (C)", title = "Show the observations as well as the box") + theme_minimal(base_size = 13)
ggsave("results/20-groups.png", plot = p, width = 7.5, height = 4.8, dpi = 140)
print(table(trial$material))
