# R 入门 · 数据调查小镇

从第一行 R 代码，走到一张读得懂的图，再到一份能解释依据、能够重新运行的分析简报。独立的开放学习教材，不要求先学 Linux、Python 或转录组。

[在线阅读](https://he-qingchuan.github.io/BioinformaticsPathfinder/r/) · [打开本地教材](index.html) · [全文阅读与打印](reading.html) · [代码、下载与来源](library.html)

## 开始学习

下载 [练习项目](practice/r-lab.zip)，解压并在安装 R 和 RStudio Desktop 后打开 `r-lab.Rproj`。第 02—04 节介绍准备、控制台、脚本与项目。网页不会执行 R；每课提供真实运行的完整脚本与参考结果。

完整教材 ZIP 从 [r-v1.0.0 发布页](https://github.com/He-qingchuan/BioinformaticsPathfinder/releases/tag/r-v1.0.0)下载。保留整个目录，解压后打开 index.html 即可离线阅读、查看图解、查术语和浏览参考结果。实际练习还需要 R 及第 13 节说明的扩展包；首次安装需要网络，安装完后可使用随包数据离线练习。

## 教材内容

36 节正文，8 个小镇街区，69 个中英术语，21 张原创 SVG 概念图，11 幅展示于正文的实际 R 图形，35 份逐课 R 脚本，6 份模拟数据表，以及完整分析与数据生成脚本。

01—10 从 R、RStudio、项目学到向量、数据框、因子、矩阵和列表；11—18 读写、描述和整理数据；19—24 绘图及简单程序；25—32 抽样、区间、假设检验、Welch 比较、相关和一元回归；33—36 排错、完整分析和换数据复跑。

首页是小镇地图，选择街区后打开课程；手机显示纵向街道。云、飞鸟、树梢与旗帜有轻微动态，可暂停，遵循系统减少动态偏好，离开视口及进入后台会暂停。地图与目录可切换，已读记录只保存在当前浏览器。禁用 JavaScript 后仍有静态入口、完整目录和术语锚点。

所有公园、地点和材料数据均为原创模拟资料，不能用于宣称真实研究结论。数据字典写明观察单位和生成方法：重复地点记录只作描述，独立随机分组装置用于 Welch 比较，独立地点横断面资料用于相关与回归。报告明确区分三种设计，不用数据行数替代独立样本数。

## 代码与维护

`content` 保存正文、课程配置、图注和术语；`practice/r-lab` 是可直接运行的项目；`practice/expected` 保存已核对输出；`assets` 是本地样式、脚本、SVG 与 R 生成图；`tools` 负责静态生成与打包；`qa` 负责代码、数据、网页和浏览器检查。

正文通过标记引用真实 `.R` 源码和参考输出，地图、目录与进度从课程配置生成，没有固定“每区几节”的假设。图解由本课程自己的代码生成，网页构建不联网、不执行 R、不安装包，也不读取其他课程。完整离线包包含本教材的源文件、数据与构建工具，第三方运行环境需按说明安装。

```bash
python -m pip install -r requirements.txt
python qa/check_r.py
python qa/check_semantics.py
python tools/build.py
python qa/validate.py
npm --prefix qa ci --ignore-scripts --no-audit --no-fund
npx --prefix qa playwright install --with-deps chromium
node qa/browser.cjs
python tools/package.py
```

上述命令供维护者在本教材目录中使用。若 Rscript 不在 PATH，可向两个 R 检查程序传入 `--rscript /path/to/Rscript`。只有显式运行 `qa/check_r.py --record` 才更新参考输出和统计图；更新后检查差异再提交。正常检查在临时项目中执行，不覆盖输入或预期结果。

R 4.6.1 的 Windows、macOS 和 Linux 三个平台已通过代码与统计检查。实现时的本地兼容性运行使用 R 4.5.3、dplyr 1.2.1、tidyr 1.3.2、stringr 1.6.0 和 ggplot2 4.0.3；跨平台状态与最终范围记录在 [qa/README.md](qa/README.md)。每次实际运行保存环境信息，统计图允许跨操作系统字体渲染差异，数值及数据关系须通过验证。

## 版本与来源

首版标记为 `r-v1.0.0`，更新说明见 [CHANGELOG.md](CHANGELOG.md)。旧 `R语言入门基础.md` 地址保留为新版入口；原笔记可在重构前提交 `f2dc51b` 的 Git 历史中查看。新版借鉴有用概念，重新组织文字、故事、数据和练习，来源与接口核对资料在网页附录中列出。
