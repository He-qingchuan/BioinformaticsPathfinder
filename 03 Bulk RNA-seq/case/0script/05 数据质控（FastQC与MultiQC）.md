# 05 数据质控：FastQC 与 MultiQC

<!-- normalized-inputs -->
输入字段和项目迁移规则见[输入规范](<附4 输入文件规范与项目迁移.md>)。代码从能看到 `0script` 的项目根目录运行。

FastQC 对每个 FASTQ 统计碱基质量、序列长度、接头、重复等信息；MultiQC 把多个样本的报告放在同一页面比较。先看原始数据，再经过 fastp 过滤并复查。RNA-seq 的高表达转录本本来就会产生较高重复率，单个黄色或红色标记不能直接证明样本不可用。

## 本章从哪里读取参数

以下值来自 [project.env](project.env)，不是写死在函数里的常量。案例值与新项目模板值分别列出；实际运行读取你当前文件中的设置。图形特有参数仍在本章入口集中设置。修改后需重新运行读取/赋值段，再调用函数；已经在内存中的旧变量不会随文件编辑自动刷新。

| 参数 | 当前案例配置 | 空模板默认 | 用途与修改注意 |
| --- | --- | --- | --- |
| `THREADS` | `24` | `24` | 上游和注释的总线程预算，正整数；默认 24。 按服务器实际分配资源调小或调大，不超过可用 CPU/内存；样本并行数还由各章 sample_jobs 分配。 |

## 1. 根据样本表读取双端文件

先在终端激活 `rnaseq`，确认当前目录是项目根目录。原始文件已由第 04 章获得或迁移到 `2data/rawdata`，本章不再次下载、不批量改名。

实现：[查看编号脚本](scripts/05_raw_qc.sh)。

<!-- execute: raw_qc env=rnaseq -->
```bash
# 目的：对样本表中的每端原始 FASTQ 做 FastQC 并用 MultiQC 汇总。
# 关键输出：2data/rawdata/qc/原FASTQ名_fastqc.html 和 .zip；总体页 2data/rawdata/multiqc/raw_multiqc.html。
#   ZIP 是压缩报告，不使用 head；下面的 raw_qc_summary 会另存可直接查看的统计表。
# 前提/去向：输入：samples.tsv 的 sample_id/read1/read2，文件位于 2data/rawdata；
#   输出 qc/*.html/*.zip与 multiqc/raw_multiqc.html。
# 先 source 加载同编号脚本定义，再设置下面变量并调用函数；加载本身不启动分析。所有路径相对能看见0script 的项目根目录。
# 本入口无位置参数；样本名/分组从 samples.tsv 获取，线程等共用设置从 project.env 获取，不必逐样本改代码。
# 执行环境：rnaseq；命令退出不代表所有后续章节都已完成，查看本步结果/日志后再继续。

source 0script/scripts/05_raw_qc.sh
run_raw_qc
```

## 2. 参数及报告解读

| 参数或模块 | 含义 | 核对内容 |
| --- | --- | --- |
| `--threads` | 并行读取的文件数 | 线程和内存预算来自入口参数，不无限并行 |
| `--outdir` | 报告保存位置 | 不与原始 FASTQ 混在同一层 |
| Per base sequence quality | 各测序位置的 Phred 质量分布 | 末端质量下降是否明显；Q20 约对应 1% 错误概率 |
| Adapter content | 接头序列出现情况 | 是否需要过滤，过滤后是否改善 |
| Sequence length distribution | read 长度分布 | 原始与过滤后不同，不能假定所有 reads 等长 |
| Duplication levels | 重复序列比例 | 结合 RNA-seq 表达不均匀性和文库复杂度判断 |
| Overrepresented sequences | 过度出现的序列 | 核对接头、rRNA 或高表达生物学序列来源 |

详细模块解释见 [FastQC 官方帮助](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/Help/)。报告中的 warning/fail 是规则提示，不是自动删样本的命令。是否存在样本异常还要结合第 09 章相关性、PCA 和实验记录。

## 3. 输出在哪里

`rawdata/qc` 中每个 mate 有一份 `*_fastqc.html` 和 `*_fastqc.zip`。ZIP 内的 `fastqc_data.txt` 是结构化统计，`summary.txt` 是模块状态。`rawdata/multiqc/raw_multiqc.html` 是总体入口，旁边的 `raw_multiqc_data` 或 `multiqc_data` 保存汇总数据，以本次程序实际输出为准。

[打开原始数据 MultiQC 报告](../2data/rawdata/multiqc/raw_multiqc.html)。本地 Markdown 查看器若不直接显示 HTML，可在浏览器中打开该文件。关键比较图在第 06 章与过滤后结果一起展示。

本次 42 个原始 mate 均完成 FastQC。Adapter Content 模块均为 fail，提示必须检查接头；Per sequence GC content 为 33 个 pass、9 个 warn。这里的模块计数不是失败文库数，不能据此删除样本。第 06 章据此进行接头处理并复查。

## 4. 把重要诊断保存为表格

下面只读取已经生成的 FastQC ZIP，不重新扫描大 FASTQ。每行一个 mate，保留质量编码、read 数、长度和模块状态，方便与第 06 章交叉检查。

实现：[查看编号脚本](scripts/05_raw_qc_summary.R)。

<!-- execute: raw_qc_summary env=rnaseq -->
```r
# 目的：汇总双端 FastQC ZIP 中的模块状态和质量范围。
# 关键输出：2data/rawdata/raw_qc_summary.tsv：每个 mate 的质量编码、read 数和 FastQC 模块状态。
#   report_dir 只改变从哪里读 ZIP，不改变这个固定汇总输出位置。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：写 2data/rawdata/raw_qc_summary.tsv；不可见返回 report_dir。读取失败中止，红黄标记不自动删样本。
# 共用读取：readRenviron 读取 project.env；Sys.getenv 返回文本，as.numeric/as.integer 将阈值/种子转成数值。
#   更改配置后需重新执行读取与赋值，旧变量不会自动刷新。
# 参数设置（下方为本次取值；不需要修改函数内部实现）：
# report_dir：字符路径；已有 FastQC ZIP 的目录。读取其中的 fastqc_data.txt，不重新扫描测序文件。
# 调用：先加载脚本，再设置参数，最后运行函数。改值后重新执行赋值和调用。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/05_raw_qc_summary.R")
report_dir <- "2data/rawdata/qc"
# interface-parameters: raw_qc_summary
run_raw_qc_summary(
  report_dir = report_dir
)
```

### 查看本步关键文件

每行对应一个 mate。查看样本标识、质量编码、read 数及模块状态，不能把一行当成一个独立生物学重复。

```bash
# 目的：查看本步文本结果的前 10 行；在项目根目录的 Bash 终端运行，只读不写。
# 前提：上一步已成功完成；报错后即使同名文件存在，也不能据此认定本次成功。
# head -n 10 含表头最多读 10 行；test -f 检查文件；printf 先显示路径，避免混淆。
preview_file="2data/rawdata/raw_qc_summary.tsv"
if test -f "$preview_file"; then
  printf "\n文件：%s\n" "$preview_file"
  head -n 10 "$preview_file"
else
  printf "尚无此文件：%s；先检查上一步是否完成。\n" "$preview_file"
fi
```

均一质量值不能被当作优秀测序质量的证据。Phred+33 中 `?` 对应 Q30；本案例部分文库的原始输入已出现这种均一值。原始文件的 ENA MD5 校验通过，不是本次过滤凭空生成质量值。它与简化质量存储的表现相容，但仅凭字符不能确定生成原因。[NCBI 的格式说明](https://www.ncbi.nlm.nih.gov/sra/docs/sra-data-formats/)解释了 SRA Lite 的固定质量机制；本次从 ENA 下载，尚无证据把每个相关文库都直接归因为 SRA Lite。需要原始逐碱基质量评估时，应追溯提交文件或完整质量格式，而不是比较哪个样本 Q30 更高。
