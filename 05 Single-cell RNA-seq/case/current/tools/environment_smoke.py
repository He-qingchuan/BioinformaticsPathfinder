"""Small computations in a fresh kernel; never starts a teaching chapter."""
from pathlib import Path
import json
import sys

import anndata as ad
import bbknn
import harmonypy
import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse

root, output = Path(sys.argv[1]), Path(sys.argv[2])
# 环境测试使用合成矩阵；缺少研究数据或物种模型不会被误判为环境缺失。
samples = {}

rng = np.random.default_rng(0)
data = ad.AnnData(sparse.csr_matrix(rng.poisson(2, (240, 100)).astype(np.float32)),
                  obs=pd.DataFrame({"samples": ["a"] * 120 + ["b"] * 120},
                                   index=[f"test_{i}" for i in range(240)]))
sc.pp.normalize_total(data, target_sum=10000)
sc.pp.log1p(data)
sc.pp.highly_variable_genes(data, n_top_genes=60)
sc.pp.pca(data, n_comps=20)
sc.pp.neighbors(data, n_neighbors=10, n_pcs=15, random_state=0)
sc.tl.umap(data, random_state=0)
sc.tl.leiden(data, flavor="igraph", directed=False, n_iterations=-1, random_state=0)
harmony = harmonypy.run_harmony(data.obsm["X_pca"], data.obs, ["samples"],
                                max_iter_harmony=3, random_state=0, verbose=False)
if not np.isfinite(harmony.Z_corr).all():
    raise RuntimeError("Harmony 测试出现非有限数值。")
bbknn.bbknn(data, batch_key="samples", n_pcs=15, neighbors_within_batch=3, annoy_n_trees=5)
assert data.obsp["connectivities"].nnz > 0
assert np.isfinite(data.obsm["X_umap"]).all()
font_manager.fontManager.addfont(str(root / "assets/NotoSansCJKsc-Regular.otf"))
plt.rcParams["font.family"] = ["Noto Sans CJK SC", "DejaVu Sans"]
fig, axis = plt.subplots(figsize=(5, 3))
axis.scatter(*data.obsm["X_umap"].T, c=np.arange(240) // 120, s=8)
axis.set(title="环境检查：合成数据", xlabel="UMAP 1", ylabel="UMAP 2")
fig.savefig(output / "smoke.png", dpi=100, bbox_inches="tight")
plt.close(fig)
data.write_h5ad(output / "smoke.h5ad")
assert sc.read_h5ad(output / "smoke.h5ad").shape == (240, 100)
summary = {"python": sys.executable, "samples": samples, "synthetic_shape": list(data.shape),
           "bbknn_edges": data.obsp["connectivities"].nnz,
           "leiden_clusters": int(data.obs["leiden"].nunique()), "harmony": "passed",
           "umap": "passed", "h5ad_roundtrip": "passed"}
if sys.argv[3] == "scvi":
    import scvi
    import torch
    assert torch.isfinite(torch.ones(2, 2) @ torch.ones(2, 2)).all()
    summary["scvi"] = {"version": scvi.__version__, "check": "import and CPU tensor only; no training"}
(output / "smoke.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False, indent=2))
