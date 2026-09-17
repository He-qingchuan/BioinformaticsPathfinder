# 数据调查小镇 · 第 06 节
# 在 r-lab 项目根目录运行；输出只写入 results。
temperature <- c(27, 29, 28, 31)
print(temperature[c(1, 4)])
keep <- temperature >= 29
print(keep)
print(temperature[keep])
print(temperature[temperature >= 28 & temperature < 31])
print(c("P01", "P04") %in% c("P01", "P02", "P03"))
