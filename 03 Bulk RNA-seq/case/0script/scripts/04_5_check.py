#!/usr/bin/env python3
# 调用：激活 rnaseq 后，在项目根目录运行 python 0script/scripts/04_5_check.py。
# --project：项目根目录，省略使用当前目录；不是结果根目录。
# --chapters：逗号分隔的整数，如 9,10,12；省略时 fastq 检查 05–15，matrix 检查 09–15。时间/非模式支线
#   需明确选中。
# --force-full：忽略缓存重新全量验证；--no-software：跳过软件启动清单检查，报告标 PARTIAL，但材料表格
#   校验仍调用 rnaseq 的 Rscript，不是无 R 环境模式。
# --protein-mapping：第 18 章可选的人工蛋白对应表路径，普通主线不用。
# 输入：project.env、samples.tsv 及本次所选范围的参考/矩阵/结果。输出：0script/runlogs/04.5_preflight_
#   时间戳.md/json 与完整性缓存。
# 首次验证大型 gzip 要读遍文件；FASTQ 配对仅抽查前 1000 条。PASS 只针对所选检查范围，不证明实验设计或
#   数据尺度正确。

"""04.5 准备检查：只读输入；仅在 runlogs 中保存检查报告和完整性缓存。

从项目根目录运行：python 0script/scripts/04_5_check.py
--chapters 9,10,12：限定检查范围，不执行这些章节。
--force-full：忽略完整性缓存；--no-software：仅材料诊断，不可报告为全部就绪。
首次完整压缩检查会读遍文件，不下载、不重命名、不自动修复。
"""
# dependency: 0script/scripts/04_5_tables.R
# dependency: 0script/tools/protein_identity.py
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

CACHE_VERSION = 2

# 接口｜read_config：读取 project.env 的静态 KEY=value 配置。
# 参数：
# path（必填，无默认值）：pathlib.Path；配置文件路径。
# 返回/写出与边界：返回字典；忽略空行/独立注释，重复键、非法键或不配对引号报错。不执行 shell 展开、不
#   修改配置。
def read_config(path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        key, sep, value = line.partition("=")
        if not sep or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in values:
            raise ValueError("配置不是唯一的 KEY=value：" + line)
        value = value.strip()
        if value[:1] in ("'", '"'):
            if len(value)<2 or value[-1]!=value[0]: raise ValueError("配置引号不成对："+key)
            value=value[1:-1]
        values[key] = value
    return values

# 接口｜read_table：按表头读取本地 TSV/CSV。
# 参数：
# path（必填，无默认值）：pathlib.Path；待读取表，UTF-8，可带 BOM。首行有制表符时按 TSV，否则 CSV。
# 返回/写出与边界：返回行字典列表，保留文本；缺失/重复表头或行宽不一致报错，不补列。
def read_table(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        line=handle.readline(); handle.seek(0)
        reader=csv.DictReader(handle, delimiter="\t" if "\t" in line else ",")
        fields=reader.fieldnames or []
        if not fields or any(not x for x in fields) or len(fields)!=len(set(fields)):
            raise ValueError("表头缺失或重名："+str(path))
        rows=list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError("表格行宽不一致："+str(path))
        return rows

# 接口｜identity：记录文件身份以判断完整性缓存是否仍适用。
# 参数：
# path（必填，无默认值）：pathlib.Path；现存文件，符号链接按实际目标解析。
# 返回/写出与边界：返回路径、字节数、纳秒级修改/状态时间、设备与 inode 的字典；这里只做 stat，不证明内
#   容完整。
def identity(path):
    stat=path.stat()
    return dict(path=str(path.resolve()),bytes=stat.st_size,mtime_ns=stat.st_mtime_ns,
                ctime_ns=stat.st_ctime_ns,device=stat.st_dev,inode=stat.st_ino)

# 接口｜verify_file：全量读取文件核对摘要，并对 gzip 做完整解压检查。
# 参数：
# path（必填，无默认值）：pathlib.Path；要验证的非空文件。
# expected（必填，无默认值）：字典；可含 bytes、digests（md5/sha256），来自提供方清单。没有官方摘要时
#   只能证明本地一致性/压缩完整。
# old（默认 None）：旧缓存字典或 None；只有签名、期望摘要、检查版本和完成状态全匹配才复用。
# force（默认 False）：bool；True 忽略有效缓存并重新全量读文件，可能耗时很长；False 允许复用。
# 返回/写出与边界：返回含 signature/complete/reused/digests 的缓存记录；摘要、大小、解压失败或检查期间
#   文件改变时报错，不删除或修复文件。
def verify_file(path, expected, old=None, force=False):
    """gzip CRC + 已提供的摘要；缓存绑定内容来源、文件身份及检查版本。"""
    if not path.is_file() or path.stat().st_size==0: raise ValueError("文件缺失或为空："+str(path))
    before=identity(path)
    # 缓存必须同时匹配文件身份、预期摘要和检查版本；缓存不是提供方摘要，也不能验证复制到另一位置后仍未检查
    #   的文件。
    signature=dict(version=CACHE_VERSION,file=before,expected=expected)
    if not force and old and old.get("signature")==signature and old.get("complete") is True:
        return dict(old, reused=True)
    if expected.get("bytes") and before["bytes"]!=int(expected["bytes"]): raise ValueError("字节数与来源清单不同")
    digests=expected.get('digests',{})
    if any(name not in ('md5','sha256') for name in digests): raise ValueError('只接受 MD5/SHA256 摘要')
    # 没有外部摘要时仍计算本地 SHA256 便于追踪，但报告必须另列来源验证缺口，不能把本地自算自比当成官网下载
    #   验证。
    hashes={name:hashlib.new(name) for name in (digests or {'sha256':''})}
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(8*1024*1024),b""):
            for digest in hashes.values(): digest.update(chunk)
    if any(hashes[name].hexdigest()!=digest.lower() for name,digest in digests.items()):
        raise ValueError("摘要不匹配；保留原文件，核实来源后仅处理该文件")
    if path.suffix==".gz":
        with gzip.open(path,"rb") as handle:
            while handle.read(8*1024*1024): pass
    if identity(path)!=before: raise ValueError("检查期间文件发生变化，本次结果不可缓存")
    return dict(signature=signature,complete=True,reused=False,digests={n:h.hexdigest() for n,h in hashes.items()},
                checked_at=dt.datetime.now(dt.timezone.utc).isoformat())

# 接口｜fasta_ids：检查压缩 FASTA 格式并提取标题 ID。
# 参数：
# path（必填，无默认值）：pathlib.Path；gzip FASTA 路径，标题首字段为 ID，版本点号保留。
# 返回/写出与边界：返回 ID 集合；序列/标题为空、ID 重复或字符不合法时报错。不是比对、也不验证物种来源。
def fasta_ids(path):
    ids=set(); current=None; bases=0
    with gzip.open(path,"rt") as handle:
        for line in handle:
            if line.startswith(">"):
                if current is not None and bases==0: raise ValueError("空 FASTA 序列："+current)
                parts=line[1:].split()
                if not parts or parts[0] in ids: raise ValueError("FASTA ID 为空或重复："+str(path))
                current=parts[0]; ids.add(current); bases=0
            elif line.strip():
                if current is None: raise ValueError("FASTA 第一条序列缺少标题")
                if not re.fullmatch(r"[A-Za-z*.-]+",line.strip()): raise ValueError("FASTA 序列含非字母字符")
                bases+=len(line.strip())
    if not ids or bases==0: raise ValueError("FASTA 没有完整非空序列")
    return ids

# 接口｜reference_check：交叉核对基因组、转录本、GTF 与 tx2gene。
# 参数：
# root（必填，无默认值）：pathlib.Path；当前项目根目录，应含 1database/genome。
# 返回/写出与边界：返回计数说明字符串；参考序列名/转录本映射不一致报错，只读输入不重建映射。
def reference_check(root):
    folder=root/"1database/genome"
    chromosome_ids=fasta_ids(folder/"genome.fa.gz")
    transcripts=fasta_ids(folder/"transcripts.fa.gz")
    aliases={}
    with gzip.open(folder/"annotation.gtf.gz","rt") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"): continue
            fields=line.rstrip("\n").split("\t")
            if len(fields)!=9: raise ValueError("GTF 不是九列")
            if fields[0] not in chromosome_ids: raise ValueError("GTF 的序列名不在 genome FASTA："+fields[0])
            attrs=dict(re.findall(r'(?:^|;\s*)(\w+)\s+"([^"]*)"',fields[8]))
            tx,gene=attrs.get("transcript_id"),attrs.get("gene_id")
            if tx and gene:
                for key in [tx]+([tx+"."+attrs["transcript_version"]] if attrs.get("transcript_version") else []):
                    if key in aliases and aliases[key]!=gene: raise ValueError("GTF 转录本对应多个基因："+key)
                    aliases[key]=gene
    missing=transcripts-set(aliases)
    if missing: raise ValueError("FASTA 转录本无同版 GTF 对应："+", ".join(sorted(missing)[:5]))
    rows=read_table(folder/"tx2gene.tsv")
    if not rows or not {"transcript_id","gene_id"}<=set(rows[0]): raise ValueError("请先完成第 03 章 tx2gene.tsv")
    mapping={r["transcript_id"]:r["gene_id"] for r in rows}
    if len(mapping)!=len(rows) or any(not k or not v for k,v in mapping.items()): raise ValueError("tx2gene ID 重复或缺失")
    if any(mapping.get(tx)!=aliases[tx] for tx in transcripts): raise ValueError("tx2gene 与当前 FASTA/GTF 不一致；不能沿用另一参考的对应表")
    return f"{len(chromosome_ids)} 条基因组序列；{len(transcripts)} 个转录本与 GTF/tx2gene 明确对应"

# 接口｜fastq_preview：抽样检查 FASTQ 四行格式及 read ID。
# 参数：
# path（必填，无默认值）：pathlib.Path；单端 gzip FASTQ 文件。
# limit（默认 1000）：正整数；最多抽取的 reads 条数，默认 1000。不是抽取 1000 个样本或文件字节数。
# 返回/写出与边界：返回前 limit 条规范化 read ID 列表，用于双端对照；不是全量配对证明，完整性检查由
#   verify_file 负责。
def fastq_preview(path, limit=1000):
    ids=[]
    with gzip.open(path,"rt") as handle:
        for i in range(limit):
            head=handle.readline()
            if not head: break
            seq,plus,quality=handle.readline().strip(),handle.readline(),handle.readline().rstrip("\r\n")
            if not head.startswith("@") or not plus.startswith("+") or not seq or len(seq)!=len(quality):
                raise ValueError(f"FASTQ 格式抽样失败：{path.name}，第 {i+1} 条")
            ids.append(re.sub(r"/[12]$","",head[1:].split()[0]))
    if not ids: raise ValueError("FASTQ 没有 reads："+path.name)
    return ids

# 接口｜environment_prefix：定位一个已经存在的 Conda 环境。
# 参数：
# name（必填，无默认值）：字符串环境名，如 rnaseq；不带项目版本号。
# 返回/写出与边界：返回环境 Path；找不到则报错。查询 conda env list，但不会安装、升级或激活环境。
def environment_prefix(name):
    if Path(sys.prefix).name==name: return Path(sys.prefix)
    candidates=[Path(sys.prefix).parent/name]
    conda=os.environ.get("CONDA_EXE") or shutil.which("conda")
    if conda:
        run=subprocess.run([conda,"env","list","--json"],capture_output=True,text=True,timeout=60)
        if run.returncode==0:
            candidates += [Path(p) for p in json.loads(run.stdout)["envs"] if Path(p).name==name]
    for path in candidates:
        if (path/"bin").is_dir(): return path
    raise ValueError("找不到 Conda 环境 "+name+"；先完成第 01 章并激活环境")

# 接口｜run_r：在指定已有环境中运行一个 R 检查子进程。
# 参数：
# prefix（必填，无默认值）：环境安装目录 Path；使用其 bin/Rscript。
# arguments（必填，无默认值）：字符串列表；传给 Rscript 的参数，不通过 shell eval。
# cwd（必填，无默认值）：Path；子进程工作目录，须为检查的项目根目录。
# 返回/写出与边界：返回标准输出字符串，非零退出时以输出尾部抛 ValueError；限制 BLAS 线程，不安装软件。
def run_r(prefix, arguments, cwd):
    env=dict(os.environ,OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1")
    result=subprocess.run([str(prefix/"bin/Rscript"),*arguments],cwd=cwd,env=env,capture_output=True,text=True)
    if result.returncode: raise ValueError((result.stderr+result.stdout)[-5000:])
    return result.stdout

# 接口｜software_checks：按选择的章节核实可执行文件和 R 包。
# 参数：
# chapters（必填，无默认值）：整数列表；第 05–20 章检查范围，未选支线不要求其环境。
# root（必填，无默认值）：Path；项目根目录，用作程序启动检查的工作目录。
# add（必填，无默认值）：回调函数 add(name,status,detail)，把每个环境的检查结果加入报告。
# 返回/写出与边界：通过 add 回调记录 PASS/FAIL；检查版本/能否加载，不运行真实分析，不自动装包。
def software_checks(chapters, root, add):
    commands={"rnaseq":set(),"rnaseq_time":set(),"rnaseq_eggnog":set(),"rnaseq_gtf":set()}
    packages={"rnaseq":{"jsonlite","digest"},"rnaseq_time":set()}
    if any(n in chapters for n in (5,6)): commands['rnaseq'].update(['fastqc','multiqc'])
    if 6 in chapters: commands['rnaseq'].add('fastp')
    if 7 in chapters: commands['rnaseq'].add('salmon')
    if any(n in chapters for n in (8,10)): commands['rnaseq'].add('Trinity')
    for n, names in {9:['tidyverse','pheatmap','PCAtools'],10:['DESeq2'],11:['tidyverse','VennDiagram','ggVennDiagram','UpSetR'],
                     12:['EnhancedVolcano','ggrepel','tidyverse'],13:['tidyverse','pheatmap','RColorBrewer'],
                     14:['tidyverse','clusterProfiler','enrichplot','patchwork'],15:['tidyverse','clusterProfiler','enrichplot'],
                     18:['tidyverse','AnnotationForge','AnnotationDbi'],19:['tidyverse','clusterProfiler','enrichplot','patchwork'],
                     20:['tidyverse','clusterProfiler','enrichplot']}.items():
        if n in chapters: packages['rnaseq'].update(names)
    if any(n in chapters for n in (16,17,19)): packages['rnaseq_time'].update(['jsonlite','digest','tidyverse'])
    if any(n in chapters for n in (16,19)): packages['rnaseq_time'].update(['ClusterGVis','Mfuzz','clusterProfiler','ComplexHeatmap'])
    if 17 in chapters: packages['rnaseq_time'].add('MetaCycle')
    if 18 in chapters:
        commands['rnaseq_eggnog'].update(['emapper.py','diamond','seqkit']); commands['rnaseq_gtf'].update(['gtftk','seqtk'])
    for name in commands:
        bins=commands[name]; libs=packages.get(name,set())
        if not bins and not libs: continue
        try:
            prefix=environment_prefix(name)
            missing=[b for b in sorted(bins) if not (prefix/'bin'/b).is_file() or not os.access(prefix/'bin'/b,os.X_OK)]
            if missing: raise ValueError('缺少软件：'+', '.join(missing))
            probe_env=dict(os.environ,PATH=str(prefix/'bin')+os.pathsep+os.environ.get('PATH',''))
            for binary in sorted(bins):
                version_args={'seqtk':[],'seqkit':['version'],'diamond':['version']}
                probe=[str(prefix/'bin'/binary)]+version_args.get(binary,['--version'])
                result=subprocess.run(probe,cwd=root,
                                      env=probe_env,capture_output=True,text=True,timeout=60)
                seqtk_help=binary=='seqtk' and result.returncode==1 and 'Version:' in result.stdout+result.stderr
                if result.returncode and not seqtk_help:
                    raise ValueError(binary+' 不能正常启动：'+(result.stderr+result.stdout)[-1000:])
                if binary=='emapper.py' and '2.1.15' not in result.stdout+result.stderr:
                    raise ValueError('eggNOG-mapper 应为指定的 2.1.15：'+result.stdout+result.stderr)
            if libs:
                expr='p<-commandArgs(TRUE); for (n in p) if (!requireNamespace(n,quietly=TRUE)) stop("缺少 R 包：",n); '
                if 'ClusterGVis' in libs: expr+='stopifnot(packageVersion("ClusterGVis")=="0.1.2"); '
                if 'MetaCycle' in libs: expr+='stopifnot(packageVersion("MetaCycle")=="1.2.1"); '
                expr+='cat(paste(p,collapse=", "))'
                run_r(prefix,['-e',expr,*sorted(libs)],root)
            add('软件 '+name,'PASS',', '.join(sorted(bins|libs)))
        except Exception as error: add('软件 '+name,'FAIL',str(error))

# 接口｜expected_checksums：合并提供方摘要与已有历史下载清单。
# 参数：
# root（必填，无默认值）：Path；项目根目录，用来定位可选 checksums.tsv/download_manifest.tsv。
# samples（必填，无默认值）：样本行字典列表；只对本次有关的样本从历史清单匹配双端摘要。
# 返回/写出与边界：返回按解析后文件路径索引的预期摘要字典；冲突、重复或格式错误报错，不修改历史清单。
def expected_checksums(root, samples):
    expected={}
    # 接口｜merge：向上层预期摘要字典合并单个来源记录。
    # 参数：
    # key（必填，无默认值）：字符串；解析后的完整文件路径，作为字典键。
    # digests（必填，无默认值）：算法名到十六进制摘要的字典，MD5/SHA256 由外层核实格式。
    # source（必填，无默认值）：字符串；官方/提供方来源说明，用于追溯而非下载。
    # size（必填，无默认值）：压缩文件正整数字节数（字符串/数值）或空；不是 GiB，空表示未提供。
    # 返回/写出与边界：原地更新外层 expected；算法摘要或文件大小冲突时抛错，不静默选择其中一份。
    def merge(key,digests,source,size):
        item=expected.setdefault(key,dict(digests={},sources=[],bytes=''))
        for algorithm,digest in digests.items():
            if algorithm in item['digests'] and item['digests'][algorithm]!=digest.lower():
                raise ValueError('两份摘要清单冲突，请核实：'+key)
            item['digests'][algorithm]=digest.lower()
        if size:
            if not re.fullmatch(r'[1-9][0-9]*',str(size)): raise ValueError('bytes 应为压缩文件的正整数字节数')
            if item['bytes'] and int(item['bytes'])!=int(size): raise ValueError('两份清单字节数冲突：'+key)
            item['bytes']=str(size)
        item['sources']=sorted(set(item['sources']+[source]))
    path=root/'0script/checksums.tsv'
    if path.exists():
        seen=set()
        for row in read_table(path):
            if not row.get('path') or not row.get('source'): raise ValueError('checksums.tsv 需要 path、source 及 md5 或 sha256')
            digests={name:row[name] for name in ('md5','sha256') if row.get(name)}
            if not digests or any(not re.fullmatch(r'[0-9a-fA-F]{64}' if name=='sha256' else r'[0-9a-fA-F]{32}',digest) for name,digest in digests.items()):
                raise ValueError('摘要格式不合法：'+row['path'])
            key=str((root/row['path']).resolve())
            if key in seen: raise ValueError('摘要清单路径重复')
            seen.add(key); merge(key,digests,row['source'],row.get('bytes',''))
    # 兼容已有案例来源清单；不生成、更新或查询这份历史记录。
    manifest=root/'0script/download_manifest.tsv'
    if manifest.exists():
        rows=read_table(manifest)
        by_sample={x['sample_id']:x for x in samples}
        for row in rows:
            sample=by_sample.get(row.get('sample_id'))
            if not sample: continue
            for mate in (1,2):
                if not sample.get(f'read{mate}'): continue
                digest=row.get(f'md5_r{mate}','')
                if not re.fullmatch('[0-9a-fA-F]{32}',digest): raise ValueError('历史下载清单 MD5 格式不合法')
                key=str((root/'2data/rawdata'/sample[f'read{mate}']).resolve())
                merge(key,{'md5':digest},row.get(f'read{mate}_url',''),row.get(f'bytes_r{mate}',''))
    return expected

# 接口｜main：协调准备检查并生成带边界的报告。
# 参数：无函数形参，命令行选项见文件头。
# 返回/写出与边界：从命令行读取参数（不设函数形参）；返回失败退出码 1，否则 0，但 --no-software 的 0
#   仍只表示 PARTIAL。仅写 runlogs 的时间戳报告和完整性缓存。
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path.cwd())
    parser.add_argument('--chapters',help='例如 9,10,12；省略检查当前入口的常规主线')
    parser.add_argument('--force-full',action='store_true')
    parser.add_argument('--no-software',action='store_true',help='仅材料诊断，报告标为部分检查')
    parser.add_argument('--protein-mapping',type=Path,help='仅第 18 章自备蛋白的明确对应表')
    args=parser.parse_args(); root=args.project.resolve(strict=True)
    config=read_config(root/'0script/project.env'); entry=config.get('DATA_ENTRY','')
    if entry not in ('fastq','matrix'): parser.error('DATA_ENTRY 必须为 fastq 或 matrix')
    try: chapters=sorted(set(int(x) for x in args.chapters.split(','))) if args.chapters else list(range(5 if entry=='fastq' else 9,16))
    except ValueError: parser.error('--chapters 需要逗号分隔的章节整数')
    if not chapters or any(n<5 or n>20 for n in chapters): parser.error('检查范围为第 05–20 章')
    rows=[]
    # 接口｜add：向准备检查报告追加一条记录并即时打印。
    # 参数：
    # name（必填，无默认值）：字符串检查项名称。
    # status（必填，无默认值）：字符串状态，如 PASS、FAIL、WARN、NOT_SELECTED。
    # detail（必填，无默认值）：字符串说明；写明依据、失败原因或检查边界。
    # 返回/写出与边界：更新外层 rows 列表并写标准输出；无返回分析对象，不改变被检查文件。
    def add(name,status,detail): rows.append(dict(check=name,status=status,detail=detail)); print(f'{status} {name}: {detail}',flush=True)
    log=root/'0script/runlogs'; log.mkdir(parents=True,exist_ok=True)
    cache_file=log/'04.5_integrity_cache.json'
    try: old=json.loads(cache_file.read_text()).get('files',{}) if cache_file.exists() else {}
    except (ValueError,OSError): old={}; add('缓存','WARN','旧缓存不可读，本次不复用')
    # 局部检查保留其他文件的历史缓存；不能因只检查矩阵而抹掉大 FASTQ 的有效记录。
    current=dict(old)
    threads=config.get('THREADS','')
    if not re.fullmatch(r'[1-9][0-9]*',threads): add('THREADS','FAIL','线程预算须为正整数，请检查 project.env')
    if args.no_software: add('软件','NOT_SELECTED','仅材料诊断；不代表全部准备完成')
    else: software_checks(chapters,root,add)
    samples=[]
    try:
        result=json.loads(run_r(environment_prefix('rnaseq'),[str(root/'0script/scripts/04_5_tables.R'),entry,','.join(map(str,chapters))],root))
        for row in result['checks']: add(row['check'],row['status'],row['detail'])
        samples=result['samples']
    except Exception as error: add('表格检查','FAIL',str(error))
    # 只检查本次范围的入口材料；所选章节将在运行时生成的中间文件不提前索要。
    # 例如只做 12 不需要原始 FASTQ；只做 07 则需要已有 clean FASTQ。
    files=[]; raw_needed=any(n in chapters for n in (5,6)); refs=any(n in chapters for n in (7,8))
    clean_needed=7 in chapters and 6 not in chapters
    if entry=='matrix' and any(n<9 for n in chapters):
        add('章节范围','FAIL','matrix 入口从第 09 章开始；要做第 05–08 章请准备 FASTQ 并更改 DATA_ENTRY')
        raw_needed=clean_needed=False
    if raw_needed:
        files += [root/'2data/rawdata'/s[f'read{mate}'] for s in samples for mate in (1,2)]
        if not samples: add('FASTQ','FAIL','样本表未通过，无法确认需要哪些原始文件')
    if clean_needed:
        files += [root/'2data/cleandata/fastp'/f"{s['sample_id']}_clean_{mate}.fastq.gz" for s in samples for mate in (1,2)]
    if refs:
        files += [root/'1database/genome'/n for n in ('genome.fa.gz','transcripts.fa.gz','annotation.gtf.gz')]
    if 18 in chapters:
        files += [root/'1database/genome'/name for name in ('proteins.fa.gz','annotation.gtf.gz')]
    files=list(dict.fromkeys(files))
    if 8 in chapters and 7 not in chapters:
        for sample in samples:
            path=root/'3Salmon'/f"{sample['sample_id']}.quant"/'quant.sf'
            try:
                table=read_table(path)
                if not table or not {'Name','Length','EffectiveLength','TPM','NumReads'}<=set(table[0]):
                    raise ValueError('不是有效的 Salmon quant.sf 表头或表格为空')
                add('既有定量 '+sample['sample_id'],'PASS',str(path))
            except Exception as error: add('既有定量 '+sample['sample_id'],'FAIL',str(error))
    try: expected=expected_checksums(root,samples if raw_needed else []) if files else {}
    except Exception as error: expected={}; add('摘要清单','FAIL',str(error))
    total=sum(p.stat().st_size for p in files if p.is_file())
    print(f'完整性检查范围：{len(files)} 个文件，{total/1024**3:.2f} GiB；首次读取全部压缩内容，命中有效记录时复用。',flush=True)
    for path in files:
        key=str(path.resolve()); exp=expected.get(key,{})
        try:
            record=verify_file(path,exp,old.get(key),args.force_full); current[key]=record
            add(str(path.relative_to(root)),'PASS','复用有效完整性记录' if record['reused'] else '本次完成完整性检查')
            if not exp.get('digests'): add(path.name+' 来源摘要','WARN','未提供官方/提供方摘要；gzip 通过和本地指纹不等于官方摘要验证')
        except Exception as error:
            current.pop(key,None)
            add(str(path.relative_to(root)),'FAIL',str(error))
    if refs:
        try: add('参考对应','PASS',reference_check(root))
        except Exception as error: add('参考对应','FAIL',str(error))
    if raw_needed or clean_needed:
        for sample in samples:
            try:
                paths=([root/'2data/rawdata'/sample[f'read{m}'] for m in (1,2)] if raw_needed else
                       [root/'2data/cleandata/fastp'/f"{sample['sample_id']}_clean_{m}.fastq.gz" for m in (1,2)])
                reads=[fastq_preview(path) for path in paths]
                if reads[0]!=reads[1]: raise ValueError('R1/R2 前 1000 条 read ID/数量不匹配')
                add('FASTQ 格式 '+sample['sample_id'],'PASS','前 1000 条四行格式、长度和双端 ID 抽样通过；不是全量 reads 配对证明')
            except Exception as error: add('FASTQ 格式 '+sample['sample_id'],'FAIL',str(error))
    if any(n in chapters for n in (14,15)):
        add('KEGG','WARN','按对应分析章 include_kegg 决定；核实 KEGG_ORGANISM/KEYTYPE 和网络，预检不联网转换 ID或证明映射完整')
    if 18 in chapters:
        try:
            sys.path.insert(0,str(root/'0script/tools'))
            from protein_identity import build_links
            mapping=(root/args.protein_mapping) if args.protein_mapping else None
            links=build_links(root/'1database/genome/annotation.gtf.gz',root/'1database/genome/proteins.fa.gz',mapping)
            add('蛋白对应','PASS',f'{len(links)} 个明确映射')
        except Exception as error: add('蛋白对应','FAIL',str(error))
        database=root/config.get('EGGNOG_DATA_DIR','__missing_database__')
        for name in ('eggnog.db','eggnog_proteins.dmnd'):
            path=database/name
            add('eggNOG '+name,'PASS' if path.is_file() and path.stat().st_size>0 else 'FAIL',str(path)+'；这里只检查存在和非空，不扫描大型数据库')
        add('注释参数','WARN','第 18 章仍须核实 tax_id、属种名、供体范围和数据库版本；预检不改变这些设计')
    # 综合状态以 FAIL 优先；--no-software 即使无材料错误也只标 PARTIAL。有警告时保留 PASS_WITH_WARNINGS，
    #   不能只看退出码。
    failed=any(x['status']=='FAIL' for x in rows)
    status='FAIL' if failed else ('PARTIAL' if args.no_software else 'PASS_WITH_WARNINGS' if any(x['status']=='WARN' for x in rows) else 'PASS')
    report=dict(status=status,entry=entry,chapters=chapters,checks=rows,checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                boundary='仅所选范围准备检查；不保证实验设计合理，不执行统计分析、不自动修复。')
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'); base=log/f'04.5_preflight_{stamp}'
    # 用 exclusive 创建报告；不能用 with_suffix 截掉含小数点的章节号。
    with open(str(base)+'.json','x',encoding='utf-8') as handle: json.dump(report,handle,ensure_ascii=False,indent=2)
    with open(str(base)+'.md','x',encoding='utf-8') as handle:
        handle.write('# 分析前准备检查\n\n状态：'+status+'\n\n'+report['boundary']+'\n\n| 项目 | 状态 | 说明 |\n| --- | --- | --- |\n')
        for row in rows: handle.write('| '+' | '.join(str(row[k]).replace('|','\\|').replace('\n',' ') for k in ('check','status','detail'))+' |\n')
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=log,prefix='04.5_cache_',delete=False) as handle:
        json.dump(dict(version=CACHE_VERSION,files=current),handle,ensure_ascii=False,indent=2); temporary=handle.name
    os.replace(temporary,cache_file)
    print('REPORT',str(base)+'.md',flush=True)
    return 1 if failed else 0

if __name__=='__main__': raise SystemExit(main())
