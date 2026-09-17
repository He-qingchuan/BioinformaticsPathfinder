# 数据调查小镇 · 第 23 节
# 在 r-lab 项目根目录运行；输出只写入 results。
mean_if_present <- function(x) {
  if (all(is.na(x))) {
    return(NA_real_)
  }
  mean(x, na.rm = TRUE)
}
print(mean_if_present(c(26, NA, 28)))
print(mean_if_present(c(NA_real_, NA_real_)))
print(mean_if_present(c(30, 32)))
