#!/usr/bin/env bash
# 文件用途｜把已完成的 Salmon 转录本定量按样本顺序合并。
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
# 输入：样本表和每样本 quant.sf；输出 3Salmon/raw_count.txt 与 tpm.txt，已有任一目标会停止。
# salmon quantmerge --quants：定量目录数组；--names：同序样本名数组；--column numreads/tpm：分别取估计
#   计数/TPM；--output：保存文件。两组数组不可换序。
# 本步是转录本层面合并；第 08 章再用明确转录本—基因映射生成基因层面的通用矩阵。

# 接口｜run_quantmerge：把已完成的 Salmon 转录本定量按样本顺序合并。
# 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
# 参数：不接收位置参数；输入路径、样本和适用线程从当前项目读取，不在调用行硬写样本名。
# 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
#   的表。
run_quantmerge() (
  set -euo pipefail
  [[ $# -eq 0 ]] || { echo "参数数量错误；请按第 07 章调用示例运行。" >&2; return 2; }

  # 功能：把各样本 quant.sf 合并为转录本 counts 和 TPM 矩阵。
  # 输入顺序由样本表决定；--column 分别选 numreads/tpm，不能混淆两种单位。
  set -euo pipefail
  workdir=$(pwd)
  quant_dirs=()
  sample_names=()
  sample_rows=$(Rscript 0script/tools/sample_columns.R sample_id)
  while IFS= read -r sample_id; do
    [[ $sample_id == sample_id ]] && continue
    test -s "$workdir/3Salmon/${sample_id}.quant/quant.sf"
    quant_dirs+=("$workdir/3Salmon/${sample_id}.quant")
    sample_names+=("$sample_id")
  done <<< "$sample_rows"
  [[ ${#quant_dirs[@]} -gt 0 ]]
  test ! -e 3Salmon/raw_count.txt
  test ! -e 3Salmon/tpm.txt
  salmon quantmerge --quants "${quant_dirs[@]}" --names "${sample_names[@]}" \
    --column numreads --output 3Salmon/raw_count.txt
  salmon quantmerge --quants "${quant_dirs[@]}" --names "${sample_names[@]}" \
    --column tpm --output 3Salmon/tpm.txt
)
