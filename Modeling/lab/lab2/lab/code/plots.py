import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys
from model import sys1, sys2, LAM, Q1
LANG = sys.argv[1] if len(sys.argv) > 1 else "ru"
OUT = "../figures/" if LANG == "ru" else "../figures_en/"
EN = {"Производительность λ', 1/с": "Throughput λ', 1/s", "Вероятность потери π": "Loss probability π",
      "Загрузка системы ρ": "Utilization ρ", "Время пребывания u, с": "Time in system u, s",
      "Суммарная длина очередей L": "Total queue length L", "Число заявок в системе M": "Requests in system M",
      "Интенсивность входящего потока λ, 1/с": "Arrival rate λ, 1/s", "СИСТЕМА_1": "SYSTEM_1", "СИСТЕМА_2": "SYSTEM_2",
      "Вероятность направления заявки к П1 (СИСТЕМА_1)": "Probability q1 of routing to server 1 (SYSTEM_1)",
      " λ = 0,5": " λ = 0.5", " q1 = 0,65": " q1 = 0.65"}
T = (lambda t: EN.get(t, t)) if LANG == "en" else (lambda t: t)

C1, C2 = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e2dc",
                     "grid.linewidth": 0.6, "axes.edgecolor": "#8a897f", "legend.frameon": False})
lams = np.linspace(0.01, 1.0, 100)
R1 = [sys1(lam=l)["tot"] for l in lams]; R2 = [sys2(lam=l)["tot"] for l in lams]
specs = [("thr", T("Производительность λ', 1/с"), "thr"),
         ("pi", T("Вероятность потери π"), "loss"),
         ("rho", T("Загрузка системы ρ"), "rho"),
         ("u", T("Время пребывания u, с"), "u"),
         ("l", T("Суммарная длина очередей L"), "queue"),
         ("m", T("Число заявок в системе M"), "m")]
for key, ylabel, fname in specs:
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    ax.plot(lams, [r[key] for r in R1], color=C1, lw=2, label=T("СИСТЕМА_1"))
    ax.plot(lams, [r[key] for r in R2], color=C2, lw=2, ls="--", label=T("СИСТЕМА_2"))
    ax.axvline(LAM, color="#8a897f", lw=1, ls=":")
    ax.text(LAM, ax.get_ylim()[1], T(" λ = 0,5"), va="top", ha="left", fontsize=8, color="#55544c")
    ax.set_xlabel(T("Интенсивность входящего потока λ, 1/с")); ax.set_ylabel(ylabel)
    ax.legend(fontsize=9, loc="best"); fig.tight_layout(); fig.savefig(f"{OUT}{fname}.pdf"); plt.close(fig)

# routing probability sweep for SYSTEM_1
qs = np.linspace(0.05, 0.95, 91)
thr = [sys1(q1=q)["tot"]["thr"] for q in qs]
fig, ax = plt.subplots(figsize=(5.2, 3.3))
ax.plot(qs, thr, color=C1, lw=2, label=T("СИСТЕМА_1"))
ax.axhline(sys2()["tot"]["thr"], color=C2, lw=2, ls="--", label=T("СИСТЕМА_2"))
ax.axvline(Q1, color="#8a897f", lw=1, ls=":"); ax.text(Q1, 0.125, T(" q1 = 0,65"), fontsize=8, color="#55544c")
ax.set_xlabel(T("Вероятность направления заявки к П1 (СИСТЕМА_1)")); ax.set_ylabel(T("Производительность λ', 1/с"))
ax.set_ylim(0.09, 0.2); ax.legend(fontsize=9, loc="center left", bbox_to_anchor=(0.02,0.35)); fig.tight_layout(); fig.savefig(OUT + "routing.pdf"); plt.close(fig)
print("max thr S1 at q1 =", qs[int(np.argmax(thr))], max(thr))
