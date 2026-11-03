cd ~/os-course/lab/intro-exp
cat > analyze.py << 'PYEOF'
#!/usr/bin/env python3
"""Analysis for intro-exp, variant Write, Cache, 1M vs 10M, Rand.

Usage: python3 analyze.py data/final_read.csv data/final_mmap.csv
Writes tables to results/ and figures to figures/.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")                      # draw to files, no window needed
import matplotlib.pyplot as plt

K_WARMUP = 2          # first K rounds are discarded (decided before the final run)
CONF = 0.95           # confidence level
E_REL = 0.01          # target CI half-width: 1% of the mean (used to check N)
COLORS = {"1M": "#2a78d6", "10M": "#eb6834"}
SIZES = ["1M", "10M"]
NAMES = {"graph_traverse": "read/lseek/write", "graph_traverse_mmap": "mmap"}

Path("results").mkdir(exist_ok=True)
Path("figures").mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.3})

# load raw data 
df = pd.concat([pd.read_csv(f) for f in sys.argv[1:]], ignore_index=True)
df["ns_per_node"] = df["wall_s"] * 1e9 / (df["nodes"] * df["iter"])
df["status"] = "kept"
df.loc[df["round"] <= K_WARMUP, "status"] = "warmup"

# outliers: 1.5*IQR rule, per configuration, warm-up excluded 
for (prog, size), g in df[df.status == "kept"].groupby(["program", "size"]):
    q1, q3 = g["wall_s"].quantile([0.25, 0.75])
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    bad = g[(g.wall_s < lo) | (g.wall_s > hi)].index
    df.loc[bad, "status"] = "outlier"
df[df.status == "outlier"][["program", "size", "round", "wall_s", "user_s", "sys_s", "ics"]] \
    .to_csv("results/outliers.csv", index=False)


# statistics per configuration 
def describe(x):
    n = len(x)
    mean, sd = x.mean(), x.std(ddof=1)          # ddof=1 -> divide by N-1
    se = sd / np.sqrt(n)
    t = stats.t.ppf(1 - (1 - CONF) / 2, n - 1)  # Student t quantile
    return dict(N=n, mean=mean, sd=sd, se=se, t=t, ci_lo=mean - t * se, ci_hi=mean + t * se,
                ci_half_pct=100 * t * se / mean, median=x.median(),
                iqr=x.quantile(0.75) - x.quantile(0.25),
                N_needed=int(np.ceil((t * sd / (E_REL * mean)) ** 2)))


rows = []
for (prog, size), g in df.groupby(["program", "size"]):
    k = g[g.status == "kept"]
    w, p = describe(k.wall_s), describe(k.ns_per_node)
    rows.append(dict(program=prog, size=size, iter=k.iter.iloc[0], N_total=len(g),
                     N_warmup=(g.status == "warmup").sum(), N_outliers=(g.status == "outlier").sum(),
                     N=w["N"], wall_mean=w["mean"], wall_sd=w["sd"], wall_ci_lo=w["ci_lo"],
                     wall_ci_hi=w["ci_hi"], wall_ci_half_pct=w["ci_half_pct"], wall_median=w["median"],
                     wall_iqr=w["iqr"], ns_node_mean=p["mean"], ns_node_ci_lo=p["ci_lo"],
                     ns_node_ci_hi=p["ci_hi"], user_mean=k.user_s.mean(), sys_mean=k.sys_s.mean(),
                     minflt_mean=k.minflt.mean(), majflt_sum=k.majflt.sum(), vcs_mean=k.vcs.mean(),
                     ics_mean=k.ics.mean(), N_needed_1pct=w["N_needed"],
                     shapiro_p=stats.shapiro(k.wall_s).pvalue,
                     wall_mean_all=g[g.status != "warmup"].wall_s.mean()))
summary = pd.DataFrame(rows)
summary.to_csv("results/summary.csv", index=False)

#compare 1M vs 10M inside each program (Welch t-test)
cmp_rows = []
for prog in summary.program.unique():
    a = df[(df.program == prog) & (df["size"] == "1M") & (df.status == "kept")].ns_per_node
    b = df[(df.program == prog) & (df["size"] == "10M") & (df.status == "kept")].ns_per_node
    res = stats.ttest_ind(b, a, equal_var=False)
    cmp_rows.append(dict(program=prog, ns_1M=a.mean(), ns_10M=b.mean(),
                         diff_pct=100 * (b.mean() / a.mean() - 1),
                         median_diff_pct=100 * (b.median() / a.median() - 1),
                         welch_t=res.statistic, p_value=res.pvalue))
comparison = pd.DataFrame(cmp_rows)
comparison.to_csv("results/comparison.csv", index=False)

pd.set_option("display.width", 200, "display.max_columns", 40)
print(summary[["program", "size", "N", "N_outliers", "wall_mean", "wall_sd", "wall_ci_lo",
               "wall_ci_hi", "wall_ci_half_pct", "wall_median", "ns_node_mean", "user_mean",
               "sys_mean", "N_needed_1pct", "shapiro_p"]].round(4).to_string(index=False))
print()
print(comparison.round(4).to_string(index=False))
print()
print("outliers removed:")
print(pd.read_csv("results/outliers.csv").to_string(index=False))


# 5 figures
def ci_panel(ax, prog):
    s = summary[summary.program == prog].set_index("size").loc[SIZES]
    for i, size in enumerate(SIZES):
        m = s.loc[size, "ns_node_mean"]
        err = m - s.loc[size, "ns_node_ci_lo"]
        ax.errorbar(i, m, yerr=err, fmt="o", ms=8, color=COLORS[size], capsize=6, lw=2)
        ax.annotate(f"{m:.1f} ns", (i, m), xytext=(12, -4), textcoords="offset points")
    ax.set_xticks(range(len(SIZES)), SIZES)
    ax.set_xlim(-0.5, 1.7)
    ax.set_title(NAMES[prog])
    ax.set_ylabel("ns per node (mean, 95% CI)")


# 5a. mean + CI, one panel per program (different scales -> separate charts)
fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
for ax, prog in zip(axes, NAMES):
    ci_panel(ax, prog)
fig.suptitle("Per-node time, 1M vs 10M (--write, warm cache)")
fig.tight_layout()
fig.savefig("figures/ci_ns_per_node.png", dpi=200)

# 5b. layered distribution (histogram + KDE) per program
for prog in NAMES:
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for size in SIZES:
        x = df[(df.program == prog) & (df["size"] == size) & (df.status != "warmup")].ns_per_node
        ax.hist(x, bins=20, density=True, alpha=0.35, color=COLORS[size], label=f"{size} histogram")
        grid = np.linspace(x.min() * 0.97, x.max() * 1.03, 300)
        ax.plot(grid, stats.gaussian_kde(x)(grid), color=COLORS[size], lw=2, label=f"{size} KDE")
    ax.set_xlabel("ns per node")
    ax.set_ylabel("density")
    ax.set_title(f"{NAMES[prog]}: distribution of runs (warm-up excluded, outliers included)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"figures/density_{prog}.png", dpi=200)

# 5c. timeline: every run in execution order (shows warm-up, drift, outliers)
fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
for ax, prog in zip(axes, NAMES):
    for size in SIZES:
        g = df[(df.program == prog) & (df["size"] == size)]
        for st, mk in [("kept", "o"), ("warmup", "s"), ("outlier", "x")]:
            h = g[g.status == st]
            ax.scatter(h["round"], h.wall_s, marker=mk, s=22 if st == "kept" else 45,
                       color=COLORS[size], label=f"{size} {st}" if len(h) else None)
    ax.axvline(K_WARMUP + 0.5, color="gray", ls="--", lw=1)
    ax.set_ylabel("wall, s")
    ax.set_title(NAMES[prog])
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1))
axes[1].set_xlabel("round")
fig.tight_layout()
fig.savefig("figures/timeline.png", dpi=200)

# 5d. stage 3: all four series side by side, relative to each program's 1M mean
fig, ax = plt.subplots(figsize=(7, 3.8))
pos = 0
labels = []
for prog in NAMES:
    base = summary[(summary.program == prog) & (summary["size"] == "1M")].ns_node_mean.iloc[0]
    for size in SIZES:
        r = summary[(summary.program == prog) & (summary["size"] == size)].iloc[0]
        m, lo = r.ns_node_mean / base * 100, r.ns_node_ci_lo / base * 100
        ax.errorbar(pos, m, yerr=m - lo, fmt="o", ms=8, capsize=6, lw=2, color=COLORS[size])
        ax.annotate(f"{r.ns_node_mean:.1f} ns", (pos, m), xytext=(10, -4), textcoords="offset points")
        labels.append(f"{NAMES[prog]}\n{size}")
        pos += 1
ax.axhline(100, color="gray", lw=1, ls=":")
ax.set_xticks(range(pos), labels)
ax.set_xlim(-0.5, pos - 0.2)
ax.set_ylabel("% of the same program's 1M mean")
ax.set_title("All four series: per-node time relative to 1M (95% CI)")
fig.tight_layout()
fig.savefig("figures/all_series_relative.png", dpi=200)
print("\nsaved results/*.csv and figures/*.png")
PYEOF
python3 analyze.py data/final_read.csv data/final_mmap.csv