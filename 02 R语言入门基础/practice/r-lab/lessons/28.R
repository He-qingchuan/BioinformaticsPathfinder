# 数据调查小镇 · 第 28 节
# 在 r-lab 项目根目录运行；输出只写入 results。
# 演示假设成立时，样本均值仍会波动。这里特意设定已知总体标准差 3。
set.seed(28)
null_means <- replicate(10000, mean(rnorm(20, mean = 30, sd = 3)))
observed_mean <- 31.2
# 双侧：离 30 至少同样远；这不是“零假设为真的概率”。
simulated_p <- mean(abs(null_means - 30) >= abs(observed_mean - 30))
exact_p <- 2 * pnorm(-abs(observed_mean - 30) / (3 / sqrt(20)))
print(round(c(simulated_p = simulated_p, normal_model_p = exact_p), 4))
