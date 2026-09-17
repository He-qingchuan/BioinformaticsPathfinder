# 数据调查小镇 · 第 19 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(ggplot2))
parks <- read.csv("data/independent_sites.csv")
p <- ggplot(parks, aes(x = canopy_pct, y = temperature_c)) +
  geom_point(colour = "#256187", size = 2.5) +
  labs(x = "Canopy cover (%)", y = "Temperature (C)", title = "One dot, one independent site") +
  theme_minimal(base_size = 13)
dir.create("results", showWarnings = FALSE)
ggsave("results/19-mapping.png", plot = p, width = 7.5, height = 4.8, dpi = 140)
print(nrow(parks))
