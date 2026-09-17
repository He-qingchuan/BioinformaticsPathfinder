#!/usr/bin/env bash
# 文件用途｜对样本表中的每端原始 FASTQ 做 FastQC 并用 MultiQC 汇总。
# 运行方式：在项目根目录激活相应环境，先 source 本文件，再按同编号 MD 的顺序传入位置参数。source 本身
#   仅定义函数，不启动分析。
# 括号函数体在子 Shell 中运行；set -e 对未处理失败停止、-u 拒绝未定义变量、-o pipefail 使管道前段失败
#   可见。它不是自动恢复机制。
# set -a / source project.env / set +a（若本段使用）：临时把配置导出给子进程；不是创建 Conda 环境。双
#   引号保留文件名边界，$() 读取命令输出。
# mkdir -p：父目录不存在时一起创建，已有目录不清空；test -s/-e：检查非空文件/路径存在，! 取反。失败返
#   回非零，不自动下载缺失文件。
# 管道 | 传标准输出，> 写日志/文件时会覆盖同名目标，2>&1 把错误并入同一日志；/usr/bin/time -v -o 记录
#   资源详情（若本段调用）。不要把所有步骤都当作自动防覆盖。
# 本文件接口与输入输出：
# 输入：samples.tsv 的 sample_id/read1/read2，文件位于 2data/rawdata；输出 qc/*.html/*.zip 与
#   multiqc/raw_multiqc.html。
# fastqc --threads：可同时处理的文件预算；--outdir：报告目录，最后的数组逐项传完整文件路径。
# multiqc 输入目录：扫描 FastQC 结果；--outdir/--filename：汇总保存位置/名称；--force 会更新同名汇总
#   HTML，不是 FASTQ 覆盖开关。

# 接口｜run_raw_qc：对样本表中的每端原始 FASTQ 做 FastQC 并用 MultiQC 汇总。
# 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
# 参数：不接收位置参数；输入路径、样本和适用线程从当前项目读取，不在调用行硬写样本名。
# 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
#   的表。
run_raw_qc() (
  set -euo pipefail
  [[ $# -eq 0 ]] || { echo "参数数量错误；请按第 05 章调用示例运行。" >&2; return 2; }

  # 功能：从样本表取得所有双端文件，分别执行 FastQC，再由 MultiQC 汇总。
  # 参数：THREADS 来自 project.env；每个 mate 独立质控，原始 FASTQ 不改动。
  set -euo pipefail
  set -a
  source 0script/project.env
  set +a
  workdir=$(pwd)
  rawdata="$workdir/2data/rawdata"
  mkdir -p "$rawdata/qc" "$rawdata/multiqc"
  raw_files=()
  # 先完成表格校验再循环；这里不用管道启动 while，避免数组在子 Shell 丢失。
  sample_rows=$(Rscript 0script/tools/sample_columns.R sample_id read1 read2)
  while IFS=$'\t' read -r sample_id read1 read2; do
    [[ $sample_id == sample_id ]] && continue
    test -s "$rawdata/$read1"
    test -s "$rawdata/$read2"
    raw_files+=("$rawdata/$read1" "$rawdata/$read2")
  done <<< "$sample_rows"
  [[ ${#raw_files[@]} -gt 0 ]]

  # -t 同时处理的文件数；每个 FASTQ 独立生成 HTML 和 ZIP 报告。
  /usr/bin/time -v -o "$rawdata/qc/resources.log" \
    fastqc --threads "$THREADS" --outdir "$rawdata/qc" "${raw_files[@]}"

  # 使用原始 ZIP 作为 MultiQC 输入，不依赖手工打开 HTML 后导出的内容。
  multiqc "$rawdata/qc" --outdir "$rawdata/multiqc" --filename raw_multiqc.html --force
)
