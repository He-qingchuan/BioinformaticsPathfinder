# V3 术语增强版验收记录 · 2026-09-16

本次只增强术语及其入口，未重新运行真实 RNA-seq 分析。课程正文、图解、数据和素材与 V2 的保留情况以字节摘要及去除术语包装后的 HTML 核验。

| 记录 | 本次核验内容 |
| --- | --- |
| `v2_backup_manifest.json` | V2 原 346 个文件、原 ZIP、26 项旧术语和 16 站原 HTML 摘要；原版与完整备份均保留 |
| `glossary_validation.json` | 178 项完整结构、旧锚点、16 站原文、首次出现规则、编号/公式保护和变更范围 |
| `glossary_coverage.json` / `术语覆盖清单.md` | 1,304 处正文或独立图解入口及其上下文，另说明 5 项经相关入口补充的基础概念 |
| `glossary_reader_review.md` | 两轮独立新读者审读，覆盖 8 类主要误解及已落实的措辞修正 |
| `glossary_browser.json` | 749 组中英文名、缩写与别名查询；精确单项解释、主题浏览、三层窗口、焦点与滚动恢复、手机、无脚本和整包迁移 |
| `static_validation.json` | 148 条素材记录、96 个 HTML、2,810 个本地引用；16 站、20 章与 04.5、23 张真实图和 14 张新增原理插图 |
| `browser_validation.json` | 原有 16 站、23 张图、4 个实验、基因查询、自测、进度、全屏、3 份离线报告和资料馆回归检查 |
| `figures_review.json` | 37 处放大图解、14 张 SVG 文字边界和 320/390/768/1440/1920 像素宽度下图文适配 |
| `responsive_review.json` | 320/390/768/1440 像素宽度下首页、地图标题点击与正文检查 |
| `print_review.json` | 本机 A4 样张 188 页；178 项中文名、178 项英文名、712 段完整术语解释，以及原 23 份图摘要、149 个读图小节、14 份插图摘要、28 段插图解释、21 份原示意说明和 16 份自测解析 |
| `independence_validation.json` | 复制到含中文与空格的临时目录，禁止访问整个原工作目录及网络，独立重建后 302 个非 QA 文件字节一致 |
| `v3_delivery_check.json` | 最终备份、复制独立性、保留文件和全部验收记录汇总 |

浏览器均离线运行，没有自动 HTTP(S) 请求或脚本错误。查看官方资料的外链由读者自愿点击，词条本身不依赖联网。普通网页阅读不需要本机测试时使用的 Python、markdown-it-py、Playwright、Chromium 或 Poppler。

`glossary_membership_320/390/768/1440.png` 是术语窗口实拍；`glossary_print_98/125/169.png` 是实际 PDF 代表页，检查附录起始、TPM/TMM 与隶属度的中英排版和完整段落。188 页对应本机 A4、12 mm 上下及 13 mm 左右页边距；其他字体或打印设置可能改变分页。PDF 只用于临时验收，没有增加第三个学习入口。

PDF 文本核验使用 `pdftotext -raw` 和 Unicode/空白归一化；数学比较符号 `<`、`>` 按文字保留，不当作 HTML 标签删除。完整段落核验通过后另看代表页的实际渲染。

`v1_backup_manifest.json`、`docs_import.json`、`delivery_check.json`、`science_review.md` 等保留 V2 的历史来源记录，不用它们替代本次 V3 验收。旧版 `print_page_*.png` 为历史样张，本次打印以 `glossary_print_*.png` 为准。

## 维护者复查

在教学包根目录运行：

```bash
python tools/build.py
python qa/validate.py
python qa/glossary_validate.py
node qa/browser.cjs
node qa/glossary_browser.cjs
node qa/figures_review.cjs
node qa/responsive.cjs
python qa/print_validate.py /tmp/rnaseq-v3-print-proof.pdf
python qa/independence.py
python qa/v3_delivery_check.py
```

历史 V2 目录存在时会额外检查其备份；整包单独移动后，正文保留检查仍可使用随包的摘要。独立构建测试仅在子进程中禁止原目录访问，不会改名、移动或禁用真实分析项目。
