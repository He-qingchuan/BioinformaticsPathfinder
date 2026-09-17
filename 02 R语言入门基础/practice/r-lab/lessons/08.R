# 数据调查小镇 · 第 08 节
# 在 r-lab 项目根目录运行；输出只写入 results。
records <- data.frame(site = c("P01", "P02", "P03"), temperature = c(27, 30, 26))
print(records)
print(dim(records))
print(records$temperature)
print(records[2, , drop = FALSE])
print(records[records$temperature >= 27, c("site", "temperature"), drop = FALSE])
records$temperature_f <- records$temperature * 9 / 5 + 32
print(records)
