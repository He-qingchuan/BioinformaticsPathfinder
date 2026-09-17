# 数据调查小镇 · R 练习项目

所有资料为原创模拟教学数据，种子为 `20260917`，由 `scripts/make_data.R` 生成。不代表真实地点、材料性能或研究结论。生成过程固定并随包保存；普通练习直接使用已经提供的 CSV，不必重建数据。

## 开始练习

先安装 R 和 RStudio Desktop，双击 `r-lab.Rproj`。使用 `getwd()` 检查当前工作目录；`file.exists("data/observations.csv")` 应为 TRUE。

在 RStudio 打开 `lessons/02.R`，选中代码点击 Run，或在控制台执行 `source("lessons/02.R")`。逐课完整脚本不依赖其他章节留下的对象。第 13 节开始使用扩展包，首次需要联网显式运行 `source("setup.R")`。普通分析不会自动安装软件。安装依赖后可在断网情况下进行随包数据练习。

项目关闭工作区自动恢复和自动保存；请保存 `.R` 脚本。所有生成内容放在 `results`，不要覆盖 data。输出目录可以重复运行并覆盖其中的同名结果，因此应为不同分析选择不同目录。

## 数据文件和设计

| 文件 | 大小与单位 | 设计与用途 |
|---|---|---|
| observations.csv | 原始 43 行；去完全重复后 42 条地点与时段记录 | 3 地点 × 7 天 × 2 时段；包含 1 条完全重复、2 条温度缺失、1 处日期斜线、标签空格大小写变体；只作描述 |
| sites.csv | 3 个地点，每个编号唯一 | 提供地点名称及冠层覆盖率，连接为 many-to-one |
| temperatures_wide.csv | 3 地点 × 2 时段 | 单独的小型形状示例，不是原始表的完整截取；用于宽长转换 |
| shade_trial.csv | 48 个独立装置，A/B 各 24 个 | 模拟随机分组，各装置测一次降温；用于独立两组 Welch 比较 |
| independent_sites.csv | 30 个模拟独立地点，各测一次 | 横断面冠层覆盖与温度，生成时使用独立噪声；用于关联与线性回归，不作因果主张 |
| new_observations.csv | 原始 13 行，去重复后 12 行 | 3 地点 × 2 天 × 2 时段；1 完全重复、1 温度缺失；用于流程迁移 |

## 字段字典

| 字段 | 类型 / 单位 | 约定 |
|---|---|---|
| record_id | 字符 | 观察记录编号；完全相同的重复导入可去重，编号冲突必须回查 |
| site_id | 字符 | P01/P02/P03 是重复观察地点；S01…S30 属于独立横断面数据，不能混作相同设计 |
| date | 日期文本 | 观察发生日；原始表以 YYYY-MM-DD 为主，包含一处斜线，需要明确转换 |
| period | 类别 | morning 上午；afternoon 下午；展示顺序由因子水平指定 |
| temperature_c | 数值 / °C | 温度；CSV 空白为缺失，不是零 |
| visitors | 整数 / 人次 | 模拟记录中的来访计数，本课程不对其进行总体推断 |
| note | 字符 | regular 常规、check 待检查；原始表含大小写和首尾空格变体 |
| site_name | 字符 | Riverside 河畔、Meadow 草地、Grove 林地 |
| canopy_pct | 数值 / % | 0—100 的冠层覆盖百分数；回归的 1 单位是 1 个百分点 |
| unit_id | 字符 | 独立实验装置编号，不允许重复 |
| material | 类别 | 模拟材料 A / B；随机分配，不是真实产品名 |
| start_c / end_c | 数值 / °C | 同一装置开始与结束温度；它们不是两份独立装置 |
| drop_c | 数值 / °C | start_c − end_c，降温为正；预先比较 B−A |
| morning / afternoon | 数值 / °C | 宽表示例的两个温度列，转长后进入 period 和 temperature_c |

CSV 采用 UTF-8、逗号分隔、首行为字段名，不写 R 行名。RDS 仅是课程演示的派生结果，原始输入采用可直接检查的 CSV。

## 综合分析

```r
source("scripts/analyse.R")
first <- analyse_records("data/observations.csv", "results/first-week")
next_week <- analyse_records("data/new_observations.csv", "results/next-week")
```

输出包括 clean.csv、summary.csv、observations.png、regression.png、report.md 和 session-info.txt。换观察表只更新描述性观察部分；实验和横断面部分仍来自固定文件，不能声称获得了新的实验验证。

统计约定：独立两组均值比较使用 Welch 双侧方法，方向 B−A；置信区间为 95%。回归含截距、一个连续解释变量，检查残差与外推范围。完整分析对缺列、冲突编号、非法日期和未知地点停止处理。对数据生成设定的了解不能替代真实资料中的设计判断。
