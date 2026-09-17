#!/usr/bin/env python3
# 调用：第 18 章代表选择脚本调用，或 python 0script/tools/protein_identity.py --output 新目录。
# --gtf：GTF 路径，默认 1database/genome/annotation.gtf.gz；--proteins：蛋白 FASTA，默认同目录
#   proteins.fa.gz。
# --mapping：可选三列身份表，缺省优先使用 GTF/FASTA 明确关系；--output：必填的空目标目录，不能覆盖已有
#   非空目录。
# 输入文件只读。输出包含原 protein_id，不能因输出 FASTA 改用 transcript_id 就丢掉原身份对应。

"""从明确的 GTF/FASTA 标头对应关系建立蛋白—转录本映射，不按点号猜异构体。

用法：python 0script/tools/protein_identity.py --output 9Enrichment_Analysis/OrgDb/protein_identity
也可 --mapping 提供三列 protein_id,transcript_id,gene_id 的 TSV。全部核对后才写结果。
"""
import argparse
import csv
import gzip
from pathlib import Path
import re

# 接口｜opener：按扩展名打开普通或 gzip 文本文件。
# 参数：
# path（必填，无默认值）：字符串或 Path；.gz 使用 gzip 文本模式，否则普通 open。
# 返回/写出与边界：返回文件连接，由调用者 with 关闭；只读，不自动改名或解压到磁盘。
def opener(path):
    return gzip.open(path, "rt") if str(path).endswith(".gz") else open(path)

# 接口｜fasta：逐条迭代 FASTA 标题和序列。
# 参数：
# path（必填，无默认值）：普通或 gzip FASTA 路径，按 opener 打开。
# 返回/写出与边界：生成 (header, sequence) 字符串元组；header 不含 >，跨行序列连接起来。身份/空序列检
#   查由 build_links 完成。
def fasta(path):
    header, sequence = None, []
    with opener(path) as handle:
        for line in handle:
            if line.startswith(">"):
                if header is not None: yield header, "".join(sequence)
                header, sequence = line[1:].strip(), []
            elif line.strip(): sequence.append(line.strip())
    if header is not None: yield header, "".join(sequence)

# 接口｜build_links：结合明确来源建立蛋白—转录本—基因身份关系。
# 参数：
# gtf（必填，无默认值）：普通或 gzip GTF 路径；属性提供 gene_id/transcript_id 和可选版本、protein_id。
# proteins（必填，无默认值）：普通或 gzip 蛋白 FASTA 路径；需要明确可核对的标题 ID。
# mapping（默认 None）：人工核实三列 TSV 路径或 None；列 protein_id/transcript_id/gene_id，若提供必须
#   覆盖实际蛋白且与 GTF 一致。
# 返回/写出与边界：返回三列行字典列表；空序列、冲突、多个蛋白对应同一转录本或缺失唯一证据时报错，不用
#   盲目去点号修复。只读所有输入。
def build_links(gtf, proteins, mapping=None):
    tx_gene, tx_alias, protein_tx = {}, {}, {}
    # 接口｜put：向一个身份对应字典加入唯一映射。
    # 参数：
    # table（必填，无默认值）：待更新的字典，如 tx_gene、tx_alias 或 protein_tx。
    # key（必填，无默认值）：字符原始 ID/明确版本别名。
    # value（必填，无默认值）：字符目标 ID；应为已核实的基因或转录本。
    # 返回/写出与边界：原地更新传入 table；同键不同值时报错，相同值允许，不从冲突候选里随意择一。
    def put(table, key, value):
        if key in table and table[key] != value: raise ValueError(f"ID 对应不唯一：{key}")
        table[key] = value
    with opener(gtf) as handle:
        for line in handle:
            if line.startswith("#"): continue
            fields = line.rstrip().split("\t")
            if len(fields) != 9: raise ValueError("GTF 必须是九列")
            attributes = dict(re.findall(r'(?:^|;\s*)(\w+)\s+"([^"]*)"', fields[8]))
            tx, gene = attributes.get("transcript_id"), attributes.get("gene_id")
            if not tx or not gene: continue
            put(tx_gene, tx, gene); put(tx_alias, tx, tx)
            if attributes.get("transcript_version"):
                put(tx_alias, tx + "." + attributes["transcript_version"], tx)
            pid = attributes.get("protein_id")
            if pid:
                put(protein_tx, pid, tx)
                if attributes.get("protein_version"):
                    put(protein_tx, pid + "." + attributes["protein_version"], tx)
    supplied = {}
    if mapping:
        with open(mapping, encoding="utf-8-sig", newline="") as handle:
            rows = csv.DictReader(handle, delimiter="\t")
            if not {"protein_id", "transcript_id", "gene_id"} <= set(rows.fieldnames or []):
                raise ValueError("映射表需要 protein_id/transcript_id/gene_id")
            for row in rows:
                if row["protein_id"] in supplied: raise ValueError("映射表蛋白 ID 重复")
                if tx_gene.get(row["transcript_id"]) != row["gene_id"]: raise ValueError("提供映射与 GTF 冲突")
                supplied[row["protein_id"]] = row["transcript_id"]
    result, seen_protein, seen_tx = [], set(), set()
    for header, sequence in fasta(proteins):
        pid = header.split()[0]
        if not sequence or pid in seen_protein: raise ValueError(f"蛋白序列为空或 ID 重复：{pid}")
        seen_protein.add(pid)
        explicit = re.search(r'(?:^|\s)transcript:([^\s]+)', header)
        # 只合并人工映射、GTF protein_id、FASTA transcript 标头和确实相同的转录本 ID 四类明确证据；多种证据必
        #   须指向同一转录本。
        candidates = {x for x in (supplied.get(pid), protein_tx.get(pid),
            tx_alias.get(explicit[1]) if explicit else None,
            pid if pid in tx_gene else None) if x is not None}
        if len(candidates) != 1:
            raise ValueError(f"蛋白 {pid} 无唯一可核实的转录本；请提供明确映射，不可盲目删版本号")
        tx = candidates.pop()
        if tx in seen_tx: raise ValueError(f"多个蛋白对应同一转录本：{tx}，请核对来源")
        seen_tx.add(tx)
        result.append(dict(protein_id=pid, transcript_id=tx, gene_id=tx_gene[tx]))
    if not result: raise ValueError("没有可映射蛋白")
    if supplied and set(supplied) != seen_protein: raise ValueError("映射表与蛋白集合不一致")
    return result

# 接口｜main：校验蛋白身份后写出明确对应关系。
# 参数：无函数形参，命令行选项见文件头。
# 返回/写出与边界：从命令行读取参数；全部映射通过后才创建输出目录，已有非空目录拒绝覆盖；写映射 TSV、
#   转录本 ID 列表和按转录本命名的蛋白 FASTA。
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gtf", default="1database/genome/annotation.gtf.gz")
    parser.add_argument("--proteins", default="1database/genome/proteins.fa.gz")
    parser.add_argument("--mapping")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    links = build_links(args.gtf, args.proteins, args.mapping)
    out = args.output
    if out.exists() and any(out.iterdir()): raise ValueError("蛋白身份输出目录已存在，拒绝覆盖")
    # 先完成全部身份验证再写输出；目录若非空已经在上一行拒绝。原蛋白 ID 另存表，不因 FASTA 改名而丢掉追溯
    #   关系。
    out.mkdir(parents=True, exist_ok=True)
    with (out / "protein_transcript_gene.tsv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=["protein_id", "transcript_id", "gene_id"], delimiter="\t")
        writer.writeheader(); writer.writerows(links)
    (out / "protein_transcript_ids.txt").write_text("".join(r["transcript_id"] + "\n" for r in links))
    by_id = {r["protein_id"]: r["transcript_id"] for r in links}
    with (out / "proteins_by_transcript.fa").open("w") as handle:
        for header, sequence in fasta(args.proteins):
            handle.write(">" + by_id[header.split()[0]] + "\n" + sequence + "\n")
    print(f"已核实 {len(links)} 个蛋白的明确对应关系：{out}")

if __name__ == "__main__": main()
