# 数据调查小镇 · 第 07 节
# 在 r-lab 项目根目录运行；输出只写入 results。
temperature <- c(27, NA, 29)
print(is.na(temperature))
print(mean(temperature))
print(mean(temperature, na.rm = TRUE))
print(sum(!is.na(temperature)))
print(c(1, "2"))
print(as.numeric(c("27", "29")))
print(c(1, 2, 3, 4) + c(10, 20))
# 长度整除时也会回收；没有警告不等于符合你的意图。
