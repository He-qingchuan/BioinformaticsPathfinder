#!/usr/bin/env bash
# 文件用途｜在有明确蛋白对应的转录本中选最长成熟转录本并保留基因身份。
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
# 输入：GTF、蛋白 FASTA 和可选身份表；先由 protein_identity.py 核实关系，再输出代表映射、派生 GTF 和
#   representative_proteins.fa，原参考不改。
# python --output：身份核对空目录；可选 --mapping：人工对应表。ulimit -c 0 关闭本子进程的 core dump，
#   不调整系统后台配置。
# cp -n：不覆盖已有副本；gzip -cd：解压到管道不删除压缩源。awk FS/OFS 设制表符，按
#   gene_id/transcript_id 提取字段，不依赖属性排列。
# gtftk select_by_key -i/-o：输入/输出 GTF；-k：要筛选的键；-f：允许 ID 文件；-v：指定值。
#   convert_ensembl 恢复筛选后需要的 gene 层记录。
# short_long -l：每基因选择最长成熟转录本（外显子长度之和），不是最长蛋白；tabulate -k：输出指定键列。
# tail -n +2：跳过表头；cut -f1：取第一列转录本 ID；seqtk subseq：按名单提取蛋白。最后 awk 改 FASTA 查
#   询名为 gene_id，原对应表另存可追溯。

# 接口｜run_representatives：在有明确蛋白对应的转录本中选最长成熟转录本并保留基因身份。
# 位置参数按以下顺序传入；Bash 没有 R 那样的具名形参调用，不能调换顺序。
# $1 protein_mapping_file：字符路径或空字符串；GTF/蛋白 ID 可明确对应时留空，否则提供人工核实的
#   protein_id/transcript_id/gene_id 表，不能猜 ID 相等。
# 返回/写出：成功返回退出状态 0，检查或软件失败为非零。实际结果保存在上述目录；本接口不返回一张内存中
#   的表。
run_representatives() (
  set -euo pipefail
  [[ $# -eq 1 ]] || { echo "参数数量错误；请按第 18 章调用示例运行。" >&2; return 2; }
  protein_mapping_file="${1}"
  # 功能：从有对应蛋白的转录本中选最长成熟转录本，再以基因 ID 命名代表蛋白。
  # short_long -l 按外显子长度选择，不是按蛋白长度；派生 GTF 不覆盖原参考。
  set -euo pipefail
  org_dir=9Enrichment_Analysis/OrgDb
  set -a
  source 0script/project.env
  set +a
  # 先核对身份；Ensembl 人/鼠蛋白 ID 通常不同于转录本 ID，不能直接当作同一个 ID。
  mapping_args=()
  [[ -z "$protein_mapping_file" ]] || mapping_args=(--mapping "$protein_mapping_file")
  python 0script/tools/protein_identity.py --output "$org_dir/protein_identity" "${mapping_args[@]}"
  mkdir -p "$org_dir/representatives"
  ulimit -c 0
  cp -n "$org_dir/protein_identity/protein_transcript_ids.txt" "$org_dir/representatives/protein_transcript_ids.txt"
  gzip -cd 1database/genome/annotation.gtf.gz |
    awk 'BEGIN {FS=OFS="\t"} /^#/ {next}
         {attrs="";
          if (match($9, /gene_id "[^"]+"/)) attrs=substr($9,RSTART,RLENGTH) ";";
          if (match($9, /transcript_id "[^"]+"/)) attrs=attrs " " substr($9,RSTART,RLENGTH) ";";
          if (attrs=="") {print "GTF 记录缺少基因/转录本 ID" > "/dev/stderr"; exit 1}
          $9=attrs; print}' > "$org_dir/representatives/identifiers_only.gtf"
  gtftk select_by_key -i "$org_dir/representatives/identifiers_only.gtf" \
    -k transcript_id -f "$org_dir/representatives/protein_transcript_ids.txt" \
    -o "$org_dir/representatives/protein_linked.gtf"
  # transcript_id 筛选不包含 gene 层记录，恢复必要层级后再运行 short_long。
  gtftk convert_ensembl -i "$org_dir/representatives/protein_linked.gtf" \
    -o "$org_dir/representatives/protein_linked_with_genes.gtf"
  gtftk short_long -l -i "$org_dir/representatives/protein_linked_with_genes.gtf" \
    -o "$org_dir/representatives/longest_transcripts.gtf"
  gtftk select_by_key -i "$org_dir/representatives/longest_transcripts.gtf" -k feature -v transcript |
    gtftk tabulate -k transcript_id,gene_id > "$org_dir/representatives/longest_mapid.tsv"
  tail -n +2 "$org_dir/representatives/longest_mapid.tsv" | cut -f1 \
    > "$org_dir/representatives/longest_transcript_ids.txt"
  seqtk subseq "$org_dir/protein_identity/proteins_by_transcript.fa" "$org_dir/representatives/longest_transcript_ids.txt" \
    > "$org_dir/representatives/longest_transcript.proteins.fa"

  # 用 gene_id 作为 eggNOG 的查询名，映射仍另存，便于回到原始转录本。
  awk -F '\t' 'NR == FNR {if (FNR > 1) id[$1]=$2; next}
    /^>/ {split(substr($0, 2), fields, /[[:space:]]+/);
          if (!(fields[1] in id)) {print "蛋白缺少基因映射" > "/dev/stderr"; exit 1}
          print ">" id[fields[1]]; next}
    {print}' "$org_dir/representatives/longest_mapid.tsv" \
    "$org_dir/representatives/longest_transcript.proteins.fa" > "$org_dir/representative_proteins.fa"
)
