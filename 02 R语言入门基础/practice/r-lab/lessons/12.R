# 数据调查小镇 · 第 12 节
# 在 r-lab 项目根目录运行；输出只写入 results。
# 先用四个数看清概念；最后一个值会把均值拉高。
x <- c(26, 27, 28, 39)
print(c(n = length(x), mean = mean(x), median = median(x), sd = round(sd(x), 2)))
print(quantile(x))
dir.create("results", showWarnings = FALSE)
png("results/12-first-plot.png", width = 1000, height = 620, res = 120)
plot(seq_along(x), x, pch = 19, col = "#256187", xlab = "Record", ylab = "Temperature (C)", main = "Read the values before averaging")
abline(h = mean(x), col = "#b9553d", lty = 2)
abline(h = median(x), col = "#36866f", lty = 3)
legend("topleft", c("Mean", "Median"), col = c("#b9553d", "#36866f"), lty = c(2, 3), bty = "n")
invisible(dev.off())
