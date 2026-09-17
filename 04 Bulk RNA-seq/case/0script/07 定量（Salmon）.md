# 07 定量：Salmon

<!-- normalized-inputs -->
输入字段和项目迁移规则见[输入规范](<附4 输入文件规范与项目迁移.md>)。代码从能看到 `0script` 的项目根目录运行。

Salmon 估计每条转录本的丰度，不是把某个基因上的全部序列简单相加。相似转录本会竞争 reads，软件结合片段长度和偏倚模型分配计数。本章保持原稿的 decoy-aware 索引、GC 与序列偏倚校正。

## 本章从哪里读取参数

以下值来自 [project.env](project.env)，不是写死在函数里的常量。案例值与新项目模板值分别列出；实际运行读取你当前文件中的设置。图形特有参数仍在本章入口集中设置。修改后需重新运行读取/赋值段，再调用函数；已经在内存中的旧变量不会随文件编辑自动刷新。

| 参数 | 当前案例配置 | 空模板默认 | 用途与修改注意 |
| --- | --- | --- | --- |
| `THREADS` | `24` | `24` | 上游和注释的总线程预算，正整数；默认 24。 按服务器实际分配资源调小或调大，不超过可用 CPU/内存；样本并行数还由各章 sample_jobs 分配。 |

## 1. 构建含基因组诱饵的索引

转录本 FASTA 放在前面，基因组放在后面；`decoys.txt` 列出基因组序列名。诱饵帮助识别更像基因组其他区域的 reads，减少其误分配到转录本。建立本项目时已重新建索引；下面保留从头执行的代码，当前文档修订不重建现有索引。

实现：[查看编号脚本](scripts/07_index.sh)。

<!-- execute: index env=rnaseq -->
```bash
# 目的：用转录本和基因组诱饵构建 Salmon 索引。
# 关键输出：3Salmon/index/gentrome.fa：转录本加基因组；decoys.txt：基因组诱饵 ID。
#   3Salmon/index/salmon_index/：Salmon 索引目录，不能用 head 当普通表格查看。
# 前提/去向：输入：统一名的 transcripts.fa.gz/genome.fa.gz；输出 gentrome.fa、decoys.txt、salmon_index。
#   已有合并参考或索引时拒绝覆盖。
# 先 source 加载同编号脚本定义，再设置下面变量并调用函数；加载本身不启动分析。所有路径相对能看见0script 的项目根目录。
# 可调参数（下面赋值是本次值，Shell 的 = 两侧不留空格）：
# kmer_length：正奇数，当前 CLI 允许 15–31；Salmon 索引的 k-mer 长度，应不长于适用 reads。改变它需新建索引及重新定量，不能只换名字复用旧索引。
# 调用时 $变量 取上面设置的值；双引号保持每个值为一个参数，空字符串也占一个参数位置。调用顺序与脚本 $1、$2… 一致，不需深入函数体改值。
# 执行环境：rnaseq；命令退出不代表所有后续章节都已完成，查看本步结果/日志后再继续。

source 0script/scripts/07_index.sh
kmer_length=31
# interface-parameters: index
run_index "$kmer_length"
```

### 查看本步关键文件

每行一个基因组序列 ID，无表头；这些 ID 是诱饵，不是差异基因，也不是转录本名单。

```bash
# 目的：查看本步文本结果的前 10 行；在项目根目录的 Bash 终端运行，只读不写。
# 前提：上一步已成功完成；报错后即使同名文件存在，也不能据此认定本次成功。
# head -n 10 含表头最多读 10 行；test -f 检查文件；printf 先显示路径，避免混淆。
preview_file="3Salmon/index/decoys.txt"
if test -f "$preview_file"; then
  printf "\n文件：%s\n" "$preview_file"
  head -n 10 "$preview_file"
else
  printf "尚无此文件：%s；先检查上一步是否完成。\n" "$preview_file"
fi
```

`-k 31` 是索引 k-mer 长度，不是要求把 reads 裁为 31 nt。更短 reads 的可用性需要重新评估。Salmon 默认可去除序列完全相同的冗余转录本，实际定量数可能少于输入 FASTA。另一个独立差别是 GTF 含有未放入 cDNA FASTA 的 ncRNA；第 08 章分别记录，不混称为定量漏失。

## 2. 批量进行双端定量


`library_type` 的双端可选值如下。`U` 表示不区分转录链，`SF/SR` 表示链特异且 R1 分别与转录本同向/反向；前面的 I/O/M 描述一对 reads 的相对方向，不是处理组方向。

| 值 | 配对方向 | 链信息与用途 |
| --- | --- | --- |
| `A` | 由 Salmon 推断 | 不预先固定类型；须核对输出的推断结果与建库记录 |
| `IU` / `ISF` / `ISR` | 相向（inward） | 依次为非链特异 / R1 同向 / R1 反向；三者不可互换 |
| `OU` / `OSF` / `OSR` | 背向（outward） | 依次为非链特异 / R1 同向 / R1 反向；仅适用于真实背向文库 |
| `MU` / `MSF` / `MSR` | 同向（matching） | 依次为非链特异 / R1 同向 / R1 反向；仅适用于真实同向文库 |

本章是双端接口，单端代码 `U/SF/SR` 不适用于这里。编码定义见 [Salmon 官方文库类型说明](https://salmon.readthedocs.io/en/latest/library_type.html)。不要为提高映射率随意挑选类型。

实现：[查看编号脚本](scripts/07_quantification.sh)。

<!-- execute: quantification env=rnaseq -->
```bash
# 目的：对每个双端样本运行 Salmon 定量。
# 关键输出：3Salmon/{sample_id}.quant/quant.sf：该文库的转录本丰度。
#   同目录 aux_info/meta_info.json 是定量诊断；command.log 和 resources.log 是日志。
# 前提/去向：输入：现存 salmon_index 与 clean FASTQ；输出 3Salmon/{sample_id}.quant/quant.sf、aux_info和日志。
#   已有 quant.sf 拒绝覆盖，不静默换一套索引。
# 先 source 加载同编号脚本定义，再设置下面变量并调用函数；加载本身不启动分析。所有路径相对能看见0script 的项目根目录。
# 可调参数（下面赋值是本次值，Shell 的 = 两侧不留空格）：
# sample_jobs：正整数；同时处理的样本数，超过 THREADS 时下调到线程预算。每样本线程为整除THREADS/sample_jobs；样本数不等于线程数或重复数。
# library_type：单个文库类型字符串，默认 "A" 自动推断；全部双端选项及含义见下表。
#   手动指定必须依据建库方向，不由样本分组、物种或文件名推断；换值需要重新定量。
# 调用时 $变量 取上面设置的值；双引号保持每个值为一个参数，空字符串也占一个参数位置。调用顺序与脚本 $1、$2… 一致，不需深入函数体改值。
# 执行环境：rnaseq；命令退出不代表所有后续章节都已完成，查看本步结果/日志后再继续。

source 0script/scripts/07_quantification.sh
sample_jobs=2
library_type=A
# interface-parameters: quantification
run_quantification "$sample_jobs" "$library_type"
```

### 查看本步关键文件

本框在 rnaseq 的 R 中运行，按样本表第一行选一个文库。`Name` 为转录本 ID，`Length/EffectiveLength` 为长度/有效长度，`TPM` 为相对丰度，`NumReads` 为估计片段计数（可有小数）。

```r
# 目的：从 Bash 切换到 rnaseq 的 R 后，只读本步关键文本结果，不重新分析。
# preview_dir/preview_files 只用于查看，不是传给分析函数的新参数。
# file.path 拼接路径；readLines(n = 10) 最多读前 10 行，含表头；不整表读入内存。
# file.exists 检查是否存在；cat 用 sep = "\n" 逐行显示；warn = FALSE 省略末行换行提示。
source("0script/tools/metadata.R")
readRenviron("0script/project.env")
preview_id <- read_samples()$sample_id[1]
preview_dir <- file.path("3Salmon", paste0(preview_id, ".quant"))
preview_files <- file.path(preview_dir, c("quant.sf"))
for (preview_file in preview_files) {
  cat("\n文件：", preview_file, "\n")
  if (file.exists(preview_file)) {
    cat(readLines(preview_file, n = 10, warn = FALSE), sep = "\n")
  } else {
    cat("尚无此文件：核对上一步是否完成、是否选择该分析，以及空结果提示。\n")
  }
}
```

| 参数 | 解释 |
| --- | --- |
| `-i` | 上一步建立的索引目录 |
| `-l A` | 自动判断文库方向；结果中记录实际推断类型，必要时与建库记录核对 |
| `-1/-2` | 配对 clean FASTQ |
| `-p` | 单样本线程；同时样本数乘单样本线程受总预算限制 |
| `--validateMappings` | 验证候选序列匹配位置 |
| `--gcBias` | 估计并校正片段 GC 相关偏倚 |
| `--seqBias` | 估计并校正序列相关偏倚；不等同于修复实验批次 |
| `-o` | 该样本独立输出目录 |

本次只整理参数入口，沿用已有索引和定量结果；不再次执行上述耗时命令。若以后改变参考序列、索引 k-mer、文库类型或校正选项，需要重新计算受影响的定量，不能仅修改绘图参数。

## 3. 合并转录本计数和 TPM

实现：[查看编号脚本](scripts/07_quantmerge.sh)。

<!-- execute: quantmerge env=rnaseq -->
```bash
# 目的：把已完成的 Salmon 转录本定量按样本顺序合并。
# 关键输出：3Salmon/raw_count.txt：转录本估计计数；3Salmon/tpm.txt：转录本 TPM。
#   这两张是转录本层面的矩阵，下一章另行生成基因层面的矩阵。
# 前提/去向：输入：样本表和每样本 quant.sf；输出 3Salmon/raw_count.txt 与 tpm.txt，已有任一目标会停止。
# 先 source 加载同编号脚本定义，再设置下面变量并调用函数；加载本身不启动分析。所有路径相对能看见0script 的项目根目录。
# 本入口无位置参数；样本名/分组从 samples.tsv 获取，线程等共用设置从 project.env 获取，不必逐样本改代码。
# 执行环境：rnaseq；命令退出不代表所有后续章节都已完成，查看本步结果/日志后再继续。

source 0script/scripts/07_quantmerge.sh
run_quantmerge
```

### 查看本步关键文件

第一列为转录本，其余为按样本表组织的文库列。两张表尺度不同，不能相互改名替代。

```bash
# 目的：查看本步文本结果的前 10 行；在项目根目录的 Bash 终端运行，只读不写。
# 前提：上一步已成功完成；报错后即使同名文件存在，也不能据此认定本次成功。
# head -n 10 含表头最多读 10 行；test -f 检查文件；printf 先显示路径，避免混淆。
for preview_file in "3Salmon/raw_count.txt" \
  "3Salmon/tpm.txt"; do
  if test -f "$preview_file"; then
    printf "\n文件：%s\n" "$preview_file"
    head -n 10 "$preview_file"
  else
    printf "尚无此文件：%s；先检查上一步是否完成。\n" "$preview_file"
  fi
done
```

保留原稿的 `quantmerge` 结果，便于观察转录本层面的矩阵；下一章另外用 Trinity 按基因汇总。样本顺序来自表格，不靠 `ls` 的字典排序。

`quant.sf` 的列为 `Name`（转录本 ID）、`Length`、`EffectiveLength`（模型中的有效长度）、`TPM` 和 `NumReads`。`NumReads` 是分配到转录本的估计片段计数，可以是小数。`aux_info/meta_info.json` 保存处理片段数、定量映射率等诊断信息；不能只凭映射率高就认定生物学结果正确。

## 4. 本次完成情况

21 个文库均完成本次定量，处理片段数与对应 fastp 保留 reads 数除以 2 逐一吻合；定量映射率为 **74.46%–78.66%**。所有文库自动推断为 `ISR`：双端相向、链特异、R1 来自反向链，编码含义见 [Salmon 官方说明](https://salmon.readthedocs.io/en/latest/library_type.html)。仍应与实际建库记录核对，不能只依赖自动判断。

映射率不是差异表达的显著性，也不能单独判定文库优劣。参考覆盖范围、重复序列、样本与参考差异及无法分配的片段都会影响它；本项目不把未映射部分直接归因为某一种原因。逐文库诊断见 `3Salmon/quanti/mapping_summary.tsv`。
