# 数据调查小镇 · 第 29 节
# 在 r-lab 项目根目录运行；输出只写入 results。
trial <- read.csv("data/shade_trial.csv")
a <- trial$drop_c[trial$material == "A"]
b <- trial$drop_c[trial$material == "B"]
comparison <- t.test(b, a, alternative = "two.sided", var.equal = FALSE, conf.level = 0.95)
print(c(n_A = length(a), n_B = length(b)))
print(round(c(mean_A = mean(a), mean_B = mean(b), difference_B_minus_A = mean(b) - mean(a)), 3))
print(round(comparison$conf.int, 3))
print(signif(comparison$p.value, 4))
print(comparison$method)
