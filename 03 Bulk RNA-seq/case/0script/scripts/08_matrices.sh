#!/usr/bin/env bash
# 文件用途｜调用 Trinity 附带汇总工具生成基因 counts、TPM 与 TMM 表。
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
# 输入：gene_trans_map.tsv 与 quant_files.txt；输出 3Salmon/quanti 下 genes 前缀的原始汇总表，本命令不
#   运行转录本组装。
# --est_method salmon：解析 Salmon 格式；--gene_trans_map：无表头的基因/转录本映射；--quant_files：定
#   量文件清单。
# --name_sample_by_basedir：以父目录名作样本列名；--cross_sample_norm TMM：跨样本组成归一化；--
#   out_prefix：输出前缀。第 08 章下一段再规范列名。

# 接口｜run_matrices：调用 Trinity 附带汇总工具生成基因 counts、TPM 与 TMM 表。
# 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
# 参数：不接收位置参数；输入路径、样本和适用线程从当前项目读取，不在调用行硬写样本名。
# 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
#   的表。
run_matrices() (
  set -euo pipefail
  [[ $# -eq 0 ]] || { echo "参数数量错误；请按第 08 章调用示例运行。" >&2; return 2; }

  # 功能：调用原指定 Trinity 工具汇总基因 counts、TPM 和 TMM 表达矩阵。
  # 参数：est_method=salmon 对应实际输入格式；TMM 为组成归一化，不是重跑转录本组装。
  set -euo pipefail
  mkdir -p 3Salmon/quanti
  abundance_estimates_to_matrix.pl \
    --est_method salmon \
    --gene_trans_map 3Salmon/quanti/gene_trans_map.tsv \
    --name_sample_by_basedir \
    --quant_files 3Salmon/quanti/quant_files.txt \
    --cross_sample_norm TMM \
    --out_prefix 3Salmon/quanti/genes
)
