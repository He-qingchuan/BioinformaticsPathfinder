"""Execute examples in disposable copies; assert outcomes independent of snapshots."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def normalize(output,lab,ident):
    output=output.replace(str(lab),'<练习目录>')
    if ident=='08-find':
        lines=output.splitlines();output='\n'.join(lines[:1]+sorted(lines[1:]))+'\n'
    return output


def execute(script,lab,args=(),check=True):
    result=subprocess.run(['bash',str(script),*args],cwd=lab,text=True,capture_output=True,timeout=20,env={**os.environ,'LC_ALL':'C.UTF-8'})
    if check:assert result.returncode==0,(script.name,result.returncode,result.stderr)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');args=parser.parse_args()
    facts=[]
    with tempfile.TemporaryDirectory(prefix='linux-course-') as tmp:
        for script in sorted((ROOT/'practice/snippets').glob('*.sh')):
            subprocess.run(['bash','-n',str(script)],check=True)
            lab=Path(tmp)/script.stem/'练习 空间'/ 'linux-lab'
            shutil.copytree(ROOT/'practice/linux-lab',lab)
            for extra in (ROOT/'practice/scripts').glob('*.sh'):shutil.copyfile(extra,lab/'tools'/extra.name)
            output=execute(script,lab).stdout
            n=int(script.name[:2]);read=lambda f:(lab/f).read_text()
            if n==3:assert output=='你好，Linux！\n一条命令，一次观察。\n'
            elif n==4:assert str(lab/'notes') in output and str(lab/'tables') in output
            elif n==5:assert read('notes/morning.txt')==read('results/day-01/morning-copy.txt') and not (lab/'results/day-01/copy.txt').exists()
            elif n==6:assert output.splitlines()==['08:00 INFO start','08:05 INFO lake ready','08:20 INFO saved','4 logs/day-01.log']
            elif n==7:assert read('results/visits.txt')=='morning\nevening\nafter rain\n'
            elif n==8:assert set(output.splitlines()[1:])=={'notes/morning.txt','notes/evening.txt','notes/雨后 记录.txt'}
            elif n==9:assert output.splitlines()==['3:08:10 WARN battery low','08:05 ERROR sensor missing']
            elif n==10:assert [s.split() for s in output.splitlines()[-2:]]==[['2','magpie'],['4','sparrow']]
            elif n==11:assert output.splitlines()[-6:]==['2','3','5','7','8','12']
            elif n==12:
                for src in (lab/'notes').glob('*.txt'):assert src.read_bytes()==(lab/'results/unpacked/notes'/src.name).read_bytes()
            elif n==13:assert output.strip()=='600'
            elif n==14:assert output=='hello\n'
            elif n==15:assert output=='后台任务已结束\n'
            elif n==16:assert output=='雨后：湖边有水洼。\n'
            elif n==17:assert output.splitlines()==['logs/day-01.log: 4','logs/day-02.log: 4']
            elif n==18:
                assert [s.split() for s in read('results/report/species-records.txt').splitlines()]==[['2','magpie'],['4','sparrow']]
                assert len(read('results/report/warnings.txt').splitlines())==2
            else:raise AssertionError(n)
            normalized=normalize(output,lab,script.stem)
            expected=ROOT/'practice/expected'/f'{script.stem}.txt'
            if args.record:expected.write_text(normalized)
            else:assert expected.read_text()==normalized,script.name
            facts.append(script.stem)
        lab=Path(tmp)/'综合 空间'/'linux-lab';shutil.copytree(ROOT/'practice/linux-lab',lab)
        summarize=ROOT/'practice/scripts/summarize.sh'
        for script in (ROOT/'practice/scripts').glob('*.sh'):subprocess.run(['bash','-n',str(script)],check=True)
        assert execute(ROOT/'practice/scripts/line-count.sh',lab,['notes/雨后 记录.txt']).stdout=='1\n'
        execute(summarize,lab,[str(lab)])
        paths=[lab/'results/report'/n for n in ['species-records.txt','warnings.txt']]
        first=[p.read_bytes() for p in paths]
        execute(summarize,lab,[str(lab)]);assert first==[p.read_bytes() for p in paths]
        (lab/'logs/day-02.log').unlink()
        missing=execute(summarize,lab,[str(lab)],False);assert missing.returncode==2 and 'Cannot read:' in missing.stderr
        (lab/'logs/day-02.log').write_text('INFO done\n');(lab/'logs/day-01.log').write_text('INFO done\n')
        execute(summarize,lab,[str(lab)]);assert (lab/'results/report/warnings.txt').read_text()==''
        assert execute(summarize,lab,[],False).returncode==2
        # An unusable output path must not be reported as a successful report.
        shutil.rmtree(lab/'results/report');(lab/'results/report').write_text('occupied')
        assert execute(summarize,lab,[str(lab)],False).returncode!=0
    report={'examples':facts,'scenarios':['Unicode and spaces','fresh fixture per example','exact semantic outcomes','repeat report','missing input','no WARN matches','missing argument','unusable output'],'bash':subprocess.check_output(['bash','--version'],text=True).splitlines()[0],'platform':Path('/etc/os-release').read_text().splitlines()[0]}
    dest=ROOT/'qa/artifacts';dest.mkdir(exist_ok=True)
    (dest/'practice.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
