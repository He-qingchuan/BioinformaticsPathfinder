#!/usr/bin/env bash
# 文件用途｜用转录本和基因组诱饵构建 Salmon 索引。
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
# 输入：统一名的 transcripts.fa.gz/genome.fa.gz；输出 gentrome.fa、decoys.txt、salmon_index。已有合并
#   参考或索引时拒绝覆盖。
# gzip -c 写标准输出、-d 解压且保留原 gzip；先转录本后基因组拼接，awk 只提取 DNA FASTA 标题的第一个字
#   段作为 decoy ID。
# salmon index -t：合并参考；-d：诱饵 ID 列表；-p：THREADS；-i：索引保存目录；-k：k-mer 长度。

# 接口｜run_index：用转录本和基因组诱饵构建 Salmon 索引。
# 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
# $1 kmer_length：正奇数，当前 CLI 允许 15–31；Salmon 索引的 k-mer 长度，应不长于适用 reads。改变它需
#   新建索引及重新定量，不能只换名字复用旧索引。
# 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
#   的表。
run_index() (
  set -euo pipefail
  [[ $# -eq 1 ]] || { echo "参数数量错误；请按第 07 章调用示例运行。" >&2; return 2; }
  kmer_length="${1}"
  # 功能：构建包含转录本和基因组诱饵的 Salmon 索引。
  # 参数：kmer_length 是索引 k-mer 长度，改它需要重新建索引和定量。
  set -euo pipefail
  # kmer_length：索引 k-mer 长度；31 为本例值，改动后需要重新建索引和定量。
  set -a
  source 0script/project.env
  set +a
  workdir=$(pwd)
  genome_dir="$workdir/1database/genome"
  index_dir="$workdir/3Salmon/index"
  if [[ -e "$index_dir/gentrome.fa" || -e "$index_dir/salmon_index" ]]; then
    echo "已有索引或合并参考，拒绝覆盖；复用已有结果时跳过本段。" >&2
    exit 1
  fi
  mkdir -p "$index_dir"
  gzip -cd "$genome_dir/genome.fa.gz" |
    awk '/^>/ {sub(/^>/, "", $1); print $1}' > "$index_dir/decoys.txt"
  # gzip 按给定顺序解压两个输入文件，保留“转录本在前、基因组在后”的次序。
  gzip -cd "$genome_dir/transcripts.fa.gz" "$genome_dir/genome.fa.gz" > "$index_dir/gentrome.fa"
  /usr/bin/time -v -o "$index_dir/resources.log" \
    salmon index -t "$index_dir/gentrome.fa" -d "$index_dir/decoys.txt" \
      -p "$THREADS" -i "$index_dir/salmon_index" -k "$kmer_length"
)
