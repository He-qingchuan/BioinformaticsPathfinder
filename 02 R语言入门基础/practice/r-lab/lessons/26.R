# 数据调查小镇 · 第 26 节
# 在 r-lab 项目根目录运行；输出只写入 results。
set.seed(26)
first <- rnorm(5, mean = 30, sd = 3)
set.seed(26)
second <- rnorm(5, mean = 30, sd = 3)
print(identical(first, second))
# 每一列是一份新的独立样本，而不是把一份观测反复抄写。
set.seed(2601)
means <- replicate(1000, mean(rnorm(20, mean = 30, sd = 3)))
print(round(c(mean_of_means = mean(means), spread_of_means = sd(means), theoretical_se = 3 / sqrt(20)), 3))
dir.create("results", showWarnings = FALSE)
png("results/26-sampling.png", width = 1000, height = 620, res = 120)
hist(means, breaks = 25, col = "#8ebabb", border = "white", main = "1000 samples, 1000 means", xlab = "Sample mean (n = 20)")
abline(v = 30, col = "#b9553d", lwd = 2)
invisible(dev.off())
