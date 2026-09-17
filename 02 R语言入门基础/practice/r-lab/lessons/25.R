# 数据调查小镇 · 第 25 节
# 在 r-lab 项目根目录运行；输出只写入 results。
trial <- read.csv("data/shade_trial.csv")
observations <- read.csv("data/observations.csv")
print(c(trial_rows = nrow(trial), independent_units = length(unique(trial$unit_id))))
print(c(observation_rows = nrow(observations), distinct_sites = length(unique(observations$site_id))))
# 同一地点的重复记录不等于同样多的独立地点。
