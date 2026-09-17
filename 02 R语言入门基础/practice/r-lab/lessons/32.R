# 数据调查小镇 · 第 32 节
# 在 r-lab 项目根目录运行；输出只写入 results。
parks <- read.csv("data/independent_sites.csv")
model <- lm(temperature_c ~ canopy_pct, data = parks)
print(round(range(parks$canopy_pct), 1))
print(round(c(residual_mean = mean(residuals(model)), residual_sd = sd(residuals(model))), 4))
dir.create("results", showWarnings = FALSE)
png("results/32-diagnostics.png", width = 1200, height = 620, res = 120)
par(mfrow = c(1, 2))
plot(fitted(model), residuals(model), pch = 19, col = "#256187", xlab = "Fitted temperature", ylab = "Residual", main = "Look for curves or changing spread")
abline(h = 0, lty = 2)
qqnorm(residuals(model), pch = 19, col = "#256187", main = "Check the normal approximation")
qqline(residuals(model), col = "#b9553d")
invisible(dev.off())
