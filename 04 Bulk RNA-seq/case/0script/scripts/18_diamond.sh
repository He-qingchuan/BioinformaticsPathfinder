#!/usr/bin/env bash
# 文件用途｜运行 eggNOG-mapper 的 DIAMOND 搜索与功能转移。
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
# 输入：representative_proteins.fa 与共享 eggNOG 数据库；输出 OrgDb/diamond/output/annotation.emapper.
#   *。已有正式 annotations 拒绝覆盖，部分失败输出需人工核实。
# -i：查询蛋白；--itype proteins：声明序列类型；-m diamond：使用指定搜索方法；--data_dir：数据库目录；
#   --dmnd_db：DIAMOND 数据库文件。
# --tax_scope：注释供体范围；--excluded_taxa：可选排除供体；空字符串时整个选项不传，不把空值当目标物种。
# --seed_ortholog_evalue：种子阈值；--cpu：实际线程；--output_dir：结果目录；-o annotation：文件名前缀
#   ；--version 只核对软件版本。

# 接口｜run_diamond：运行 eggNOG-mapper 的 DIAMOND 搜索与功能转移。
# 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
# $1 annotation_tax_scope：字符分类范围；eggNOG 功能转移供体范围，本案例 33090 为绿色植物。换人/鼠等项
#   目必须核实，不代表目标物种 tax_id。
# $2 annotation_excluded_taxa：字符税号或空字符串；排除哪些注释供体。案例 3702 用于模拟不借用本物种注
#   释；普通项目可空，不默认沿用案例排除条件。
# $3 seed_evalue：正数 E 值阈值；控制种子直系同源命中筛选，值越小越严格。不是最终富集 P 值，改变需重做
#   相关注释。
# $4 max_annotation_threads：正整数；eggNOG 注释线程上限，实际取它与项目 THREADS 的较小者，只控制资源。
# 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
#   的表。
run_diamond() (
  set -euo pipefail
  [[ $# -eq 4 ]] || { echo "参数数量错误；请按第 18 章调用示例运行。" >&2; return 2; }
  annotation_tax_scope="${1}"
  annotation_excluded_taxa="${2}"
  [[ -n "$annotation_tax_scope" ]] || { echo '请先在第 18 章核实并填写 annotation_tax_scope。' >&2; return 2; }
  seed_evalue="${3}"
  max_annotation_threads="${4}"
  # 功能：用 DIAMOND 搜索代表蛋白并转移功能注释；不执行额外蛋白搜索路线。
  # seed_evalue 控制种子阈值，max_annotation_threads 控制资源，二者含义不同。
  set -euo pipefail
  set -a
  source 0script/project.env
  set +a
  workdir=$(pwd)
  org_dir="$workdir/9Enrichment_Analysis/OrgDb"
  # seed_evalue：DIAMOND 种子命中的 E 值阈值；改变后要重新进行相关注释。
  # max_annotation_threads：注释线程上限，还受项目 THREADS 限制；只控制资源。
  annotation_threads=$(( THREADS < max_annotation_threads ? THREADS : max_annotation_threads ))
  # 本物种税号与排除哪些注释供体是两项设计；普通项目可不排除供体。
  exclude_args=()
  [[ -z "$annotation_excluded_taxa" ]] || exclude_args=(--excluded_taxa "$annotation_excluded_taxa")
  : "${EGGNOG_DATA_DIR:?请配置公共数据库路径}"
  test ! -e "$org_dir/diamond/output/annotation.emapper.annotations"
  mkdir -p "$org_dir/diamond/output"
  emapper.py --data_dir "$EGGNOG_DATA_DIR" --version
  /usr/bin/time -v -o "$org_dir/diamond/output/resources.log" \
    emapper.py -i "$org_dir/representative_proteins.fa" --itype proteins \
      -m diamond --data_dir "$EGGNOG_DATA_DIR" \
      --dmnd_db "$EGGNOG_DATA_DIR/eggnog_proteins.dmnd" \
      --tax_scope "$annotation_tax_scope" "${exclude_args[@]}" \
      --seed_ortholog_evalue "$seed_evalue" --cpu "$annotation_threads" \
      --output_dir "$org_dir/diamond/output" -o annotation
  test -s "$org_dir/diamond/output/annotation.emapper.annotations"
)
