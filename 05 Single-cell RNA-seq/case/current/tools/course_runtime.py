"""Shared file handling for the notebooks; analysis stays in the lesson cells."""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import time
import uuid
from course_decisions import DecisionMixin, token
from course_projects import installation, resolve_project, descriptor, config_digest, external_files, input_issues


def root_dir():
    """返回明确选择的研究项目；公共软件环境通过 installation() 单独定位。"""
    return resolve_project()


def read_json(path, default=None):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


def json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    temporary.replace(path)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_digest(path):
    content = []
    for c in read_json(path)["cells"]:
        if c["cell_type"] != "code":
            continue
        source = "".join(c["source"])
        try:
            content.append(ast.dump(ast.parse(source), include_attributes=False))
        except SyntaxError:
            content.append(source)  # Preserve IPython magic cells verbatim.
    return hashlib.sha256(json.dumps(content, ensure_ascii=False).encode()).hexdigest()


def legacy_code_digest(path):
    notebook = read_json(path)
    content = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    return hashlib.sha256(json.dumps(content, ensure_ascii=False).encode()).hexdigest()


def full_source_digest(path):
    content = [(c["cell_type"], "".join(c["source"])) for c in read_json(path)["cells"]]
    return hashlib.sha256(json.dumps(content, ensure_ascii=False).encode()).hexdigest()


def settings(root=None):
    root = root or root_dir()
    return descriptor(root) if (root / "project.json").exists() else read_json(root / "config/course.json")


def chapter_info(chapter, root=None):
    return next(c for c in settings(root)["chapters"] if c["id"] == chapter)


def relative(path, root=None):
    return os.path.relpath(Path(path).resolve(), (root or root_dir()).resolve())


def environment_versions():
    result = {"python": platform.python_version(), "platform": platform.platform(), "machine": platform.machine()}
    for name in ("scanpy", "anndata", "numpy", "scipy", "pandas", "matplotlib", "scikit-learn",
                 "harmonypy", "bbknn", "igraph", "leidenalg", "celltypist", "nbclient"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def state(root=None):
    return read_json((root or root_dir()) / "results/state.json", {"chapters": {}})


def chapter_status(chapter, root=None, visited=None):
    root = root or root_dir()
    record = state(root)["chapters"].get(chapter)
    if not record:
        return "not_run"
    if (root / "project.json").exists() and descriptor(root).get("read_only"):
        return "reference"
    if record["status"] not in ("complete", "skipped", "awaiting_input", "awaiting_confirmation"):
        return record["status"]
    spec = chapter_info(chapter, root)
    if record.get("source_sha256") != source_digest(root / spec["notebook"]):
        executed = root / record["directory"] / "executed.ipynb"
        # Earlier receipts also hashed prose. Verified identical executable cells
        # remain valid when only a lesson explanation is edited.
        if not (executed.exists() and record.get("source_sha256") in
                (full_source_digest(executed), legacy_code_digest(executed))
                and source_digest(executed) == source_digest(root / spec["notebook"])):
            return "stale"
    if record.get("config_sha256") != config_digest(root, chapter):
        return "stale"
    for filename, checksum in record.get("external_inputs", {}).items():
        if not (root / filename).is_file() or digest(root / filename) != checksum:
            return "stale"
    for parent, attempt in record.get("parents", {}).items():
        current = state(root)["chapters"].get(parent)
        if not current or current["attempt"] != attempt or chapter_status(parent, root) not in ("complete", "skipped"):
            return "stale"
    if record.get("helpers_sha256") != helpers_digest():
        return "stale"
    checkpoint = record.get("checkpoint")
    if checkpoint and (not (root / checkpoint).is_file() or digest(root / checkpoint) != record.get("checkpoint_sha256")):
        return "stale"
    return record["status"]


def helpers_digest():
    """辅助层也参与科学身份校验；修改规则后不能继续使用旧确认。"""
    return token({p: digest(installation() / "tools" / p) for p in
                  ("course_runtime.py", "course_projects.py", "course_decisions.py", "course_resources.py")})


def cluster_digest(adata, key):
    text = "\n".join(str(cell) + "\t" + str(label) for cell, label in zip(adata.obs_names, adata.obs[key]))
    return hashlib.sha256(text.encode()).hexdigest()


class Chapter(DecisionMixin):
    def __init__(self, chapter, allow_missing=False):
        import fcntl
        from course_environment import require_ready
        self.root = root_dir()
        self.installation = installation()
        if descriptor(self.root).get("read_only"):
            raise RuntimeError("教程示例是历史参考，请先创建自己的练习项目。")
        if chapter == "E02":
            require_ready(self.installation, active=False)
            require_ready(self.installation, "scvi")
        else:
            require_ready(self.installation)
        self.config = settings(self.root)
        os.environ["CELLTYPIST_FOLDER"] = str(self.root / ".runtime/celltypist")
        self.spec = chapter_info(chapter, self.root)
        self.id = chapter
        (self.root / ".runtime").mkdir(exist_ok=True)
        self.lock = (self.root / ".runtime/course.lock").open("w")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("当前项目已有章节正在运行，请等待它完成；其他项目使用独立锁。")
        # 每个项目有排他锁；公共环境为共享读锁，setup.sh 需要排他锁才能替换环境。
        self.environment_lock = (self.installation / ".runtime/course.lock").open("r")
        fcntl.flock(self.environment_lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        self.parents = {}
        for parent in self.spec.get("depends", []):
            status = chapter_status(parent, self.root)
            if status not in ("complete", "skipped"):
                raise RuntimeError(f"第 {parent} 章状态为 {status}，请先完成有效的上游运行。")
            self.parents[parent] = state(self.root)["chapters"][parent]["attempt"]
        self.started = time.time()
        self.attempt = os.environ.get("SC_COURSE_ATTEMPT") or time.strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:6]
        self.directory = self.root / "results" / self.spec["slug"] / self.attempt
        self.directory.mkdir(parents=True, exist_ok=True)
        self.figures = self.directory / "figures"
        self.tables = self.directory / "tables"
        self.figures.mkdir(exist_ok=True)
        self.tables.mkdir(exist_ok=True)
        external = {}
        paths = external_files(self.root, chapter)
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path)
            external[relative(path, self.root)] = digest(path)
        self.record = {
            "id": chapter, "title": self.spec["title"], "attempt": self.attempt, "status": "running",
            "directory": relative(self.directory, self.root), "parents": self.parents,
            "source_sha256": source_digest(self.root / self.spec["notebook"]),
            "config_sha256": config_digest(self.root, chapter),
            "helpers_sha256": helpers_digest(), "external_inputs": external, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "environment": environment_versions(), "parameters": self.config["parameters"],
        }
        self.record["binding"] = token({"project": self.config["uuid"],
            **{k:self.record[k] for k in ("source_sha256","config_sha256","helpers_sha256","external_inputs","parents","environment")}})
        self._publish()
        self._configure_plots()
        issues = input_issues(self.root, chapter) if not allow_missing else []
        if issues:
            self.wait_input("inputs", "\n".join(issues))
        print(f"第 {chapter} 章：{self.spec['title']}\n结果目录：{relative(self.directory, self.root)}")

    def _publish(self):
        write_json(self.directory / "run.json", self.record)
        current = state(self.root)
        current["chapters"][self.id] = self.record
        write_json(self.root / "results/state.json", current)

    def _configure_plots(self):
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        import scanpy as sc
        import numpy as np
        import random
        seed = self.config["parameters"]["random_seed"]
        np.random.seed(seed)
        random.seed(seed)
        sc.settings.n_jobs = self.config["parameters"]["threads"]
        sc.settings.verbosity = 1
        sc.settings.figdir = self.figures
        sc.set_figure_params(dpi=90, dpi_save=160, facecolor="white", color_map="viridis_r")
        plt.rcParams["figure.max_open_warning"] = 40
        font = self.installation / "assets/NotoSansCJKsc-Regular.otf"
        if font.exists():
            from matplotlib import font_manager
            font_manager.fontManager.addfont(str(font))
            plt.rcParams["font.family"] = ["Noto Sans CJK SC", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        original = getattr(Figure.savefig, "_course_original", Figure.savefig)
        figures = self.figures

        def save_and_mirror(figure, filename, *args, **kwargs):
            result = original(figure, filename, *args, **kwargs)
            if isinstance(filename, (str, Path)):
                path = Path(filename).resolve()
                if path.suffix.lower() == ".pdf" and path.is_relative_to(figures):
                    original(figure, path.with_suffix(".png"), dpi=160, bbox_inches="tight")
            return result

        save_and_mirror._course_original = original
        Figure.savefig = save_and_mirror

    def load_input(self):
        import scanpy as sc
        parent = self.spec.get("input")
        if not parent:
            return None
        record = state(self.root)["chapters"][parent]
        path = self.root / record["checkpoint"]
        if digest(path) != record["checkpoint_sha256"]:
            raise RuntimeError("上游检查点内容已经变化，请重新运行对应章节。")
        adata = sc.read_h5ad(path)
        print(f"读取检查点：{record['checkpoint']}\n{adata.n_obs:,} 个细胞 × {adata.n_vars:,} 个基因")
        return adata

    def table(self, name, frame, index=True):
        path = self.tables / (name if name.endswith(".csv") else name + ".csv")
        frame.to_csv(path, index=index, encoding="utf-8-sig")
        return path

    def capture(self, name):
        import matplotlib.pyplot as plt
        for i, number in enumerate(plt.get_fignums()):
            plt.figure(number).savefig(self.figures / f"{name}_{i + 1}.pdf", bbox_inches="tight")

    def annotation_map(self, adata, key, level):
        """先导出当前证据、等待真实确认，再读取映射；不使用固定的教程答案。"""
        return super().annotation_map(adata, key, level)

    def finish(self, adata=None, summary=None, save=True, status="complete"):
        import fcntl
        summary = dict(summary or {})
        if adata is not None:
            if not adata.obs_names.is_unique or not adata.var_names.is_unique:
                raise ValueError("细胞和基因索引必须唯一。")
            summary.update(n_cells=int(adata.n_obs), n_genes=int(adata.n_vars))
        if adata is not None and save:
            path = self.directory / "checkpoint.h5ad"
            temporary = self.directory / "checkpoint.pending.h5ad"
            adata.write_h5ad(temporary, compression="gzip")
            temporary.replace(path)
            self.record.update(checkpoint=relative(path, self.root), checkpoint_sha256=digest(path))
        elif self.spec.get("input"):
            parent = state(self.root)["chapters"][self.spec["input"]]
            self.record.update(checkpoint=parent["checkpoint"], checkpoint_sha256=parent["checkpoint_sha256"])
        self.record.update(status=status, elapsed_seconds=round(time.time() - self.started, 2), summary=summary)
        write_json(self.directory / "summary.json", summary)
        self.record["artifacts"] = inventory(self.directory, self.root)
        self._publish()
        fcntl.flock(self.lock, fcntl.LOCK_UN)
        self.lock.close()
        fcntl.flock(self.environment_lock, fcntl.LOCK_UN)
        self.environment_lock.close()
        print("本章计算完成。请阅读本次图表和表格，再更新本章解读。")


def inventory(directory, root=None):
    return [
        {"path": relative(path, root), "kind": path.suffix.lstrip("."), "bytes": path.stat().st_size}
        for path in sorted(Path(directory).rglob("*"))
        if path.is_file() and path.suffix in (".png", ".pdf", ".csv", ".h5ad", ".ipynb")
        and ".pending." not in path.name and ".history" not in path.parts
    ]


def start_chapter(chapter):
    return Chapter(chapter)


def marker_sets(adata):
    return {
        level: {key: list(value) for key, value in groups.items()}
        for level, groups in adata.uns["course_markers"].items()
    }


def scaled_view(adata, genes):
    import scanpy as sc
    genes = list(dict.fromkeys(g for g in genes if g in adata.var_names))
    if not genes:
        raise ValueError("没有可用于缩放绘图的基因。")
    view = adata[:, genes].copy()
    view.X = view.layers["log1p"].copy()
    sc.pp.scale(view)
    view.layers["scaled"] = view.X.copy()
    view.X = view.layers["log1p"].copy()
    return view
