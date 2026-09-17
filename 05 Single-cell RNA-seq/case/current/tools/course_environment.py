"""Validate this machine before a lesson can create or replace analysis results."""
from __future__ import annotations

import argparse
import fcntl
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile

from course_runtime import digest, read_json, settings, write_json
from course_projects import installation as root_dir

SCHEMA = 1
MODULES = ("scanpy", "anndata", "numpy", "scipy", "pandas", "matplotlib", "h5py",
           "celltypist", "harmonypy", "bbknn", "igraph", "leidenalg", "skimage",
           "nbclient", "nbformat", "ipykernel", "psutil")


def receipt_path(root, name="sc_rna"):
    return root / ".runtime" / ("preflight.json" if name == "sc_rna" else "preflight-scvi.json")


def _file_identity(path):
    stat = path.stat()
    return {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def environment_identity(root, name="sc_rna"):
    """Cheap recheck: location, host, executables, installed metadata and inputs."""
    root = root.resolve()
    prefix = root / ".envs" / name
    libraries = list((prefix / "lib").glob("python*/site-packages"))
    if not libraries:
        raise RuntimeError(f"找不到 {name} 的项目依赖目录。")
    distributions = {}
    for dist in importlib.metadata.distributions(path=[str(p) for p in libraries]):
        package = dist.metadata.get("Name")
        if package:
            distributions[package.lower().replace('_', '-')] = dist.version
    files = [prefix / "bin/python", root / ".envs/sc_rna/bin/node"]
    files += list((prefix / "conda-meta").glob("*.json"))
    files += [p for library in libraries for p in library.glob("*.dist-info/METADATA")]
    files += [p for library in libraries for p in library.glob("*.dist-info/RECORD")]
    sources = ["tools/course_environment.py", "tools/environment_smoke.py", "tools/build_report.cjs",
               "tools/package-lock.json", "tools/node_modules/docx/package.json",
               "tools/node_modules/markdown-it/package.json"]
    return {
        "schema": SCHEMA, "root": str(root), "prefix": str(prefix),
        "host": platform.node(), "os": platform.system(), "machine": platform.machine(),
        "libc": list(platform.libc_ver()), "packages": dict(sorted(distributions.items())),
        "files": {str(p.relative_to(root)): _file_identity(p) for p in sorted(set(files))},
        "checks": {p: digest(root / p) for p in sources},
    }


def assert_interpreter(root, name="sc_rna"):
    prefix = (root / ".envs" / name).resolve()
    if Path(sys.prefix).resolve() != prefix or not Path(sys.executable).resolve().is_relative_to(prefix):
        raise RuntimeError(f"当前 Python 不是项目的 {name} 环境。请选择 {prefix}/bin/python，再执行环境检查。")


def require_ready(root, name="sc_rna", *, active=True):
    """Refuse early, before creating an attempt or changing results/state.json."""
    command = "bash setup.sh --scvi" if name == "scvi" else "bash setup.sh 或 ./course check"
    if active:
        assert_interpreter(root, name)
    valid = False
    try:
        record = read_json(receipt_path(root, name), {})
        current = environment_identity(root, name)
        valid = record.get("status") == "ready" and record.get("identity") == current
    except (OSError, ValueError, RuntimeError):
        pass
    if not valid:
        raise RuntimeError(f"本机 {name} 环境尚未通过检查，或目录/依赖已经变化。请先执行 {command}。参考结果的完成状态不能代替环境检查。")
    if active:
        for module_name in MODULES:
            module = sys.modules.get(module_name)
            if module is not None and getattr(module, "__file__", None):
                if not Path(module.__file__).resolve().is_relative_to(root / ".envs" / name):
                    raise RuntimeError(f"已加载的 {module_name} 来自项目环境以外。请重新选择项目内核并检查环境。")
    return record


def _kernel_smoke(root, directory, name):
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpec, KernelSpecManager

    executable = root / ".envs" / name / "bin/python"

    class ProjectKernelSpecManager(KernelSpecManager):
        def get_kernel_spec(self, kernel_name):
            return KernelSpec(argv=[str(executable), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                              display_name="course environment check", language="python")

    script = str(root / "tools/environment_smoke.py")
    source = f"import runpy, sys\nsys.argv = {[script, str(root), str(directory), name]!r}\nrunpy.run_path({script!r}, run_name='__main__')\n"
    nb = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(source)])
    manager = KernelManager(kernel_name="course-check", kernel_spec_manager=ProjectKernelSpecManager())
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.update(SC_COURSE_ROOT=str(root), PYTHONNOUSERSITE="1", PYTHONHASHSEED="0",
               OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2", NUMBA_NUM_THREADS="2",
               MPLCONFIGDIR=str(root / ".runtime/matplotlib"), IPYTHONDIR=str(root / ".runtime/ipython"),
               JUPYTER_RUNTIME_DIR=str(root / ".runtime/jupyter"))
    client = NotebookClient(nb, km=manager, timeout=600, allow_errors=False,
                            resources={"metadata": {"path": str(directory)}})
    try:
        client.execute(env=env)
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
        if client.kc is not None:
            client.kc.stop_channels()
        nbformat.write(nb, directory / "smoke.executed.ipynb")
        log = []
        for cell in nb.cells:
            for output in cell.get("outputs", []):
                if output.output_type == "stream":
                    log.append(output.text)
                elif output.output_type == "error":
                    log.append("\n".join(output.traceback))
        (directory / "kernel.log").write_text("\n".join(log), encoding="utf-8")
    return read_json(directory / "smoke.json")


def _word_smoke(root, directory):
    target = str((directory / "smoke.png").relative_to(root))
    payload = {
        "title": "环境检查：测试报告（非生物学分析）", "created": time.strftime("%Y-%m-%d %H:%M"),
        "root": str(root), "pending": [], "appendix": [], "notes": [],
        "chapters": [{"id": "TEST", "title": "环境运行测试", "markdown":
                      "## 目的\n验证中文、图片和表格可以写入 Word。\n\n"
                      "## 方法\n使用合成矩阵进行小规模计算，不产生课程分析结论。\n\n"
                      f"## 结果\n![合成数据，仅用于环境测试]({target})\n\n"
                      "| 检查 | 结果 |\n|---|---|\n| 新内核与绘图 | 通过 |\n\n"
                      "## 解释\n此文档保存在环境检查目录，不加入正式课程报告。"}],
    }
    write_json(directory / "word_input.json", payload)
    node = root / ".envs/sc_rna/bin/node"
    subprocess.run([str(node), str(root / "tools/build_report.cjs"), str(directory / "word_input.json"),
                    str(directory / "smoke.docx")], check=True, capture_output=True, text=True, timeout=120)
    with zipfile.ZipFile(directory / "smoke.docx") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("测试 Word 压缩结构损坏。")
        document = ET.fromstring(archive.read("word/document.xml"))
        if not any(n.startswith("word/media/") for n in archive.namelist()):
            raise RuntimeError("测试 Word 缺少图片。")
        if "环境运行测试" not in "".join(document.itertext()):
            raise RuntimeError("测试 Word 缺少中文正文。")


def check(root, name="sc_rna"):
    root = root.resolve()
    runtime = root / ".runtime"
    runtime.mkdir(exist_ok=True)
    with (runtime / f"preflight-{name}.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("这个环境已有检查正在运行，请等待它完成。")
        receipt = receipt_path(root, name)
        receipt.unlink(missing_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:6]
        directory = runtime / "preflight" / name / stamp
        directory.mkdir(parents=True)
        result = {"status": "checking", "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                  "directory": str(directory.relative_to(root))}
        try:
            assert_interpreter(root, name)
            if name == "scvi":
                require_ready(root, active=False)
            if platform.system() != "Linux" or platform.machine() != "x86_64":
                raise RuntimeError("正式支持 Linux x86_64；请先阅读环境准备与迁移说明。")
            for marker in (f"{name}.prepared-prefix", f"{name}.install-prefix"):
                path = runtime / marker
                if path.exists() and path.read_text().strip() != str(root / ".envs" / name):
                    raise RuntimeError("环境已被移动。请从原包重新解压，或运行 bash setup.sh --rebuild（scVI 加 --scvi）。")
            modules = MODULES + (("scvi", "torch") if name == "scvi" else ())
            locations = {}
            for module_name in modules:
                module = importlib.import_module(module_name)
                path = Path(module.__file__).resolve()
                if not path.is_relative_to(root / ".envs" / name):
                    raise RuntimeError(f"依赖 {module_name} 来自项目外部：{path}")
                locations[module_name] = str(path.relative_to(root))
            result["imports"] = locations
            print("启动独立内核：测试 PCA、UMAP、聚类、Harmony、BBKNN 和绘图；真实输入按项目核查。", flush=True)
            result["smoke"] = _kernel_smoke(root, directory, name)
            _word_smoke(root, directory)
            result["word"] = "passed: ZIP/XML, Chinese text, embedded PNG"
            result.update(status="ready", identity=environment_identity(root, name))
            write_json(directory / "result.json", result)
            write_json(receipt, result)
            (runtime / f"{name}.prepared-prefix").write_text(str(root / ".envs" / name) + "\n")
            print(f"环境检查通过：{name}。检查记录：{directory.relative_to(root)}", flush=True)
            return result
        except Exception as exc:
            result.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            write_json(directory / "result.json", result)
            receipt.unlink(missing_ok=True)
            print(f"环境未就绪，不能开始分析。诊断：{directory.relative_to(root)}", file=sys.stderr)
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scvi", action="store_true")
    args = parser.parse_args()
    check(root_dir(), "scvi" if args.scvi else "sc_rna")
