# Linux 入门 · 观察站的工作台

从第一条命令，到自己能解释的一份观察简报。独立的 Linux 入门教材，无需先学习 R、Python 或转录组。

- [在线阅读](https://he-qingchuan.github.io/BioinformaticsPathfinder/linux/)
- [打开本地教材](index.html) · [连续阅读与打印](reading.html) · [代码与资料](library.html)
- [下载练习材料](practice/linux-lab.zip)
- [下载完整教材](https://github.com/He-qingchuan/BioinformaticsPathfinder/releases/download/linux-v1.1.0/linux-v1.1.0.zip)（联网）

## 怎样开始

网页可直接阅读。完整包解压后打开 `index.html`；保留整个目录，图片、术语和代码均使用包内文件。练习使用 `practice/linux-lab.zip` 的副本，操作环境准备见第 02 节。

首页是一张自然观察站地图：从出发营地经过文件林舍、线索瞭望台、溪边工坊和运行值守站，最后到达脚本工作室。点击编号路牌打开课程；“地图／目录”可切换查看方式，手机上沿纵向步道阅读。各区域显示已读进度，并标出建议的下一站；原有阅读记录会继续使用。

飞鸟、云、树梢、溪流和水车带来轻微动态。“暂停动态”可让地图静止；系统设置减少动态效果时也会自动停止。地图离开视口或页面进入后台时暂停。禁用 JavaScript 时，静态地图和文字目录依然可以使用。

18 节主线、60 项中英术语、14 张 SVG 插图、4 个概念演示、16 组已执行的命令示例、2 个完整脚本，以及 5 份选读资料。每节都包含任务、提示、解法与理解检查。数据为人为编写的小型练习数据，不代表真实观察结论。

推荐环境为 Ubuntu 24.04 LTS + Bash + GNU 工具；Windows 使用 WSL，已有服务器可通过 SSH 练习。网页中的小演示不执行真实 Shell 命令。安装系统或软件时需要网络，离线阅读不需要。

## 内容如何维护

`content` 保存正文、课程顺序和术语；`practice` 保存实际命令、完整脚本、数据和参考输出；`tools` 根据这些文件生成网页与 SVG；`assets` 保存本地样式和交互；`qa` 保存检查程序。

`tools/atlas.py` 生成地图的 SVG 场景与章节路牌；`assets/atlas.css` 和 `assets/atlas.js` 仅在首页加载。章节名称与顺序直接取自课程数据，地图不维护另一份课程目录，也不需要外部地图服务。

正文通过标记引用原始脚本，网页中的命令与下载文件来自同一来源。生成脚本只读取本教材，不访问转录组目录、不执行练习、不安装软件。

```bash
python -m pip install -r requirements.txt
python qa/check_practice.py
python tools/build.py
python qa/validate.py
npm --prefix qa ci --ignore-scripts --no-audit --no-fund
npx --prefix qa playwright install chromium
node qa/browser.cjs
node qa/atlas.cjs
python tools/package.py
```

依赖只供维护者构建与检查，普通阅读不需要 Python、Node 或 Playwright。首次安装依赖需要网络。命令期望输出经过语义断言后记录；修改示例时显式运行 `python qa/check_practice.py --record`，随后检查输出差异。正常检查不会更新参考结果。

运行记录在被 Git 忽略的 `qa/artifacts` 中；发布包在 `dist`。复建测试会把本教材复制到含中文和空格的新目录，并禁止读取原仓库、禁止网络，核对产物摘要是否一致。

## 版本与原资料

本版本为 `linux-v1.1.0`，升级为动态探索地图。更新摘要见 [CHANGELOG.md](CHANGELOG.md)，验证范围见 [qa/README.md](qa/README.md)。首个完整教材仍可在 [v1.0.0](https://github.com/He-qingchuan/BioinformaticsPathfinder/releases/tag/linux-v1.0.0) 下载。旧 Linux 教材保留在重构前的 Git 历史（`cbd3352`）；正文与案例在 v1.0.0 重新编写，不依赖旧教程或公众号阅读前提。

Linux 拥有独立网址与完整下载包。R、Python 和转录组材料仍分别维护，本次只为 Linux 建立新教材。
