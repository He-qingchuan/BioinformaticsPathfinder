## A · 环境、安装与包版本

普通阅读不需要 R、Python 或 Node。实际练习使用 R 与可选的 RStudio Desktop；推荐 R 4.6.1，兼容性与实际验证范围见维护说明。首次安装四个扩展包需要网络，教材、代码、数据与参考图都在包内。

安装报错时先查看完整消息和 `sessionInfo()`。确认镜像使用 HTTPS、网络可达、R 与操作系统版本受支持；Windows/macOS 优先使用匹配版本的官方二进制包。不要把来源不同、编译环境不同的包目录直接拼接到 `.libPaths()`。

需要固定依赖时，可以在独立项目中使用 renv 保存和恢复包版本。恢复可能联网获取包，锁文件不等于把所有包安装文件放进教材。对首次学习者，先完成 setup.R 和小例子，再了解依赖管理。R 与包的实际运行版本记录在验证产物以及综合分析的 session-info.txt。

## B · 旧写法与现代接口对照

| 遇到的写法或习惯 | 本教材采用的做法 |
|---|---|
| 在脚本中写自己的绝对路径 | 从项目根目录使用相对路径 |
| 依赖上次保存的整个工作区 | 重启后用脚本从输入重新生成 |
| `%>%` 管道 | 主线统一使用原生 `|>`；复杂占位语法不应机械替换 |
| `T`、`F` | 使用完整 `TRUE`、`FALSE`，避免短名称被重新赋值 |
| `..prop..` 等旧图形统计记法 | 按现行 ggplot2 文档使用 `after_stat()`；初学先区分原始记录与汇总数据 |
| 给任何图直接加比较星号 | 先确认设计、估计目标和方法条件，再报告效应、区间和 p 值 |
| 安装失败就混用其他环境的包库 | 检查版本、平台和编译依赖；在独立环境恢复明确版本 |

基础 R 图形仍然有明确用途，不能简单理解为“过时不能用”。本教材在第 12、26、27、32 节使用基础图形，其他章节使用 ggplot2。

## C · 怎样继续学习统计

主线覆盖描述统计、抽样、均值区间、独立两组 Welch 比较、Pearson 相关和一元线性回归。后续按实际问题学习配对设计、多重比较、多变量模型、非线性关系和相关数据结构。学习新方法前，先明确观察单位和目标参数。

不要通过多次尝试结果后再决定检验方向、分组或删除哪些点。需要探索时明确标注探索性质，保留完整过程，并考虑后续验证。对统计定义可查 NIST 手册和 ASA 声明；对 R 的参数及返回值查官方函数文档。

## D · 历史、接口与原始资料

以下资料用于核对概念和接口，教材的故事、模拟数据、图解和讲解重新编写；阅读主线不要求先读其他教材。

- [R 官方介绍](https://www.r-project.org/about.html)：R 的定位与背景。
- [An Introduction to R](https://cran.r-project.org/doc/manuals/r-release/R-intro.html)：对象、语法与基础统计计算。
- [RStudio Projects](https://docs.posit.co/ide/user/ide/guide/code/projects.html)：项目与工作目录。
- [dplyr 的表格连接](https://dplyr.tidyverse.org/reference/mutate-joins.html)：连接类型及关系检查。
- [tidyr 宽长转换](https://tidyr.tidyverse.org/reference/pivot_longer.html)：转换参数与数据形状。
- [ggplot2 图形语法](https://ggplot2.tidyverse.org/reference/ggplot.html)与[统计映射](https://ggplot2.tidyverse.org/reference/aes_eval.html)：图层、映射和当前接口。
- [R 的 t.test 文档](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/t.test.html)与[lm 文档](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/lm.html)：参数、方法和返回值；同时以本机 `?t.test`、`?lm` 对照实际版本。
- [NIST：置信区间](https://www.itl.nist.gov/div898/handbook/prc/section1/prc14.htm)：重复抽样与覆盖解释。
- [ASA：p 值声明](https://www.amstat.org/asa/files/pdfs/P-ValueStatement.pdf)：p 值含义和解释边界。

## E · 图形、报告与使用来源

本教材的地图与概念图是可编辑 SVG；所有展示的统计图都来自随包 R 代码。统计图使用英文标签与中文读图说明，避免依赖某台电脑独有的中文绘图字体。正文、术语、数据字典、脚本和参考结果一起构成可复查的学习材料。

原 R 笔记保留在重构前的 Git 历史中。新版重新组织知识与案例，不要求读者参考旧公众号材料，也不保留无法随包运行的隐藏数据依赖。R、RStudio 和各扩展包均属于其原作者，使用时遵守各自许可；本仓库没有为这些第三方软件重新授权。
