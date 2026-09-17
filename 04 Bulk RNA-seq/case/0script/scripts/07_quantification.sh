#!/usr/bin/env bash
# 文件用途｜对每个双端样本运行 Salmon 定量。
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
# 输入：现存 salmon_index 与 clean FASTQ；输出 3Salmon/{sample_id}.quant/quant.sf、aux_info 和日志。已
#   有 quant.sf 拒绝覆盖，不静默换一套索引。
# salmon quant -i：索引；-l：文库类型；-1/-2：双端输入；-p：每样本线程；-o：该样本结果目录。
# --gcBias/--seqBias：启用 GC/序列偏倚校正；--validateMappings：验证候选映射，保留本项目既定定量路线。
# xargs -r：无输入不启动；-P：并行样本数；-n 1：每次一个 sample_id。技术 ID 已按规范校验，子函数从导出
#   变量取同一组资源设置。

# 接口｜run_quantification：对每个双端样本运行 Salmon 定量。
# 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
# $1 sample_jobs：正整数；同时处理的样本数，超过 THREADS 时下调到线程预算。每样本线程为整除
#   THREADS/sample_jobs；样本数不等于线程数或重复数。
# $2 library_type：字符文库类型；A 自动推断，IU/ISF/ISR 等应按真实建库方向核实。与样本分组无关，不能由
#   物种或文件名推断。
# 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
#   的表。
run_quantification() (
  set -euo pipefail
  [[ $# -eq 2 ]] || { echo "参数数量错误；请按第 07 章调用示例运行。" >&2; return 2; }
  sample_jobs="${1}"
  library_type="${2}"
  # 功能：设置文库类型和并行预算，读取配对 clean FASTQ。
  # library_type=A 为自动判断；明确知道实验建库类型时可修改，不能只改样本名推断。
  set -euo pipefail
  set -a
  source 0script/project.env
  set +a
  workdir=$(pwd)
  cleandata="$workdir/2data/cleandata/fastp"
  index="$workdir/3Salmon/index/salmon_index"
  # sample_jobs：同时运行的样本数；与 THREADS 一起决定每个样本的线程，不是生物学重复数。
  # library_type：文库方向；A 自动推断。明确已知建库方向时核实 Salmon 支持的编码再修改。
  [[ $sample_jobs =~ ^[1-9][0-9]*$ && $THREADS =~ ^[1-9][0-9]*$ ]]
  (( sample_jobs > THREADS )) && sample_jobs=$THREADS
  threads_per_sample=$((THREADS / sample_jobs))

  # 功能：为一个样本调用 Salmon；保留 GC、序列偏倚校正和匹配验证。
  # $1 是样本表的 sample_id；library_type/threads_per_sample 来自入口并导出给子进程。
  # 接口｜quantify_one_sample：只定量一个样本，使用外层导出的索引、目录、文库类型和每样本线程。
  # 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
  # $1 id：样本表的单个 sample_id，以它定位 clean 文件及输出目录。
  # 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
  #   的表。
  quantify_one_sample() {
    local id=$1
    local outdir="$workdir/3Salmon/${id}.quant"
    test ! -e "$outdir/quant.sf"
    mkdir -p "$outdir"
    /usr/bin/time -v -o "$outdir/resources.log" \
      salmon quant -i "$index" -l "$library_type" \
        -1 "$cleandata/${id}_clean_1.fastq.gz" \
        -2 "$cleandata/${id}_clean_2.fastq.gz" \
        -p "$threads_per_sample" --gcBias --seqBias --validateMappings \
        -o "$outdir" > "$outdir/command.log" 2>&1
    test -s "$outdir/quant.sf"
  }
  export -f quantify_one_sample
  export workdir cleandata index threads_per_sample library_type

  # 功能：按样本表逐样本启动定量，子进程调用同一个函数，不另写一套参数。
  Rscript 0script/tools/sample_columns.R sample_id |
    xargs -r -P "$sample_jobs" -n 1 bash -c 'set -euo pipefail; quantify_one_sample "$@"' quantify_one_sample
)
