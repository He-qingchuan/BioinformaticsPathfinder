# 数据调查小镇 · 第 30 节
# 在 r-lab 项目根目录运行；输出只写入 results。
parks <- read.csv("data/independent_sites.csv")
print(nrow(parks))
print(round(cor(parks$canopy_pct, parks$temperature_c, method = "pearson"), 3))
# 相关系数描述线性关系；不能排除地形、时间等其他解释。
