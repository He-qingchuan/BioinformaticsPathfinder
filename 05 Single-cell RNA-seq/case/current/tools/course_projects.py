"""项目目录与输入材料。

功能说明：将课程安装位置与每次研究的工作目录分开。
运行目的：课件可以独立修改，输入、决定、检查点和报告不会串到另一项目。
数据流程：公共模板 → 项目副本；用户材料 → 输入核查 → 当前章节。
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import uuid


def installation():
    """返回软件、环境和模板所在位置；不使用当前研究项目来寻找 Conda。"""
    return Path(__file__).resolve().parents[1]


def resolve_project(name=None, required=True):
    """从显式编号或项目内工作目录确定项目；不设置共享的‘当前项目’指针。"""
    course = installation()
    name = name or os.environ.get("SC_COURSE_PROJECT")
    if name:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
            raise ValueError("项目编号须为 1–64 位字母、数字、下划线或短横线；中文名称另存 name。")
        root = course / "projects" / name
        if not (root / "project.json").is_file():
            raise ValueError(f"项目不存在：{name}。先执行 course project create。")
        return root
    for root in [Path.cwd(), *Path.cwd().parents]:
        if (root / "project.json").is_file() and root.parent == course / "projects":
            return root
    if required:
        raise ValueError("请指定 --project 项目编号；可执行 course project list 查看。公共课件是模板，请运行项目内副本。")
    return None


def descriptor(root):
    """读取 AI 根据对话整理的项目说明；配置中的路径均相对于此项目。"""
    return json.loads((Path(root) / "project.json").read_text(encoding="utf-8"))


def input_path(root, value):
    """解析材料路径；允许引用随包示例，要求材料留在整个课程包内以便迁移。"""
    path = (Path(root) / value).resolve()
    if not path.is_relative_to(installation().resolve()):
        raise ValueError(f"请将材料放到本项目 inputs 再登记相对路径：{value}")
    return path


def config_digest(root, chapter):
    """只校验本章消费的配置；填写项目名称、模型信息不应使导入结果过期。"""
    data = descriptor(root) if (root / "project.json").exists() else json.loads((root / "config/course.json").read_text())
    keys = {
        "00": ["id", "uuid"], "01": ["samples"],
        "02": ["species", "assay", "qc"], "03": [], "04": [], "05": ["batch_key"],
        "06": [], "07": ["markers"], "08": ["annotation_extra_genes"], "09": ["subcluster"],
        "10": ["comparison"], "11": ["models", "species", "tissue", "assay"], "12": [], "E01": ["exercise_mtx"], "E02": [],
    }.get(chapter, [])
    parameter_keys = {
        "02": ["min_genes", "min_cells"], "03": ["n_top_genes"], "04": ["n_pcs"],
        "05": ["n_pcs"], "06": ["resolutions"], "E02": ["scvi_epochs"],
    }.get(chapter, []) + ["random_seed", "threads"]
    value = {key: data.get(key) for key in keys}
    value["parameters"] = {key: data["parameters"].get(key) for key in parameter_keys}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def create_project(identifier, name, preset="custom"):
    """创建轻量课件副本。tutorial 引用只读示例输入；custom 留空并等待真实资料。"""
    from course_runtime import read_json, write_json
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", identifier):
        raise ValueError("非法项目编号。")
    root = installation() / "projects" / identifier
    if root.exists():
        raise FileExistsError(f"项目已经存在，不覆盖：{root}")
    config = copy.deepcopy(read_json(installation() / "config/course.json"))
    data = {**config, "schema": 3, "id": identifier, "uuid": uuid.uuid4().hex,
            "name": name, "preset": preset, "species": "", "tissue": "", "assay": "",
            "samples": {}, "markers": "", "models": [], "batch_key": "samples",
            "qc": {"gene_sets": {}, "mt_cutoff": 20, "general_mads": 5, "mt_mads": 3},
            "subcluster": {"group": "", "resolution": 0.05},
            "comparison": {"group": "", "reference": "", "question": "", "plot_clusters": []},
            "annotation_extra_genes": [],
            "adaptation": {"confirmed": False, "note": "请按 99 指南核对物种、基因编号、质控和材料。"}}
    if preset == "tutorial":
        prefix = "../tutorial_example/inputs/"
        data.update(species="Homo sapiens", tissue="骨髓", assay="10x scRNA UMI")
        data["samples"] = {sid: {"path": prefix + "data/h5/" + filename,
                                "format": "10x_h5", "capture_library": sid, "counts_confirmed": True}
                           for sid, filename in config["samples"].items()}
        data["markers"] = prefix + "markers.json"
        data["annotation_extra_genes"] = ["CD34", "CD3D", "TRAC"]
        data["models"] = [{"name": role, "path": prefix + "models/" + filename,
                           "species": "Homo sapiens", "tissue": "跨组织免疫细胞", "source": "https://www.celltypist.org/models"}
                          for role, filename in [("coarse", "Immune_All_High.pkl"), ("fine", "Immune_All_Low.pkl")]]
        data["qc"]["gene_sets"] = {"mt": {"prefixes": ["MT-"]}, "ribo": {"prefixes": ["RPS", "RPL"]},
                                     "hb": {"regex": "^HB[^(P)]"}}
        data["subcluster"]["group"] = "B_cells"
        data["comparison"].update(group="B_cells", reference="T_NK_ILCs", question="比较 B 细胞与 T/NK/ILC 的描述性标记差异，供教学核对细胞类型。", plot_clusters=["2", "11"])
        data["adaptation"] = {"confirmed": True, "note": "教程预设；运行中仍需确认 QC、整合、分辨率、注释和模型。"}
    root.mkdir(parents=True)
    (root / "inputs").mkdir()
    (root / "results").mkdir()
    (root / "reports/sections").mkdir(parents=True)
    shutil.copytree(installation() / "notebooks", root / "notebooks", ignore=shutil.ignore_patterns("README.md"))
    shutil.copytree(installation() / "exercises", root / "notebooks/exercises", ignore=shutil.ignore_patterns("README.md"))
    for ch in data["chapters"]:
        if ch["notebook"].startswith("exercises/"):
            ch["notebook"] = "notebooks/" + ch["notebook"]
    data["exercise_mtx"] = {sid: "../tutorial_example/inputs/data/mtx/" + sid for sid in ["F30", "M66"]}
    write_json(root / "project.json", data)
    write_json(root / "results/state.json", {"chapters": {}})
    print(f"已创建：{root}\n材料统一放入 inputs；请按 99 指南完成本项目输入核查。")
    return root


def input_issues(root, chapter="01"):
    """按阶段列出缺失材料；缺模型仅阻塞模型步骤，缺计数则阻塞数据导入。"""
    p = descriptor(root)
    issues = []
    if chapter == "00":
        return issues
    if chapter == "E01":
        return [f"练习材料缺失：{sid}" for sid,path in p.get("exercise_mtx",{}).items() if not input_path(root,path).is_dir()]
    if not p.get("samples"):
        issues.append("尚未登记 samples；请提供表达计数文件和样本对应关系。")
    for sid, sample in p.get("samples", {}).items():
        try:
            path = input_path(root, sample["path"])
            if not path.exists():
                issues.append(f"样本 {sid} 文件不存在：{sample['path']}")
        except (KeyError, ValueError) as exc:
            issues.append(f"样本 {sid} 路径需要补充：{exc}")
        if not sample.get("counts_confirmed"):
            issues.append(f"样本 {sid} 需确认原始计数来源；整数值本身不能证明未归一化。")
        if sample.get("format") not in {"10x_h5", "10x_mtx", "h5ad"}:
            issues.append(f"样本 {sid} 需登记 format：10x_h5、10x_mtx 或 h5ad。")
    if chapter not in {"01", "E01"}:
        for key in ("species", "tissue", "assay"):
            if not p.get(key):
                issues.append(f"请补充 {key}。")
        if not p.get("adaptation", {}).get("confirmed"):
            issues.append("请核对本项目课件与物种/组织/测序方式，完成 adaptation 记录后再继续。")
    if chapter == "02":
        for sid, sample in p.get("samples", {}).items():
            if not sample.get("capture_library"):
                issues.append(f"样本 {sid} 缺 capture_library；请确认哪些细胞来自同一次捕获文库。")
    if chapter == "07" and (not p.get("markers") or not input_path(root, p["markers"]).is_file()):
        issues.append("缺少适配的 markers 标记资源；请先检查基因编号、查找来源并与用户确认。")
    if chapter == "11":
        if not p.get("models"):
            issues.append("尚未登记适配模型；先检索官方目录并建议下载/用户提供/跳过。")
        for m in p.get("models", []):
            if not m.get("path") or not input_path(root, m["path"]).is_file():
                issues.append(f"缺少模型文件：{m.get('name', '')}。先检索模型目录，再询问用户。")
            if m.get("species") != p.get("species"):
                issues.append(f"模型 {m.get('name')} 物种与项目不同；需要独立适配与证据，不能直接应用。")
    return issues


def read_sample(root, sample):
    """导入已确认的原始 RNA 计数，保留基因编号；不根据文件扩展名猜测归一化状态。"""
    import anndata as ad
    import numpy as np
    import pandas as pd
    import scanpy as sc
    from scipy import sparse
    path = input_path(root, sample["path"])
    fmt = sample["format"]
    if fmt == "10x_h5":
        data = sc.read_10x_h5(path, genome=sample.get("genome"), gex_only=True)
    elif fmt == "10x_mtx":
        # Scanpy 1.11.5 的 v3 读取器要求 gzip；未压缩矩阵直接由 SciPy 读取，避免改动原材料。
        if (path / "matrix.mtx.gz").exists() or (path / "genes.tsv").exists():
            data = sc.read_10x_mtx(path, var_names=sample.get("gene_index", "gene_symbols"), cache=False)
        else:
            from scipy.io import mmread
            genes = pd.read_csv(path / "features.tsv", sep="\t", header=None, dtype=str)
            cells = pd.read_csv(path / "barcodes.tsv", sep="\t", header=None, dtype=str)
            data = ad.AnnData(sparse.csr_matrix(mmread(path / "matrix.mtx").T),
                              obs=pd.DataFrame(index=cells[0].to_numpy()),
                              var=pd.DataFrame({"gene_ids": genes[0].values, "gene_symbols": genes[1].values}, index=genes[1].to_numpy()))
            if genes.shape[1] > 2:
                data = data[:, (genes[2] == "Gene Expression").values].copy()
    elif fmt == "h5ad":
        data = ad.read_h5ad(path)
        layer = sample.get("counts_layer")
        if not layer:
            raise ValueError("H5AD 必须指定 counts_layer：X、raw 或具体 layers 名称。")
        if layer == "raw":
            if data.raw is None:
                raise ValueError("H5AD 没有 raw；请确认真实计数保存位置。")
            data = data.raw.to_adata()
        elif layer != "X":
            data.X = data.layers[layer].copy()
        data.uns.clear(); data.obsm.clear(); data.obsp.clear(); data.layers.clear(); data.raw = None
    else:
        raise ValueError("不支持的输入格式；请先转换到计数矩阵并登记。")
    data.X = sparse.csr_matrix(data.X)
    values = data.X.data
    if not data.n_obs or not data.n_vars or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("表达矩阵为空，或包含负数/非有限值。")
    if not np.allclose(values, np.rint(values), rtol=0, atol=1e-6):
        raise ValueError("本课程从原始计数开始；检测到非整数，请先核查计数来源。")
    data.var_names = data.var_names.astype(str)
    data.var_names_make_unique()
    return data


def external_files(root, chapter):
    """列出本章真正读取的材料，用内容校验绑定输入，而非扫描整个共享数据目录。"""
    p = descriptor(root); paths = []
    if chapter == "01":
        paths = [input_path(root, s["path"]) for s in p.get("samples",{}).values() if s.get("path")]
    elif chapter == "07" and p.get("markers"):
        paths = [input_path(root, p["markers"])]
    elif chapter == "11":
        paths = [input_path(root, m["path"]) for m in p.get("models", []) if m.get("path")]
    elif chapter == "02":
        paths = [input_path(root, v["file"]) for v in p.get("qc", {}).get("gene_sets", {}).values() if isinstance(v, dict) and v.get("file")]
    elif chapter == "E01":
        paths = [input_path(root, v) for v in p.get("exercise_mtx", {}).values()]
    return sorted({f for path in paths for f in (path.rglob('*') if path.is_dir() else [path]) if f.is_file()})
