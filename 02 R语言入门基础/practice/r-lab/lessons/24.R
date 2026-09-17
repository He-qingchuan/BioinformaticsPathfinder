# 数据调查小镇 · 第 24 节
# 在 r-lab 项目根目录运行；输出只写入 results。
celsius <- c(26, 28, 30)
fahrenheit <- numeric(length(celsius))
for (i in seq_along(celsius)) {
  fahrenheit[i] <- celsius[i] * 9 / 5 + 32
}
print(fahrenheit)
print(celsius * 9 / 5 + 32)
print(identical(fahrenheit, celsius * 9 / 5 + 32))
print(seq_along(numeric(0)))
