"""Create a readable report figure from already computed chapter evidence."""
from pathlib import Path
import os
ROOT = Path(os.environ.get("SC_COURSE_ROOT", Path(__file__).resolve().parents[1]))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".runtime/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd


def main():
    # 功能说明：只读取已确认检查点中的 UMAP、标签和分数，不重新拟合模型。
    # 输入参数：--checkpoint 指定 H5AD；--output 由 course redraw 指向暂存图目录。
    # 运行目的：学生可复制本脚本并修改字号/布局，再由 AI 看图、更新本章解读和 Word。
    import argparse
    import scanpy as sc
    parser=argparse.ArgumentParser()
    parser.add_argument('--checkpoint',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    data=sc.read_h5ad(args.checkpoint)
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    merged=data.obs.copy()
    merged[['UMAP1','UMAP2']]=data.obsm['X_umap']
    fine_key=str(data.uns['annotation_keys']['fine'])
    if 'celltypist_conf_score_fine' not in merged:
        raise ValueError('该检查点没有精细模型分数；请为实际存在的手工标签或粗模型改写绘图脚本。')
    # 支持 course redraw 保存到项目后的脚本副本；字体来自环境登记的课程安装位置。
    install=Path(os.environ['SC_COURSE_ROOT'])
    font_manager.fontManager.addfont(str(install / "assets/NotoSansCJKsc-Regular.otf"))
    plt.rcParams.update({"font.family": "Noto Sans CJK SC", "font.size": 10, "axes.unicode_minus": False})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), constrained_layout=True,
                             gridspec_kw={"width_ratios": [1.25, 1]})
    score = merged["celltypist_conf_score_fine"]
    pts = axes[0].scatter(merged.UMAP1, merged.UMAP2, c=score, s=2, cmap="viridis", vmin=0, vmax=1,
                          rasterized=True, linewidths=0)
    axes[0].set(title="精细模型：多数投票标签的置信度", xlabel="UMAP1", ylabel="UMAP2")
    axes[0].set_xticks([]); axes[0].set_yticks([])
    fig.colorbar(pts, ax=axes[0], label="标签置信度", shrink=0.7)
    medians = merged.groupby(fine_key, observed=True)["celltypist_conf_score_fine"].median().sort_values()
    axes[1].barh([str(x) for x in medians.index], medians, color="#337B9B")
    for i, value in enumerate(medians):
        axes[1].text(value + 0.015, i, f"{value:.2f}", va="center", fontsize=8)
    axes[1].set(xlim=(0, 1.17), xlabel="置信度中位数", ylabel="Leiden 簇编号", title="按簇复核预测可靠程度")
    axes[1].set_xticks([0, 0.25, 0.5, 0.75, 1])
    axes[1].spines[["top", "right"]].set_visible(False)
    for suffix in ("png", "pdf"):
        fig.savefig(output / ("report_confidence." + suffix), dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(output / "report_confidence.png")


if __name__ == "__main__":
    main()
