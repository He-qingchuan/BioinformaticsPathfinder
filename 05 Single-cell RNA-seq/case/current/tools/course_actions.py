"""明确跳过可选科学分支，以及只修改排版的重绘入口。

功能说明：维护原有检查点和报告，避免为了换字号重新计算聚类。
运行目的：跳过须保留理由；重绘保留脚本、旧图和内容校验，AI 看图后重新提交解读。
输入输出：项目内章节状态/检查点 → 明确的操作记录 → 当前项目的新图或传递检查点。
"""
from pathlib import Path
import os
import shutil
import subprocess
import time
import uuid


def skip_chapter(root, chapter, reason, confirmation):
    """仅 05/09/11 可按科学理由跳过；上游仍必须有效，不生成假模型结果。"""
    from course_runtime import Chapter, write_json
    if chapter not in ('05','09','11') or not reason.strip() or not confirmation.strip():
        raise ValueError('跳过需要支持的章节、具体理由和用户真实确认原文。')
    os.environ.pop('SC_COURSE_ATTEMPT',None)
    ctx=Chapter(chapter,allow_missing=True)
    data=ctx.load_input()
    if chapter=='05': data.uns['course_neighbors_key']='neighbors'
    if chapter=='11': data.uns['report_label_column']='manual_level2'
    record={'reason':reason,'confirmation':confirmation,'mode':'explicit_skip'}
    write_json(ctx.directory/'skip.json',record)
    ctx.record['skip']=record
    ctx.finish(data,record,status='skipped')


def redraw_chapter(root, chapter, script):
    """执行项目内保存的绘图脚本；参数 --checkpoint 只读，--output 为暂存图目录。

    只接收 PNG/PDF/SVG 新图；科学表格和 H5AD 的校验值必须保持一致。
    原图移入本次尝试的 .history；改变图片后原解读自动失效，待 AI 看图并 review。
    这是本地可信代码的运行入口，不是任意代码的安全沙箱。
    """
    import fcntl
    from course_projects import descriptor,installation
    from course_runtime import chapter_status,state,read_json,write_json,digest,relative,inventory
    from course_environment import require_ready
    require_ready(installation())
    if descriptor(root).get('read_only') or chapter_status(chapter,root) not in ('complete','skipped'):
        raise ValueError('只可重绘当前有效项目结果；历史参考不可改写。')
    script=Path(script).resolve()
    if not script.is_file(): raise FileNotFoundError(script)
    with (root/'.runtime/course.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        record=state(root)['chapters'][chapter]
        directory=root/record['directory']
        stamp=time.strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:6]
        work=directory/'.history/redraw'/stamp
        work.mkdir(parents=True)
        copied=work/'plot.py';shutil.copy2(script,copied)
        output=work/'new_figures';output.mkdir()
        # 将所有当前主线 H5AD、科学 CSV 及当前课件绑定，检测重绘是否越过排版范围。
        protected={}
        for code,item in state(root)['chapters'].items():
            for key in ('checkpoint',):
                if item.get(key): protected[item[key]]=digest(root/item[key])
            for a in item.get('artifacts',[]):
                if a['kind'] in ('csv','h5ad'): protected[a['path']]=digest(root/a['path'])
        env=os.environ.copy();env.update(SC_COURSE_PROJECT=root.name,SC_COURSE_ROOT=str(installation()))
        subprocess.run([str(installation()/'.envs/sc_rna/bin/python'),str(copied),
                        '--checkpoint',str(root/record['checkpoint']),'--output',str(output)],
                       cwd=root,env=env,check=True)
        if any(not (root/f).is_file() or digest(root/f)!=h for f,h in protected.items()):
            raise ValueError('重绘脚本改变了科学数据，拒绝登记为排版更新；请核查并重跑受影响章节。')
        figures=list(output.iterdir())
        if not figures or any(not f.is_file() or f.suffix.lower() not in ('.png','.pdf','.svg') for f in figures):
            raise ValueError('重绘输出只能包含至少一幅 PNG/PDF/SVG 图。')
        replacements={}
        for figure in figures:
            target=directory/'figures'/figure.name
            if target.exists():
                old=work/'previous_figures';old.mkdir(exist_ok=True)
                shutil.copy2(target,old/figure.name)
            shutil.copy2(figure,target)
            replacements[relative(target,root)]=digest(target)
        write_json(work/'redraw.json',{'chapter':chapter,'attempt':record['attempt'],
                   'script':relative(copied,root),'script_sha256':digest(copied),
                   'checkpoint_sha256':record['checkpoint_sha256'],'figures':replacements})
        record['artifacts']=inventory(directory,root)
        record.setdefault('redraws',[]).append(relative(work/'redraw.json',root))
        current=state(root);current['chapters'][chapter]=record
        write_json(directory/'run.json',record);write_json(root/'results/state.json',current)
        print('已保存新图、脚本和旧图。请实际查看图片，修订相应解读并 course review；之后 Word 使用新图。')
