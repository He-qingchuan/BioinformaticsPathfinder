# 数据调查小镇 · 第 27 节
# 在 r-lab 项目根目录运行；输出只写入 results。
# 来自正态总体的独立样本；总体均值 30 是模拟者知道的真值。
set.seed(27)
intervals <- replicate(1000, {
  x <- rnorm(20, mean = 30, sd = 3)
  margin <- qt(0.975, df = length(x) - 1) * sd(x) / sqrt(length(x))
  c(lower = mean(x) - margin, upper = mean(x) + margin)
})
covered <- intervals["lower", ] <= 30 & intervals["upper", ] >= 30
print(round(mean(covered), 3))
print(round(intervals[, 1:3], 2))
dir.create("results", showWarnings = FALSE)
png("results/27-intervals.png", width = 1000, height = 700, res = 120)
plot(NA, xlim = range(intervals[, 1:40]), ylim = c(1, 40), xlab = "Mean temperature (C)", ylab = "Repeated sample", main = "40 intervals from repeated sampling")
segments(intervals[1, 1:40], 1:40, intervals[2, 1:40], 1:40, col = ifelse(covered[1:40], "#256187", "#b9553d"), lwd = 2)
abline(v = 30, lty = 2)
invisible(dev.off())
