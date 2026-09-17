"""候选结果与人工决定。

功能说明：让 Notebook 能正常停在等待信息/确认的位置，而不伪造计算失败。
运行目的：只有当前项目、当前输入、当前候选获确认后才形成正式输出。
数据流程：章节保存候选 → AI 读图表并提问 → choose/approve 登记真实回复 → 再运行本章。
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import time


class AwaitingDecision(RuntimeError):
    """正常教学暂停；CLI 根据运行记录识别此状态，Notebook 会显示具体待办。"""


def token(value):
    """为结构化的输入身份生成稳定校验值，避免字典顺序影响确认记录。"""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def validate_files(root, files):
    """核对候选/证据在用户确认后仍未改变；只检查当前项目内的产物。"""
    from course_runtime import digest
    for filename, expected in files.items():
        path = (root / filename).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path) != expected:
            raise ValueError(f"候选或证据已经改变，请重新准备并确认：{filename}")


def annotation_rows(root, request):
    """验证逐簇建议表；每个真实簇恰好一行，人数正确，标签和证据不能缺失。"""
    import pandas as pd
    details = request["annotation"]
    frame = pd.read_csv(root / details["proposal"], dtype=str, keep_default_na=False)
    required = {"cluster_key", "cluster", "n_cells", "level1", "level2", "support", "supporting_markers",
                "opposing_markers", "evidence_refs", "rationale", "uncertainty"}
    if not required.issubset(frame.columns):
        raise ValueError(f"注释表缺列：{sorted(required-set(frame.columns))}")
    expected = {(r['cluster_key'], r['cluster']): r for r in details['clusters']}
    actual = list(zip(frame.cluster_key, frame.cluster))
    if len(set(actual)) != len(actual) or set(actual) != set(expected):
        raise ValueError("注释表的簇重复、缺失或多余；不能套用其他项目/分辨率的映射。")
    for row in frame.to_dict('records'):
        original = expected[(row['cluster_key'],row['cluster'])]
        if int(row['n_cells']) != original['n_cells']:
            raise ValueError("n_cells 应由程序生成，不能手动改变。")
        if not row['level1'].strip() or (row['cluster_key']==details['fine_key'] and not row['level2'].strip()):
            raise ValueError("标签未填完整；不能确定时请明确填写 Uncertain 并解释。")
        if row['support'] not in ('高','较高','中','低','未定') or not row['rationale'].strip() or not row['evidence_refs'].strip():
            raise ValueError("请填写定性支持程度、证据引用和理由，再向用户汇报。")
        # 引用可以附 # 行定位；文件必须属于本次程序生成的证据。
        for ref in row['evidence_refs'].split(';'):
            if ref.strip().split('#')[0] not in request['files']:
                raise ValueError(f"证据引用不属于本次输入：{ref}")
    return frame


def confirm(root, chapter, stage, candidate, confirmation, test_only=False):
    """记录操作人提供的确认原文。AI 必须先获得用户回复；本函数不生成回复。"""
    from course_runtime import chapter_status, digest, read_json, state, write_json
    from course_projects import descriptor
    record = state(root)['chapters'].get(chapter, {})
    if chapter_status(chapter, root) not in ('awaiting_confirmation','awaiting_input'):
        raise ValueError("本章没有当前有效的待确认请求，请先运行该章生成候选。")
    if record.get('pending_stage') != stage:
        raise ValueError(f"本次正在等待 {record.get('pending_stage')}，不能确认其他阶段。")
    request = read_json(root / record['request'])
    if request['binding'] != record['binding'] or request['project_uuid'] != descriptor(root)['uuid']:
        raise ValueError("请求属于其他输入或其他项目。")
    if not confirmation.strip():
        raise ValueError("必须记录用户的真实确认原文。")
    if test_only and not descriptor(root).get('test_only'):
        raise ValueError("测试确认只允许在显式标记 test_only 的验收项目使用。")
    validate_files(root, request['files'])
    if candidate not in request['options']:
        raise ValueError(f"候选不存在：{candidate}；可选 {list(request['options'])}")
    decision = {**request, 'candidate': candidate, 'confirmation': confirmation, 'test_only': test_only,
                'confirmed_at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
    if 'annotation' in request:
        annotation_rows(root, request)
        proposal = request['annotation']['proposal']
        decision['proposal_sha256'] = digest(root / proposal)
    path = root / record['directory'] / ('decision_' + stage + '.json')
    if path.exists():
        previous = read_json(path)
        write_json(path.parent / '.history' / (stage + '_' + str(time.time_ns()) + '.json'), previous)
    write_json(path, decision)
    print(f"已登记 {stage} → {candidate}。再次运行第 {chapter} 章，程序将复核并继续。")
    return decision


class DecisionMixin:
    """给原 Chapter 增加少量保存/等待方法；具体分析仍在学生代码单元格中。"""

    def wait_input(self, stage, message):
        """缺少真实材料时保存待办；不会自行填入样本、标记或模型答案。"""
        from course_runtime import relative, write_json
        request = self.directory / ('request_' + stage + '.json')
        write_json(request, {'project_uuid':self.config['uuid'], 'binding':self.record['binding'],
                             'stage':stage, 'message':message, 'options':{}, 'files':{}})
        self.record.update(status='awaiting_input',pending_stage=stage,request=relative(request,self.root), message=message)
        self._publish()
        raise AwaitingDecision(message)

    def candidate(self, stage, name, adata=None, **details):
        """独立保存候选对象；续跑时复用同一候选，防止覆盖用户看过的文件。"""
        from course_runtime import digest, read_json, relative, write_json
        directory = self.directory / 'candidates' / stage / name
        receipt = directory / 'candidate.json'
        existing = read_json(receipt, {})
        binding = token({'chapter':self.record['binding'], 'prior_choices':{k:(v['request_id'],v['candidate']) for k,v in self.record.get('decisions',{}).items()}})
        if existing and existing.get('binding') != binding:
            raise ValueError('本次尝试已有不同上游选择的候选；请使用 run --fresh 新建尝试，保留旧证据。')
        if existing and existing.get('binding') == binding:
            validate_files(self.root, existing.get('files', {}))
            return existing
        directory.mkdir(parents=True, exist_ok=True)
        item = {'id':name, 'binding':binding, 'files':{}, **details}
        if adata is not None:
            path = directory / 'candidate.h5ad'
            adata.write_h5ad(path, compression='gzip')
            item.update(checkpoint=relative(path,self.root),n_cells=adata.n_obs,n_genes=adata.n_vars)
            item['files'][relative(path,self.root)] = digest(path)
        write_json(receipt,item)
        return item

    def choose(self, stage, options, message, files=(), annotation=None):
        """先输出可比较证据，后确认；确认校验包括项目、上游、代码、文件内容。"""
        from course_runtime import digest, read_json, relative, write_json
        hashes = {relative(p,self.root):digest(p) for p in files}
        for option in options.values():
            hashes.update(option.get('files',{}))
        request = {'project_uuid':self.config['uuid'], 'chapter':self.id,'stage':stage,
                   'binding':self.record['binding'],'options':options,'message':message,'files':hashes}
        if annotation:
            request['annotation']=annotation
        request['request_id'] = token(request)
        decision = read_json(self.directory / ('decision_' + stage + '.json'), {})
        if decision.get('request_id') == request['request_id']:
            validate_files(self.root, hashes)
            if annotation and digest(self.root / annotation['proposal']) != decision.get('proposal_sha256'):
                decision = {}
            else:
                selected = decision['candidate']
                self.record.setdefault('decisions',{})[stage] = decision
                print(f"采用已确认的 {stage}：{selected}；确认原文：{decision['confirmation']}")
                return selected
        path = self.directory / ('request_' + stage + '.json')
        write_json(path, request)
        self.record.update(status='awaiting_confirmation',pending_stage=stage,request=relative(path,self.root),message=message)
        self._publish()
        print(json.dumps({k:{a:b for a,b in v.items() if a!='files'} for k,v in options.items()},ensure_ascii=False,indent=2))
        raise AwaitingDecision(message + '\n请先读图表并询问用户，登记 choose/approve 后再次运行本章。')

    def choose_data(self, stage, candidates, message):
        """比较各候选细胞数、保留率、指标分布和交集，再接受明确选择。

        basic 是三个 QC 候选共同的基础输入；双细胞比较以 keep 为共同输入。
        所有表、图只生成一次，续跑复核内容校验，避免覆盖用户已经看过的证据。
        """
        import numpy as np
        import pandas as pd
        import scanpy as sc
        import matplotlib.pyplot as plt
        table=self.tables/(stage+'_candidate_comparison.csv')
        overlap=self.tables/(stage+'_candidate_overlap.csv')
        distribution=self.tables/(stage+'_cell_metrics.csv')
        figure=self.figures/(stage+'_comparison.png')
        if not table.exists():
            rows=[];sets={};observations=[]
            baseline=candidates['basic' if stage=='qc' else 'keep']
            base=sc.read_h5ad(self.root/baseline['checkpoint'])
            base_sizes=base.obs['samples'].value_counts()
            metric_names=[x for x in base.obs if x in ('total_counts','n_genes_by_counts','doublet_score','predicted_doublet') or x.startswith('pct_counts_')]
            for name,item in candidates.items():
                data=sc.read_h5ad(self.root/item['checkpoint']);sets[name]=set(data.obs_names)
                obs=data.obs[['samples','capture_library']+metric_names].copy()
                obs.insert(0,'candidate',name);obs.insert(1,'cell',data.obs_names)
                observations.append(obs)
                for (sample,library),base_group in base.obs.groupby(['samples','capture_library'],observed=True):
                    group=obs[(obs.samples==sample)&(obs.capture_library==library)]
                    n_base=len(base_group)
                    row={'candidate':name,'sample':str(sample),'capture_library':str(library),
                         'n_cells':len(group),'n_genes':data.n_vars,'baseline_cells':n_base,
                         'retained_fraction':len(group)/n_base if n_base else np.nan}
                    for metric in metric_names:
                        row['median_'+metric]=group[metric].median()
                    if 'predicted_doublet' in group:
                        row['predicted_doublets']=int(group.predicted_doublet.sum())
                        row['predicted_doublet_fraction']=float(group.predicted_doublet.mean())
                    rows.append(row)
                del data
            frame=pd.DataFrame(rows)
            self.table(stage+'_candidate_comparison',frame,index=False)
            comparisons=[]
            for left in sets:
                for right in sets:
                    comparisons.append({'candidate_a':left,'candidate_b':right,
                        'intersection':len(sets[left]&sets[right]),'a_only':len(sets[left]-sets[right]),
                        'b_only':len(sets[right]-sets[left]),'jaccard':len(sets[left]&sets[right])/max(1,len(sets[left]|sets[right]))})
            self.table(stage+'_candidate_overlap',pd.DataFrame(comparisons),index=False)
            combined=pd.concat(observations,ignore_index=True)
            self.table(stage+'_cell_metrics',combined,index=False)
            # 上排数量/保留率，下排同一批指标的分布。缺失的物种指标不补零。
            metrics=[m for m in ('total_counts','n_genes_by_counts','pct_counts_mt','pct_counts_cp','doublet_score') if m in combined]
            fig,axes=plt.subplots(2,max(2,len(metrics)),figsize=(4*max(2,len(metrics)),7),squeeze=False)
            for axis,metric in zip(axes[0],['n_cells','retained_fraction','predicted_doublet_fraction']):
                if metric in frame:
                    frame.pivot_table(index='sample',columns='candidate',values=metric,aggfunc='sum' if metric=='n_cells' else 'mean').plot.bar(ax=axis,title=metric,rot=20)
            for axis,metric in zip(axes[1],metrics):
                axis.boxplot([combined.loc[combined.candidate==name,metric].to_numpy() for name in candidates],tick_labels=list(candidates),showfliers=False)
                axis.set_title(metric)
                if metric in ('total_counts','n_genes_by_counts'):axis.set_yscale('log')
            for axis in axes.ravel():
                if not axis.has_data():axis.set_visible(False)
            fig.tight_layout();fig.savefig(figure,dpi=130,bbox_inches='tight');plt.close(fig)
        eligible={k:v for k,v in candidates.items() if v['n_cells'] > 0}
        if not eligible:self.wait_input(stage, '所有候选均无细胞，请核对输入与过滤规则。')
        choice=self.choose(stage,eligible,message,files=[table,overlap,distribution,figure])
        return sc.read_h5ad(self.root/candidates[choice]['checkpoint'])

    def prepare_annotation(self, adata):
        """从当前对象计算表达和 QC 证据，生成空白建议表；AI 只能填写解释和标签。"""
        import numpy as np
        import pandas as pd
        from course_runtime import cluster_digest, digest, read_json, relative, write_json
        keys=adata.uns['annotation_keys']; coarse=str(keys['coarse']);fine=str(keys['fine'])
        manifest=self.directory/'annotation_inputs.json'
        proposal=self.tables/'annotation_proposal.csv'
        if not manifest.exists():
            groups=adata.uns['course_markers']
            genes=list(dict.fromkeys([str(g) for sets in groups.values() for gs in sets.values() for g in gs]
                                    +self.config.get('annotation_extra_genes',[])))
            genes=[g for g in genes if g in adata.var_names]
            X=adata.layers['log1p'][:,adata.var_names.get_indexer(genes)]
            rows=[];clusters=[];qc=[]
            for key in dict.fromkeys([coarse,fine]):
                labels=adata.obs[key].astype(str)
                for cluster in sorted(labels.unique()):
                    mask=(labels==cluster).to_numpy(); n=int(mask.sum())
                    counts={'cluster_key':key,'cluster':cluster,'n_cells':n};clusters.append(counts)
                    inside=np.asarray(X[mask].mean(axis=0)).ravel(); fractions=np.asarray((X[mask]>0).mean(axis=0)).ravel()
                    outside=np.asarray(X[~mask].mean(axis=0)).ravel() if (~mask).any() else np.full(len(genes),np.nan)
                    outside_fraction=np.asarray((X[~mask]>0).mean(axis=0)).ravel() if (~mask).any() else np.full(len(genes),np.nan)
                    for j,g in enumerate(genes):
                        rows.append({**counts,'gene':g,'mean_log1p':inside[j],'fraction_expressing':fractions[j],
                                     'mean_log1p_other':outside[j],'fraction_expressing_other':outside_fraction[j]})
                    metrics={m:float(adata.obs.loc[mask,m].median()) for m in adata.obs if m.startswith('pct_counts_') or m in ('total_counts','n_genes_by_counts','doublet_score')}
                    qc.append({**counts,**metrics})
            evidence=self.table('marker_evidence',pd.DataFrame(rows),index=False)
            quality=self.table('cluster_qc_evidence',pd.DataFrame(qc),index=False)
            draft=pd.DataFrame(clusters)
            for column in ('level1','level2','support','supporting_markers','opposing_markers','evidence_refs','rationale','uncertainty'):
                draft[column]=''
            draft['evidence_refs']=relative(evidence,self.root)+';'+relative(quality,self.root)
            draft.to_csv(proposal,index=False,encoding='utf-8-sig')
            write_json(manifest,{'coarse_key':coarse,'fine_key':fine,'clusters':clusters,
                                'cluster_sha256':{k:cluster_digest(adata,k) for k in dict.fromkeys([coarse,fine])},
                                'proposal':relative(proposal,self.root),
                                'evidence':[relative(evidence,self.root),relative(quality,self.root)]})
        details=read_json(manifest)
        for key,expected in details['cluster_sha256'].items():
            if cluster_digest(adata,key)!=expected: raise ValueError('聚类成员变化，请重新开始本章证据准备。')
        self.choose('annotation',{'apply':{'label':'应用用户审阅后的逐簇建议'}},
                    '请 AI 阅读 marker_evidence、cluster_qc_evidence 和第 07 章图片，填写 annotation_proposal.csv，解释逐簇理由，再等待用户明确确认。',
                    files=[self.root/f for f in details['evidence']]+[manifest],annotation=details)
        request=read_json(self.directory/'decision_annotation.json')
        frame=annotation_rows(self.root,request)
        maps={}
        for key,group in frame.groupby('cluster_key'):
            maps[key]={'level1':dict(zip(group.cluster,group.level1)), 'level2':dict(zip(group.cluster,group.level2))}
        write_json(self.tables/'annotation_map.json',maps)
        self._annotation_maps=maps
        return maps

    def annotation_map(self, adata, key, level):
        """读取经过本次确认的映射；不再从公共 config 读取教程答案。"""
        if not hasattr(self,'_annotation_maps'):
            self.prepare_annotation(adata)
        return self._annotation_maps[key][level]
