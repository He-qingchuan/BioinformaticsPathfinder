# 本地报告展示资源

`plotly.min.js` 为 Plotly.js 2.25.2，来自本机已安装的 `r-plotly` 4.12.1 包中 `htmlwidgets/lib/plotlyjs/plotly-latest.min.js`，按原字节复制。许可保存在 `plotly.LICENSE`；不通过网页运行时下载 CDN 文件。

SHA256：`419deebe105f4c993feb7e6d1fe94fb1c2f7f98716db5d9b8fe3e37773838898`。

用途仅为 fastp 旧 HTML 报告的离线预览：只在返回浏览器的临时响应中改写脚本地址，不在项目集合生成报告副本。原始报告、曲线数值和统计结果不修改。迁移时保留本目录即可，不需要安装额外的 Plotly R/Python 包。
