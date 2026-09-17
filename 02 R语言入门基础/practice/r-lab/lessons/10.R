# 数据调查小镇 · 第 10 节
# 在 r-lab 项目根目录运行；输出只写入 results。
measurements <- matrix(1:6, nrow = 3, dimnames = list(c("P01", "P02", "P03"), c("morning", "afternoon")))
print(measurements)
print(measurements[2, 1])
print(dim(measurements[, 1, drop = FALSE]))
box <- list(title = "Park notes", readings = measurements, checked = TRUE)
print(names(box))
print(class(box["readings"]))
print(class(box[["readings"]]))
print(box$readings)
