"""按项目核对标记、质控基因和外部模型；资源缺失时交回 AI 与用户讨论。"""
from __future__ import annotations
import json
from pathlib import Path
import time
import urllib.request

MODEL_INDEX = 'https://celltypist.cog.sanger.ac.uk/models/models.json'


def marker_resources(ctx):
    """读取本项目标记列表。JSON 使用 broad/fine；CSV 每行是一个 cell_type/gene。"""
    from course_projects import input_path
    path = input_path(ctx.root,ctx.config['markers'])
    if path.suffix.lower()=='.json':
        value=json.loads(path.read_text())
        if not all(isinstance(value.get(k),dict) and value[k] for k in ('broad','fine')):
            raise ValueError('markers JSON 需要非空 broad、fine 字典；键为候选类型，值为基因列表。')
        return value
    import pandas as pd
    frame=pd.read_csv(path,sep='\t' if path.suffix=='.tsv' else ',',dtype=str,keep_default_na=False)
    if not {'cell_type','gene','source'}.issubset(frame.columns):
        raise ValueError('标记表至少包含 cell_type、gene、source；可用 level 列区分 broad/fine。')
    value={}
    for level in ('broad','fine'):
        subset=frame if 'level' not in frame else frame[frame.level.isin([level,'both'])]
        value[level]=subset.groupby('cell_type',sort=False)['gene'].agg(list).to_dict()
    return value


def qc_gene_sets(ctx,adata):
    """按用户核对的命名/基因清单生成布尔列；未匹配到基因不会伪装为真实零比例。"""
    import numpy as np
    from course_projects import input_path
    valid=[]
    if not ctx.config.get("qc",{}).get("gene_sets"):
        ctx.wait_input("qc_genes", "未定义质控基因规则；请按物种补充，无法计算的指标需明确 disabled_reason。")
    for category,rule in ctx.config.get('qc',{}).get('gene_sets',{}).items():
        if rule.get('disabled_reason'):
            print(f"{category} 未计算：{rule['disabled_reason']}");continue
        names=adata.var[rule['column']].astype(str) if rule.get('column') else adata.var_names
        mask=np.zeros(adata.n_vars,dtype=bool)
        if rule.get('prefixes'): mask|=np.asarray(names.str.startswith(tuple(rule['prefixes'])))
        if rule.get('regex'): mask|=np.asarray(names.str.contains(rule['regex'],regex=True))
        genes=rule.get('genes',[])
        if rule.get('file'):
            genes=input_path(ctx.root,rule['file']).read_text().splitlines()
        if genes: mask|=np.asarray(names.isin(genes))
        if not mask.any():
            ctx.wait_input('qc_genes',f'{category} 未匹配任何基因，请核对物种/编号并提供清单；确实无法计算时，经用户确认后填写 disabled_reason。')
        adata.var[category]=mask;valid.append(category)
    return valid


def resolution_preview(ctx,adata,markers):
    """复用第 06 章的分辨率，先给出同一标记集合的图表，再确认粗/细聚类列。"""
    import pandas as pd
    import scanpy as sc
    import matplotlib.pyplot as plt
    from course_runtime import cluster_digest
    available={ct:list(dict.fromkeys(g for g in genes if g in adata.var_names)) for ct,genes in markers.items()}
    available={ct:genes for ct,genes in available.items() if genes}
    if not available:
        ctx.wait_input('markers','所有标记均未匹配；请先检查基因编号、物种和标记来源。')
    choices={};rows=[];evidence=[]
    for key in [x for x in adata.obs if x.startswith('leiden_res_')]:
        sizes=adata.obs[key].value_counts()
        choices[key]={'label':key,'n_clusters':int((sizes>0).sum()),'smallest_cluster':int(sizes[sizes>0].min()),
                      'cluster_sha256':cluster_digest(adata,key)}
        for label,n in sizes.items():
            rows.append({'cluster_key':key,'cluster':str(label),'n_cells':int(n)})
        # 预览复用固定文件；确认时绑定这些真实表/图，排版或数据改变需重新审阅。
        figure=ctx.figures/('compare_'+key+'.png')
        mean=ctx.tables/('compare_mean_'+key+'.csv');fraction=ctx.tables/('compare_fraction_'+key+'.csv')
        if not figure.exists():
            plot=sc.pl.dotplot(adata,available,groupby=key,layer='log1p',use_raw=False,return_fig=True,show=False)
            plot.savefig(figure,dpi=120)
            ctx.table('compare_mean_'+key,plot.dot_color_df)
            ctx.table('compare_fraction_'+key,plot.dot_size_df)
            plt.close('all')
        evidence.extend([figure,mean,fraction])
    sizes=ctx.tables/'resolution_sizes.csv'
    if not sizes.exists():ctx.table('resolution_sizes',pd.DataFrame(rows),index=False)
    evidence.append(sizes)
    coarse=ctx.choose('coarse_resolution',choices,'请先比较各分辨率的簇规模、QC 和 marker 图，再确认粗粒度展示使用的聚类列。',files=evidence)
    fine=ctx.choose('fine_resolution',choices,'请结合 marker 的群体区分度确认细粒度注释使用的聚类列。可与粗粒度相同。',files=evidence)
    adata.uns['annotation_keys']={'coarse':coarse,'fine':fine}
    return coarse,fine


def fetch_catalog(root,query=''):
    """只读取官方模型清单，不自动下载权重；失败与‘未找到适配模型’分开记录。"""
    from course_runtime import write_json
    output=root/'results/resource_checks';output.mkdir(parents=True,exist_ok=True)
    result={'source':MODEL_INDEX,'checked_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'query':query}
    try:
        with urllib.request.urlopen(MODEL_INDEX,timeout=45) as response:
            catalog=json.load(response)
        words=query.lower().split()
        result.update(status='searched',models=[m for m in catalog['models'] if all(w in (m['filename']+' '+m.get('details','')).lower() for w in words)])
        result['note']='这些是关键词候选；AI 还需核对物种、组织、阶段、标签范围和来源论文。不能把关键词匹配当适配证明。'
    except Exception as exc:
        result.update(status='network_unavailable',error=str(exc),models=[],note='无法核查官网，不代表没有适配模型；请向用户说明并讨论提供文件或跳过。')
    write_json(output/'model_search.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


def download_model(root,filename,confirmation):
    """用户明确同意后下载指定的一个模型；保留来源和哈希，下一步仍需检查适配性。"""
    from course_runtime import digest,read_json,write_json
    if not confirmation.strip(): raise ValueError('下载前请记录用户明确同意的原文。')
    search=read_json(root/'results/resource_checks/model_search.json',{})
    candidates=[m for m in search.get('models',[]) if m['filename']==filename]
    if search.get('status')!='searched' or len(candidates)!=1:
        raise ValueError('请先检索官方目录，并选择已展示给用户的确切模型文件名。')
    model=candidates[0]
    if Path(filename).name!=filename or not model['url'].startswith('https://celltypist.cog.sanger.ac.uk/'):
        raise ValueError('模型地址或文件名异常；请核查官方来源。')
    output=root/'inputs/models';output.mkdir(parents=True,exist_ok=True)
    path=output/filename
    if path.exists(): raise FileExistsError('已有同名模型，请先核对，不覆盖已有版本。')
    temporary=path.with_suffix('.download')
    try:
        with urllib.request.urlopen(model['url'],timeout=60) as response,temporary.open('wb') as out:
            while block:=response.read(1024*1024):out.write(block)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    write_json(path.with_suffix('.source.json'),{**model,'sha256':digest(path),'confirmation':confirmation,
                                               'downloaded_at':time.strftime('%Y-%m-%dT%H:%M:%S%z')})
    print(f'模型已保存：{path.relative_to(root)}。请核对物种、组织、标签和基因匹配，登记到 project.json.models。')
    return path
