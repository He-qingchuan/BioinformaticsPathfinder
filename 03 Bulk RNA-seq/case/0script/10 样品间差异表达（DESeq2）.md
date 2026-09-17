# 10 样品间差异表达：DESeq2

<!-- normalized-inputs -->
输入字段和项目迁移规则见[输入规范](<附4 输入文件规范与项目迁移.md>)。代码从能看到 `0script` 的项目根目录运行。

DESeq2 用负二项模型描述计数，估计样本大小因子、基因离散度及组间差异。本章沿用 Trinity 的 `run_DE_analysis.pl --method DESeq2`；模型针对比较中的两组生物学重复拟合，不能把 TPM 或均值替代的伪重复送入。

## 本章从哪里读取参数

以下值来自 [project.env](project.env)，不是写死在函数里的常量。案例值与新项目模板值分别列出；实际运行读取你当前文件中的设置。图形特有参数仍在本章入口集中设置。修改后需重新运行读取/赋值段，再调用函数；已经在内存中的旧变量不会随文件编辑自动刷新。

| 参数 | 当前案例配置 | 空模板默认 | 用途与修改注意 |
| --- | --- | --- | --- |
| `FDR_CUTOFF` | `0.05` | `0.05` | 差异汇总、火山图及相应富集筛选使用的校正 P 值阈值；默认 0.05。 改小通常筛选更严格。各章具体作用见正文；不等于所有检验共享一次多重校正，也不控制所有同名局部阈值。 |
| `LOG2FC_CUTOFF` | `1` | `1` | 差异方向分类及火山图的绝对 log2FC 阈值；默认 1，即两倍变化。 增大要求更大的效应量；只改分类不重拟合 DESeq2，但须重做受影响汇总/图形并选择对应结果来源。 |
| `COUNT_MATRIX` | `3Salmon/quanti/gene.counts.matrix` | `3Salmon/quanti/gene.counts.matrix` | 第 10 章等读取的未做 TPM/TMM 归一化的基因计数矩阵路径。 自备矩阵或选择另一套定量时修改；第一列基因 ID、其余列与 sample_id 对应，不能用 TPM 冒充 counts。 |
| `DE_DESIGN_DIR` | `5DESeq2/design` | `5DESeq2/design` | 第 10 章生成和读取 Trinity 样本/比较设计表的目录。 通常保持通用目录；设计输入改变且已有输出时使用新的明确位置，避免混用旧设计。 |
| `DE_ANALYSIS_DIR` | `5DESeq2/DE_analysis` | `5DESeq2/DE_analysis/reps2_cpm1` | 第 10 章汇总时读取已有 DESeq2 统计文件的目录。 不是运行 DESeq2 时的输出开关；新统计输出由该章 analysis_dir 生成，完成后将此值指向那一套结果。 |

## 1. 比较方向和输入检查

`contrasts.tsv` 的 `test_group` 是实验组、`reference_group` 是参照组。正 log2FC 表示实验组更高，不按名称字典顺序或时间先后猜方向。同一比较表也传给后续韦恩图、火山图和富集分析。

实现：[查看编号脚本](scripts/10_design.R)。

<!-- execute: design env=rnaseq -->
```r
# 目的：把规范样本/比较表转换为 Trinity DESeq2 设计文件。
# 关键输出：DE_DESIGN_DIR 中 samples.txt 和 contrasts.txt，默认 5DESeq2/design/。
#   两张均无表头：前者为组别/样本 ID，后者为实验组/参照组；不是正式 TSV 的替代编辑位置。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：写 samples.txt、contrasts.txt 与设计记录；不运行差异检验，不擅自添加批次/交互模型。
# 共用读取：readRenviron 读取 project.env；Sys.getenv 返回文本，as.numeric/as.integer 将阈值/种子转成数值。
#   更改配置后需重新执行读取与赋值，旧变量不会自动刷新。
# 本入口没有可调形参；先 source 加载当前定义，再调用函数即可。输入来自本节说明的项目文件，不需要寻找一个并不存在的参数赋值段。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/10_design.R")
run_design()
```

### 查看本步关键文件

这是给 Trinity 使用的无表头格式。修改设计应回到正式 samples.tsv/contrasts.tsv，不直接改这里来制造两套不同的分组。

```r
# 目的：只读当前参数路径的关键文本；留在上一框的 R 会话，不重新分析。
# 前提：上一分析已成功或明确提示完整结果复用；若报错/冲突，先处理，不把旧文件当本次成功结果。
# preview_dir/preview_files 只用于查看，不是传给分析函数的新参数。
# file.path 拼接路径；readLines(n = 10) 最多读前 10 行，含表头；不整表读入内存。
# file.exists 检查是否存在；cat 用 sep = "\n" 逐行显示；warn = FALSE 省略末行换行提示。
preview_dir <- project_result("DE_DESIGN_DIR", "5DESeq2/design")
preview_files <- file.path(preview_dir, c("samples.txt", "contrasts.txt"))
for (preview_file in preview_files) {
  cat("\n文件：", preview_file, "\n")
  if (file.exists(preview_file)) {
    cat(readLines(preview_file, n = 10, warn = FALSE), sep = "\n")
  } else {
    cat("尚无此文件：核对上一步是否完成、是否选择该分析，以及空结果提示。\n")
  }
}
```

## 2. 调用原流程指定的脚本

实现：[查看编号脚本](scripts/10_deseq2.sh)。

<!-- execute: deseq2 env=rnaseq -->
```bash
# 目的：使用指定 Trinity/DESeq2 路线按比较表拟合差异。
# 关键输出：5DESeq2/DE_analysis/reps{min_reps}_cpm{min_cpm}/：本次拟合结果目录。
#   里面每个比较的 *.DESeq2.DE_results 是原始统计表，并保存 R 脚本/对象及日志；下一步汇总成统一 TSV。
# 前提/去向：输入：COUNT_MATRIX 的未归一化 counts、设计 samples.txt/contrasts.txt；输出DE_analysis/repsN_cpmM。
#   已有目标目录会停止，不混用另一输入的模型。
# 先 source 加载同编号脚本定义，再设置下面变量并调用函数；加载本身不启动分析。所有路径相对能看见0script 的项目根目录。
# 可调参数（下面赋值是本次值，Shell 的 = 两侧不留空格）：
# min_reps：正整数；表达过滤要求至少多少个样本达到 min_cpm 条件，不是指定新的生物学重复数。与 min_cpm联合改变进入 DESeq2 的基因。
# min_cpm：非负 CPM 门槛（每百万计数）；至少 min_reps 个样本达到该过滤条件。改变后需要重新拟合，不只是调整最后一张图。
# 调用时 $变量 取上面设置的值；双引号保持每个值为一个参数，空字符串也占一个参数位置。调用顺序与脚本 $1、$2… 一致，不需深入函数体改值。
# 执行环境：rnaseq；命令退出不代表所有后续章节都已完成，查看本步结果/日志后再继续。

source 0script/scripts/10_deseq2.sh
min_reps=2
min_cpm=1
# interface-parameters: deseq2
run_deseq2 "$min_reps" "$min_cpm"
```

| 参数或步骤 | 解释 |
| --- | --- |
| `--matrix` | 未作 TMM/TPM 归一化的 estimated counts；原脚本进入 R 后四舍五入 |
| `--min_reps_min_cpm 2,1` | 保留至少两个样本 CPM > 1 的基因，显式写出原脚本默认值 |
| `--samples_file` | 无表头，两列为组别、样本 ID |
| `--contrasts` | 无表头，两列为实验组、参照组 |
| DESeq2 大小因子 | 用于计数模型，与上一章展示矩阵的 TMM 因子不同 |
| `padj` | 每个比较中对基因检验进行 BH 多重校正，不表示所有比较联合控制错误率 |

多个比较都可报告，但不能从中挑一个最小 P 值当作预先指定的唯一检验。配对实验或复杂批次设计需要显式调整模型，不能仅靠改分组名称获得正确设计。

## 3. 合并结果并生成统一字段

实现：[查看编号脚本](scripts/10_de_summary.R)。

<!-- execute: de_summary env=rnaseq -->
```r
# 目的：合并真实 DESeq2 结果并按门槛标记 up/down/ns。
# 关键输出：5DESeq2/padj阈值_lfc阈值[__标签]/，默认新输出为 5DESeq2/padj0.05_lfc1/。
#   内含 de_result.tsv、de_result.RData、DE_summary.tsv 和 DE_summary.png/.pdf；不重新拟合 DESeq2。
# 运行位置：项目根目录（能看见 0script）；在本章指定环境的 R 中执行。
# 输出/边界：保存 de_result.tsv/RData、DE_summary.tsv 与图，不可见返回 output_dir/analysis_dir；不重新拟合模型。
# 共用读取：readRenviron 读取 project.env；Sys.getenv 返回文本，as.numeric/as.integer 将阈值/种子转成数值。
#   更改配置后需重新执行读取与赋值，旧变量不会自动刷新。
# 参数设置（下方为本次取值；不需要修改函数内部实现）：
# fdr_cutoff：数值阈值，通常 0.05，范围 (0,1]；控制当前步骤的校正 P 值筛选，调小更严格。各比较/富集本体分别校正，不代表全项目共同做一次 BH。
# logfc_cutoff：非负数；绝对 log2FoldChange 门槛，1 对应两倍变化。调大要求更大效应量；在汇总/绘图中修改不会重新拟合 DESeq2。
# analysis_dir：字符路径；已有 DESeq2 原始统计文件所在目录。这里只读并汇总，不重新拟合模型，也不自动选取最新目录。
# variant_label：一个文本标签，默认 "" 表示不加额外后缀；如 "large_font" 会给末级结果目录加 __large_font。
#  非空时只用字母、数字、点、下划线、短横线，首字符为字母或数字；不填路径、空格或 NA。
#  调整未进入目录名的图幅、字体等时用不同标签另存；标签本身不改变计算参数。
#  它不是强制覆盖开关：同一路径参数冲突仍停止，不修改旧结果清单。
# 路径组合：file.path 按目录层级拼接；project_result 读取配置指定来源并核对存在，不查找最新目录。重绘来源与输出目录应分清。
# 调用：先加载脚本，再设置参数，最后运行函数。改值后重新执行赋值和调用。

source("0script/tools/metadata.R")
source("0script/tools/outputs.R")
readRenviron("0script/project.env")
source("0script/scripts/10_de_summary.R")
fdr_cutoff <- as.numeric(Sys.getenv("FDR_CUTOFF"))
logfc_cutoff <- as.numeric(Sys.getenv("LOG2FC_CUTOFF"))
analysis_dir <- project_result("DE_ANALYSIS_DIR", "5DESeq2/DE_analysis")
variant_label <- ""
# interface-parameters: de_summary
run_de_summary(
  fdr_cutoff = fdr_cutoff,
  logfc_cutoff = logfc_cutoff,
  analysis_dir = analysis_dir,
  variant_label = variant_label
)
```

### 查看本步关键文件

de_result 的 gene_id、contrast_id、log2FoldChange、pvalue、padj、direction 分别对应基因、比较、效应和检验/分类结果；DE_summary 汇总各比较数量。后续读取哪套表仍由 DE_RESULT_FILE 明确指定。

```r
# 目的：只读当前参数路径的关键文本；留在上一框的 R 会话，不重新分析。
# 前提：上一分析已成功或明确提示完整结果复用；若报错/冲突，先处理，不把旧文件当本次成功结果。
# preview_dir/preview_files 只用于查看，不是传给分析函数的新参数。
# file.path 拼接路径；readLines(n = 10) 最多读前 10 行，含表头；不整表读入内存。
# file.exists 检查是否存在；cat 用 sep = "\n" 逐行显示；warn = FALSE 省略末行换行提示。
# nzchar 判断标签是否非空；非空时按原命名规则在末级目录加 __标签。
preview_dir <- file.path("5DESeq2", parameter_tag(padj = fdr_cutoff, lfc = logfc_cutoff))
if (nzchar(variant_label)) preview_dir <- paste0(preview_dir, "__", variant_label)
preview_files <- file.path(preview_dir, c("de_result.tsv", "DE_summary.tsv"))
for (preview_file in preview_files) {
  cat("\n文件：", preview_file, "\n")
  if (file.exists(preview_file)) {
    cat(readLines(preview_file, n = 10, warn = FALSE), sep = "\n")
  } else {
    cat("尚无此文件：核对上一步是否完成、是否选择该分析，以及空结果提示。\n")
  }
}
```

`ns` 不能等同于“证明无差异”。需特别注意：当前 Trinity 脚本在导出时将 DESeq2 的缺失 `padj` 记为 1，原始 `pvalue` 的缺失仍保留。本项目保留这份软件导出结果并说明其含义，不把 `padj = 1` 一概解释为完成检验且无差异；后续以有限的 `pvalue` 判断可检验背景。不能把缺失 P 值改成显著值，也不能从这份导出表恢复所有独立过滤前的 `padj` 状态。

阈值默认 `padj <= 0.05` 且 `|log2FC| >= 1`。本次 11 个启用比较均已完成：

| 比较 | 上调 | 下调 |
| --- | --- | --- |
| ZT1 vs ZT0 | 1,017 | 607 |
| ZT4 vs ZT0 | 1,087 | 826 |
| ZT8 vs ZT0 | 1,647 | 1,268 |
| ZT12 vs ZT0 | 1,734 | 1,376 |
| ZT16 vs ZT0 | 1,392 | 1,117 |
| ZT20 vs ZT0 | 593 | 552 |
| ZT4 vs ZT1 | 853 | 877 |
| ZT8 vs ZT4 | 815 | 735 |
| ZT12 vs ZT8 | 466 | 497 |
| ZT16 vs ZT12 | 371 | 209 |
| ZT20 vs ZT16 | 390 | 695 |

![11 个比较的差异基因数量](../5DESeq2/DE_summary.png)

以上数值来自 `DE_summary.tsv`，不是预期值或旧版本截图。对首时期和相邻时期提出的问题不同，数量不能相互替代，也不能简单据此给某个时期的重要性排序。后续图形和富集均读取同一份 `de_result.tsv`。
