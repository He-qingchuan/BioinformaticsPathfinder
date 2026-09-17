#!/usr/bin/env python3
# 功能：命令行执行 MD 的明确标记入口，再调用同编号维护脚本；这里不实现统计方法。
# 调用：python 0script/tools/run_chapter.py PROJECT CHAPTER [--only NAME] [--params 参数.json] [--
#   check]。
# PROJECT：能看到 0script 的项目根目录，. 表示当前目录；CHAPTER：01–20 或 04.5。
# --only：只选择一个实际 execute 单元名，如 volcano，不是任意函数名；省略按正文标记顺序运行。
# --params：按单元分组且符合 catalog 白名单的 JSON 文件，只覆盖本次运行，不回写 MD/project.env。
# --check：只解析代码及维护依赖，不运行分析；仍会在 runlogs/generated 生成本次入口副本，不是完全无写入。
# 输入：章节 MD、维护脚本和参数 JSON。正常运行输出时间戳 log/json 并追加 execution_history.jsonl；
#   generated 是运行副本，不在这里编辑维护。
# 此文件是可执行入口：顶层解析命令行，不应当作为普通函数库 import。运行失败会停止后续单元，不自动补齐
#   所有上游。

"""Execute explicitly marked Markdown parameter/call blocks and maintained scripts.

Usage: python run_chapter.py PROJECT CHAPTER [--only BLOCK_NAME] [--check]
An executable fence is preceded by: <!-- execute: BLOCK_NAME env=ENV_NAME -->
Other examples are never run automatically. Consecutive fences sharing an
execution name are joined in document order and run in one process.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from markdown_blocks import extract_blocks, chapter_id, chapter_prefix, chapter_from_filename
from validation import validate_parameters
from execution import inject_parameters, tool_environment

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("project", type=Path)
parser.add_argument("chapter", type=chapter_id)
parser.add_argument("--only")
parser.add_argument("--check", action="store_true")
parser.add_argument("--params", type=Path, help="经过类型检查的 JSON 参数；不执行任意代码")
args = parser.parse_args()
parameters = validate_parameters(json.loads(args.params.read_text()) if args.params else {})
root = args.project.resolve(strict=True)
chapters = sorted(p for p in (root / "0script").glob("*.md")
                  if chapter_from_filename(p.name) == args.chapter)
if len(chapters) != 1:
    parser.error(f"Expected exactly one chapter, found {chapters}")
chapter = chapters[0]
body = chapter.read_text(encoding="utf-8")
blocks = extract_blocks(body)
if args.only:
    blocks = [x for x in blocks if x[0] == args.only]
if not blocks:
    parser.error("No marked execution blocks matched")
conda = os.environ.get("CONDA_EXE") or shutil.which("conda")
if not conda:
    parser.error("Conda executable unavailable; initialize Conda or export CONDA_EXE")
log_root = root / "0script/runlogs"
generated = log_root / "generated"
generated.mkdir(parents=True, exist_ok=True)
for name, environment, language, code in blocks:
    prefix = f"{chapter_prefix(args.chapter)}_{name}"
    extension = "sh" if language == "bash" else "R"
    script = generated / f"{prefix}.{extension}"
    # Generated copies are artifacts; edit MD parameters or maintained numbered scripts.
    execution_code = inject_parameters(code, name, language, parameters.get(name, {}))
    text = ("set -euo pipefail\n" if language == "bash" else "") + execution_code + "\n"
    # 生成副本用于解析和本次运行；这是可再生运行记录，不是维护源代码。--check 也执行到这一步，因此不是完全
    #   无写入的检查。
    script.write_text(text, encoding="utf-8")
    check_command = ["bash", "-n", str(script)] if language == "bash" else [
        conda, "run", "--no-capture-output", "-n", environment,
        "Rscript", "-e", "invisible(parse(commandArgs(TRUE)[1]))", str(script),
    ]
    subprocess.run(check_command, cwd=root, check=True)
    # Parse and fingerprint maintained dependencies too; a short MD cannot hide a broken script.
    # 同时追踪被 source 的脚本与 dependency 注释指向的维护文件，解析并记源文件 SHA256。纯注释更新也会改变
    #   源码摘要，但不应回写旧运行历史。
    pending = re.findall(r'(?:source\(["\']|source\s+)(0script/[^"\'\s)]+)', code)
    pending += re.findall(r'python\s+(0script/[^\s]+\.py)', code)
    dependencies = {}
    while pending:
        relative = pending.pop()
        dependency = (root / relative).resolve(strict=True)
        if root not in dependency.parents:
            raise ValueError("脚本依赖越出当前项目：" + relative)
        if relative in dependencies: continue
        contents = dependency.read_text(encoding="utf-8")
        dependencies[relative] = hashlib.sha256(dependency.read_bytes()).hexdigest()
        pending.extend(re.findall(r'(?:source\(["\']|source\s+)(0script/[^"\'\s)]+)', contents))
        pending.extend(re.findall(r'python\s+(0script/[^\s]+\.py)', contents))
        pending.extend(re.findall(r'^# dependency:\s+(0script/\S+)', contents, re.M))
        if dependency.suffix.lower() == ".r":
            command = [conda, "run", "--no-capture-output", "-n", environment,
                       "Rscript", "-e", "invisible(parse(commandArgs(TRUE)[1]))", str(dependency)]
        elif dependency.suffix == ".sh": command = ["bash", "-n", str(dependency)]
        elif dependency.suffix == ".py":
            command = [sys.executable, "-c", "import ast,sys,pathlib; ast.parse(pathlib.Path(sys.argv[1]).read_text())", str(dependency)]
        else: continue
        subprocess.run(command, cwd=root, check=True)
    if args.check:
        print(f"PARSE_OK {prefix}", flush=True)
        continue
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    code_hash = hashlib.sha256(text.encode()).hexdigest()
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    logfile = log_root / f"{prefix}_{timestamp}.log"
    invocation = ["bash", str(script)] if language == "bash" else [
        "Rscript", "-e", "options(warn=1); tryCatch(source(commandArgs(TRUE)[1], chdir=FALSE), rnaseq_result_reused=function(e) cat(conditionMessage(e), '\\n'))", str(script)
    ]
    command = [conda, "run", "--no-capture-output", "-n", environment] + invocation
    run_env = tool_environment(conda, environment)
    # 对本次子进程限定底层数学库线程，避免外层样本并行再叠加隐式 BLAS 并行；不修改系统长期环境变量。
    run_env.update({"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    print(f"START {prefix} env={environment} log={logfile}", flush=True)
    with logfile.open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=root, env=run_env, stdout=log, stderr=subprocess.STDOUT)
    record = {"chapter": chapter.name, "block": name, "environment": environment,
              "code_sha256": code_hash, "started": started,
              "finished": dt.datetime.now(dt.timezone.utc).isoformat(),
              "exit_code": result.returncode, "log": str(logfile.relative_to(root)),
              "warnings_streamed": language == "r",
              "parameters": parameters.get(name, {}),
              "dependency_sha256_at_start": dependencies}
    (log_root / f"{prefix}_{timestamp}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    with (log_root / "execution_history.jsonl").open("a", encoding="utf-8") as history:
        history.write(json.dumps(record) + "\n")
    print(f"END {prefix} exit={result.returncode}", flush=True)
    if result.returncode:
        print("\n".join(logfile.read_text(errors="replace").splitlines()[-35:]), file=sys.stderr)
        sys.exit(result.returncode)
