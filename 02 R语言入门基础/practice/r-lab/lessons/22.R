# 数据调查小镇 · 第 22 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(ggplot2))
parks <- read.csv("data/independent_sites.csv")
p <- ggplot(parks, aes(canopy_pct, temperature_c)) + geom_point(colour = "#256187", size = 2.5) + labs(title = "Shade and temperature: a simulated survey", subtitle = "30 independent sites; association is not causation", x = "Canopy cover (%)", y = "Temperature (C)", caption = "Original simulated data | Data Town") + theme_minimal(base_size = 13)
dir.create("results", showWarnings = FALSE)
ggsave("results/22-labelled.png", plot = p, width = 7.5, height = 5, units = "in", dpi = 140)
ggsave("results/22-labelled.pdf", plot = p, width = 7.5, height = 5, units = "in")
print(file.exists(c("results/22-labelled.png", "results/22-labelled.pdf")))
