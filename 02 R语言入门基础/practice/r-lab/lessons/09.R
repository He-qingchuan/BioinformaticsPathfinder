# 数据调查小镇 · 第 09 节
# 在 r-lab 项目根目录运行；输出只写入 results。
period <- factor(c("afternoon", "morning", "morning"), levels = c("morning", "afternoon"))
print(period)
print(table(period))
print(levels(period))
labels <- factor(c("10", "20", "10"))
print(as.integer(labels))
print(as.numeric(as.character(labels)))
