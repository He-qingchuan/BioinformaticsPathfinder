# 数据调查小镇 · 第 21 节
# 在 r-lab 项目根目录运行；输出只写入 results。
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))
x <- read.csv("data/observations.csv", stringsAsFactors = FALSE) |> distinct()
x$date <- as.Date(gsub("/", "-", x$date))
x$period <- factor(x$period, levels = c("morning", "afternoon"))
p <- ggplot(x, aes(date, temperature_c, colour = period, group = period)) + geom_line(na.rm = TRUE) + geom_point(na.rm = TRUE) + facet_wrap(~ site_id, nrow = 1) + scale_colour_manual(values = c("#256187", "#b9553d")) + labs(x = "June 2026", y = "Temperature (C)", colour = "Period", title = "Same scales, separate sites") + theme_minimal(base_size = 12)
dir.create("results", showWarnings = FALSE)
ggsave("results/21-trends.png", plot = p, width = 9, height = 4.5, dpi = 140)
print(c(records = nrow(x), missing_temperature = sum(is.na(x$temperature_c))))
