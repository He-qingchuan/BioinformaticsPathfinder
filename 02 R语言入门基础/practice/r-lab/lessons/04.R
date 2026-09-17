# 数据调查小镇 · 第 04 节
# 在 r-lab 项目根目录运行；输出只写入 results。
# 从 r-lab.Rproj 打开项目，再运行脚本；路径从项目根目录出发。
print(file.exists("data/observations.csv"))
dir.create("results", showWarnings = FALSE)
writeLines("My first reproducible note", "results/first-note.txt")
print(readLines("results/first-note.txt"))
