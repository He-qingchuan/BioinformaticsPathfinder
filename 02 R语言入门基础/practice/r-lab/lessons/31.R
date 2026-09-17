# 数据调查小镇 · 第 31 节
# 在 r-lab 项目根目录运行；输出只写入 results。
parks <- read.csv("data/independent_sites.csv")
model <- lm(temperature_c ~ canopy_pct, data = parks)
print(round(coef(model), 4))
print(round(confint(model), 4))
print(round(predict(model, newdata = data.frame(canopy_pct = 50), interval = "confidence"), 3))
print(round(summary(model)$r.squared, 3))
