#!/usr/bin/env python
"""Run one lesson, inspect evidence and assemble a report without an AI API."""
from __future__ import annotations
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from course_projects import installation, resolve_project, descriptor, create_project, input_issues
from course_runtime import (
    chapter_info, chapter_status, digest, environment_versions, inventory, read_json,
    relative, root_dir, settings, source_digest, state, write_json,
)


def check(root):
    from course_environment import check as environment_check
    result = environment_check(installation())
    if root is not None:
        print("项目输入核查：", descriptor(root)["name"])
        for code in ("01", "02", "07", "11"):
            issues = input_issues(root, code)
            print(code, "；".join(issues) if issues else "材料登记完整；内容仍需按 99 指南检查。")
    return result


def status(root):
    from course_environment import require_ready
    try:
        require_ready(installation())
        print("本机环境：已通过检查。以下为分析结果状态。")
    except RuntimeError as exc:
        print(f"本机环境：未就绪。{exc}")
    current = state(root)
    labels = {"not_run": "未运行", "running": "运行中", "failed": "失败", "stale": "需重跑", "complete": "计算完成", "skipped": "已确认跳过", "reference": "历史参考", "awaiting_input": "等待材料", "awaiting_confirmation": "等待确认"}
    for chapter in settings(root)["chapters"]:
        if chapter.get("optional"):
            continue
        code = chapter["id"]
        result = chapter_status(code, root)
        review = read_json(root / "reports/sections" / (code + ".json"), {})
        record = current["chapters"].get(code, {})
        source = root / "reports/sections" / (code + ".md")
        interpretation = "仅供查阅，不续跑" if result=="reference" else ("已解读" if review_valid(root, code, result) else "待解读")
        print(f"{code}  {chapter['title']:<20} {labels[result]} / {interpretation}")


def execute(root, code, fresh=False):
    """运行项目课件；同一次有效等待可续跑，改变科学输入必须另开尝试。"""
    if descriptor(root).get("read_only"):
        raise ValueError("教程示例只读；请创建 tutorial 练习项目。")
    from course_environment import require_ready
    require_ready(installation())
    if code == "E02":
        require_ready(installation(), "scvi", active=False)
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
    import psutil
    import threading
    spec = chapter_info(code, root)
    for parent in spec.get("depends", []):
        if chapter_status(parent, root) not in ("complete", "skipped"):
            raise RuntimeError(f"请先运行第 {parent} 章；当前上游结果不完整或已过期。")
    executable = installation() / ".envs" / ("scvi" if code == "E02" else "sc_rna") / "bin/python"
    if not executable.exists():
        raise RuntimeError("请先运行 bash setup.sh --scvi 准备扩展环境。")
    previous = state(root)["chapters"].get(code, {})
    resumable = chapter_status(code, root) in ("awaiting_input", "awaiting_confirmation")
    attempt = previous["attempt"] if resumable and not fresh else time.strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:6]
    directory = root / "results" / spec["slug"] / attempt
    directory.mkdir(parents=True, exist_ok=True)
    nb = nbformat.read(root / spec["notebook"], as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    env = os.environ.copy()
    threads = str(settings(root)["parameters"]["threads"])
    env.update(SC_COURSE_ROOT=str(installation()), SC_COURSE_PROJECT=root.name, SC_COURSE_ATTEMPT=attempt,
               OMP_NUM_THREADS=threads, OPENBLAS_NUM_THREADS=threads,
               MKL_NUM_THREADS=threads, NUMBA_NUM_THREADS=threads,
               PYTHONNOUSERSITE="1", PYTHONHASHSEED="0",
               MPLCONFIGDIR=str(root / ".runtime/matplotlib"),
               IPYTHONDIR=str(root / ".runtime/ipython"))

    class ProjectKernelSpecManager(KernelSpecManager):
        def get_kernel_spec(self, kernel_name):
            return KernelSpec(argv=[str(executable), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                              display_name="scRNA course", language="python")

    manager = KernelManager(kernel_name="course", kernel_spec_manager=ProjectKernelSpecManager())
    started = time.time()
    memory = {"peak_process_tree_rss_bytes": 0}
    stopped = threading.Event()

    def monitor():
        process = psutil.Process()
        while not stopped.wait(0.5):
            total = 0
            for child in [process] + process.children(recursive=True):
                try:
                    total += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            memory["peak_process_tree_rss_bytes"] = max(memory["peak_process_tree_rss_bytes"], total)

    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    log_path = directory / "execution.log"

    def after_cell(cell, cell_index, **kwargs):
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n--- Cell {cell_index} ---\n")
            for number, output in enumerate(cell.get("outputs", [])):
                if output.output_type == "stream":
                    log.write(output.text)
                if output.output_type == "error":
                    log.write("\n".join(output.traceback))
                data = output.get("data", {})
                if "image/png" in data:
                    images = directory / "figures"
                    images.mkdir(exist_ok=True)
                    (images / f"cell_{cell_index:03d}_{number:02d}.png").write_bytes(base64.b64decode(data["image/png"]))
        print(f"[{code}] 完成单元格 {cell_index + 1}/{len(nb.cells)}", flush=True)

    client = NotebookClient(nb, km=manager, timeout=3600, allow_errors=False,
                            force_raise_errors=True, on_cell_executed=after_cell,
                            resources={"metadata": {"path": str(root)}})
    failure = None
    paused = False
    try:
        client.execute(env=env)
    except Exception as exc:
        current = state(root)
        record = current["chapters"].get(code, {})
        # 只有本次内核明确发出的教学等待才按正常暂停处理；其他异常照常失败。
        paused = (record.get("attempt") == attempt
                  and record.get("status") in ("awaiting_input", "awaiting_confirmation")
                  and getattr(exc, "ename", "") == "AwaitingDecision")
        if not paused:
            failure = exc
            owns_current = not record or record.get("attempt") == attempt
            if not owns_current:
                record = {"id": code, "attempt": attempt, "directory": relative(directory, root)}
            record.update(status="failed", error=str(exc)[-5000:])
            if owns_current:
                current["chapters"][code] = record
                write_json(root / "results/state.json", current)
            write_json(directory / "run.json", record)
    finally:
        stopped.set()
        watcher.join(timeout=2)
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
        if client.kc is not None:
            client.kc.stop_channels()
        nbformat.write(nb, directory / "executed.ipynb")
        write_json(directory / "resources.json", {**memory, "wall_seconds": round(time.time() - started, 2)})
        current = state(root)
        record = current["chapters"].get(code)
        if record and record.get("attempt") == attempt:
            record["artifacts"] = inventory(directory, root)
            record["resources"] = read_json(directory / "resources.json")
            write_json(directory / "run.json", record)
            write_json(root / "results/state.json", current)
    # Refresh the export after any attempt so an old downstream interpretation
    # is not left in the Word document after its input has become stale.
    build_report(root)
    if paused:
        record = state(root)["chapters"][code]
        print("正常暂停：" + record["message"])
        print("待办与候选：" + record["request"])
        return
    if failure:
        raise RuntimeError(f"第 {code} 章执行失败，请查看 {relative(directory / 'executed.ipynb', root)}") from failure
    if chapter_status(code, root) != "complete":
        raise RuntimeError("章节没有提交有效检查点，请检查最后一个单元格。")
    print(f"图表和摘要：{relative(directory / 'run.json', root)}")
    print("请阅读结果，保存解读 Markdown，再使用 course review 绑定本次运行。")


def review(root, code, source):
    if chapter_status(code, root) not in ("complete", "skipped"):
        raise RuntimeError("只能为当前有效的已完成/明确跳过章节提交解读。")
    record = state(root)["chapters"][code]
    source = Path(source).resolve()
    text = source.read_text(encoding="utf-8")
    for heading in ("目的", "方法", "结果", "解释"):
        if not re.search(r"^#{1,4}\s+.*" + heading, text, re.M):
            raise ValueError("本章解读需包含目的、方法、结果、解释四项标题。")
    evidence = []
    # 图片只需核对其所属的当前章节，避免每张图重新哈希所有大型检查点。
    valid_directories = [(chapter, root / item["directory"])
                         for chapter,item in state(root)["chapters"].items()]
    for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
        path = (root / target).resolve()
        if not path.is_file() or not any(path.is_relative_to(d) and chapter_status(chapter, root) in ("complete", "skipped") for chapter,d in valid_directories):
            raise ValueError(f"图片必须来自当前有效结果：{target}")
        evidence.append(relative(path, root))
    destination = root / "reports/sections" / (code + ".md")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        history = root / "reports/.meta/history" / code
        history.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:6]
        (history / (stamp + ".md")).write_text(destination.read_text(encoding="utf-8"), encoding="utf-8")
        previous = read_json(destination.with_suffix(".json"))
        if previous:
            write_json(history / (stamp + ".json"), previous)
    destination.write_text(text, encoding="utf-8")
    write_json(destination.with_suffix(".json"), {
        "chapter": code, "attempt": record["attempt"], "markdown_sha256": digest(destination),
        "evidence": {f: digest(root / f) for f in evidence},
        "tables": {a["path"]: digest(root / a["path"]) for a in record.get("artifacts", []) if a["kind"] == "csv"},
        "reviewed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    })
    print(f"第 {code} 章解读已与本次运行关联。")
    build_report(root)


def review_valid(root, code, known_status=None):
    """解读正文、当前尝试、引用图片和本章数字表均未变，才进入正式报告。"""
    record = state(root)["chapters"].get(code, {})
    source = root / "reports/sections" / (code + ".md")
    meta = read_json(source.with_suffix(".json"), {})
    # 无解读时先返回；调用方刚核对过的状态可以复用，证据内容仍逐项检查。
    if not (source.exists() and meta.get("attempt") == record.get("attempt")
            and meta.get("markdown_sha256") == digest(source)):
        return False
    if (known_status or chapter_status(code, root)) not in ("complete", "skipped"):
        return False
    for collection in (meta.get("evidence", {}), meta.get("tables", {})):
        if not isinstance(collection, dict):
            return False
        if any(not (root / f).is_file() or digest(root / f) != h for f,h in collection.items()):
            return False
    return True


def build_report(root):
    """每次从有效章节重新合成 Word；过期解读从成品撤出，历史源文件仍保留。"""
    project = descriptor(root)
    if project.get("read_only"):
        print("历史参考报告：" + str(root / "reports/analysis_report.docx"))
        return
    payload = {"title": project["name"] + " — 单细胞转录组分析报告",
               "created": time.strftime("%Y-%m-%d %H:%M"), "root": str(root),
               "chapters": [], "pending": [], "appendix": [], "notes": []}
    if project.get("test_only"):
        payload["title"] = "[流程验收，非用户科学确认] " + payload["title"]
    current = state(root)["chapters"]
    markdown = ["# " + payload["title"], ""]
    for spec in settings(root)["chapters"]:
        if spec.get("optional"):
            continue
        code = spec["id"]
        status_code = chapter_status(code, root)
        record = current.get(code, {})
        source = root / "reports/sections" / (code + ".md")
        if review_valid(root, code, status_code):
            payload["chapters"].append({"id":code,"title":spec["title"],
                "markdown":source.read_text(),"attempt":record["attempt"]})
            markdown += ["## 第 " + code + " 章 " + spec["title"], "", source.read_text(), ""]
        else:
            payload["pending"].append({"id":code,"title":spec["title"],"status":status_code})
        if status_code in ("complete","skipped","awaiting_input","awaiting_confirmation"):
            payload["appendix"].append({"id":code,"title":spec["title"],"artifacts":record.get("artifacts",[])})
    for source in sorted((root / "reports/notes").glob("*.md")):
        payload["notes"].append({"title":source.stem,"markdown":source.read_text()})
    if payload["pending"]:
        markdown += ["## 待完成或待更新的章节", ""] + [f"- {x['id']} {x['title']}：{x['status']}" for x in payload["pending"]]
    directory = root / "reports"
    directory.mkdir(exist_ok=True)
    write_json(directory / ".meta/report_content.json", payload)
    (directory / "analysis_report.md").write_text("\n".join(markdown), encoding="utf-8")
    index = ["# 当前结果索引", "", "路径相对于本项目目录。候选结果并非已确认的最终输出。", ""]
    for chapter in payload["appendix"]:
        index += [f"## {chapter['id']} {chapter['title']}", ""]
        index += ["- " + a["path"] for a in chapter["artifacts"]]
        index.append("")
    (directory / "artifact_index.md").write_text("\n".join(index), encoding="utf-8")
    node = installation() / ".envs/sc_rna/bin/node"
    temporary = directory / ".meta/analysis_report.pending.docx"
    subprocess.run([str(node), str(installation() / "tools/build_report.cjs"),
                    str(directory / ".meta/report_content.json"), str(temporary)], check=True)
    temporary.replace(directory / "analysis_report.docx")
    print(f"Word 已更新：{directory / 'analysis_report.docx'}（{len(payload['chapters'])} 章有效解读）")


def main():
    parser = argparse.ArgumentParser(description="逐项目、逐章运行单细胞课程；参见 99 指南")
    parser.add_argument("--project", help="项目编号；在项目目录内运行可省略")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    commands.add_parser("status")
    commands.add_parser("report")
    project = commands.add_parser("project").add_subparsers(dest="project_command", required=True)
    project.add_parser("list")
    create = project.add_parser("create")
    create.add_argument("identifier")
    create.add_argument("--name", required=True)
    create.add_argument("--preset", choices=["tutorial","custom"], default="custom")
    run = commands.add_parser("run")
    run.add_argument("chapter")
    run.add_argument("--fresh", action="store_true", help="新建尝试，保留旧结果；旧确认不自动迁移")
    interpretation = commands.add_parser("review")
    interpretation.add_argument("chapter")
    interpretation.add_argument("--source", required=True)
    choice = commands.add_parser("choose")
    choice.add_argument("chapter"); choice.add_argument("stage"); choice.add_argument("candidate")
    approval = commands.add_parser("approve")
    approval.add_argument("chapter", choices=["08"])
    for sub in (choice,approval):
        sub.add_argument("--confirmation", required=True, help="用户真实确认原文；不能由 AI 虚构")
        sub.add_argument("--test-only", action="store_true", help="只允许显式 test_only 验收项目")
    skip = commands.add_parser("skip")
    skip.add_argument("chapter", choices=["05","09","11"])
    skip.add_argument("--reason", required=True); skip.add_argument("--confirmation", required=True)
    redraw = commands.add_parser("redraw")
    redraw.add_argument("chapter"); redraw.add_argument("--script", required=True)
    model = commands.add_parser("models").add_subparsers(dest="model_command", required=True)
    search = model.add_parser("search"); search.add_argument("--query", default="")
    download = model.add_parser("download"); download.add_argument("filename")
    download.add_argument("--confirmation", required=True)
    args = parser.parse_args()
    if args.command == "project":
        if args.project_command == "create":
            create_project(args.identifier, args.name, args.preset)
        else:
            for path in sorted((installation()/"projects").glob("*/project.json")):
                data=read_json(path)
                print(data["id"], data["name"], "历史参考" if data.get("read_only") else "可运行项目")
        return
    root = resolve_project(args.project, required=args.command!="check")
    if root:
        os.environ["SC_COURSE_PROJECT"] = root.name
    if args.command == "check":
        check(root)
    elif args.command == "status":
        status(root)
    elif args.command == "run":
        execute(root, args.chapter.zfill(2), args.fresh)
    elif args.command == "review":
        review(root, args.chapter.zfill(2), args.source)
    elif args.command in ("choose", "approve"):
        from course_decisions import confirm
        confirm(root, args.chapter.zfill(2), args.stage if args.command=="choose" else "annotation",
                args.candidate if args.command=="choose" else "apply", args.confirmation, args.test_only)
    elif args.command == "skip":
        from course_actions import skip_chapter
        skip_chapter(root, args.chapter, args.reason, args.confirmation)
        build_report(root)
    elif args.command == "redraw":
        from course_actions import redraw_chapter
        redraw_chapter(root,args.chapter.zfill(2),args.script)
        build_report(root)
    elif args.command == "models":
        from course_resources import fetch_catalog,download_model
        if args.model_command=="search": fetch_catalog(root,args.query)
        else: download_model(root,args.filename,args.confirmation)
    else:
        build_report(root)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
