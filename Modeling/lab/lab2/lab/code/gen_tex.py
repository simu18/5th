"""Generate LaTeX fragments (tables, matrices, graphs) from the model."""
import sys
import numpy as np
from model import sys1, sys2, LAM, B, Q1, Q2
LANG = sys.argv[1] if len(sys.argv) > 1 else "ru"     # "ru" -> tex/, "en" -> tex_en/
s1, s2 = sys1(), sys2()
out = "../tex/" if LANG == "ru" else "../tex_en/"
DEC = "{,}" if LANG == "ru" else "."
def f(x, d=4): return f"{x:.{d}f}".replace(".", DEC)
EN = {"Нагрузка": "Offered load", "Загрузка": "Utilization", "Длина очереди": "Queue length",
      "Число заявок": "Requests in system", "Время ожидания": "Waiting time", "Время пребывания": "Time in system",
      "Вероятность потери": "Loss probability", "Произво\\-дитель\\-ность": "Throughput",
      "Интенс. потерь": "Loss rate", "Ср. число раб. приборов": "Mean busy servers",
      "Сумм.": "Total", "П1": "S1", "П2": "S2", "(С1)": "(Sys1)", "(С2)": "(Sys2)", "П (С2)": "S (Sys2)",
      ", с": ", s", "1/с": "1/s"}
def tr(t):
    if LANG == "ru": return t
    for k in sorted(EN, key=len, reverse=True): t = t.replace(k, EN[k])
    return t

def lab1(s): return f"({s[0]},{s[1]})"
def lab2(s): return "0" if s == (0, 0) else f"{s[0]}_{{{s[1]}}}"

# ---------- Form 1 ----------
rows = []
for i in range(max(len(s1["S"]), len(s2["S"]))):
    a = (f"$E_{{{i+1}}}$: ${lab1(s1['S'][i])}$", f(s1["p"][i], 6)) if i < len(s1["S"]) else ("", "")
    b = (f"$E_{{{i+1}}}$: ${lab2(s2['S'][i])}$", f(s2["p"][i], 6)) if i < len(s2["S"]) else ("", "")
    rows.append(f"{i+1} & {a[0]} & {a[1]} & {b[0]} & {b[1]} \\\\")
rows.append(r"\hline $\sum$ & & " + f(s1['p'].sum(), 6) + " & & " + f(s2['p'].sum(), 6) + r" \\")
open(out + "form1.tex", "w").write("\n".join(rows))

# ---------- G matrices (numeric, blanks for zero) ----------
def gmat(s, lab, fname, d=3):
    n = len(s["S"])
    hdr = " & ".join(f"$E_{{{j+1}}}$" for j in range(n))
    lines = [r"\begin{tabular}{c|" + "c" * n + "}", r" & " + hdr + r" \\ \hline"]
    for i in range(n):
        cells = []
        for j in range(n):
            v = s["G"][i, j]
            cells.append("" if abs(v) < 1e-12 else (r"\textbf{" + f(v, d) + "}" if i == j else f(v, d)))
        lines.append(f"$E_{{{i+1}}}$ & " + " & ".join(cells) + r" \\")
    lines.append(r"\end{tabular}")
    open(out + fname, "w").write("\n".join(lines))
gmat(s1, lab1, "G1.tex"); gmat(s2, lab2, "G2.tex")

# ---------- transition lists (for entering into MARK) ----------
def tlist(s, lab, fname):
    items = []
    n = len(s["S"])
    for i in range(n):
        for j in range(n):
            if i != j and s["G"][i, j] > 0:
                items.append(f"$E_{{{i+1}}}\\to E_{{{j+1}}}$: ${s['sym'][i][j]}={f(s['G'][i,j],3)}$")
    open(out + fname, "w").write(r"\begin{multicols}{4}\footnotesize" + "\n" + r"\\".join(items) + "\n" + r"\end{multicols}")
tlist(s1, lab1, "T1.tex"); tlist(s2, lab2, "T2.tex")

# ---------- Form 2 ----------
p1, t1, p2 = s1["per"], s1["tot"], s2["tot"]
def row(name, f1, f2, v1, v2, d=4):
    return (name, f1, f2, v1, v2, d)
D = []
D.append(("Нагрузка $y$", [
  ("П1", r"$y_1=q_1\lambda b$", r"$y=\lambda b$", p1["y"][0], p2["y"]),
  ("П2", r"$y_2=q_2\lambda b$", "--", p1["y"][1], None),
  ("Сумм.", r"$Y=y_1+y_2$", r"$Y=y$", t1["y"], p2["y"])]))
D.append(("Загрузка $\\rho$", [
  ("П1", r"$\rho_1=\sum\limits_{n_1>0}p$", r"$\rho=1-p_0$", p1["rho"][0], p2["rho"]),
  ("П2", r"$\rho_2=\sum\limits_{n_2>0}p$", "--", p1["rho"][1], None),
  ("Сумм.", r"$\rho=(\rho_1+\rho_2)/2$", r"$\rho$", t1["rho"], p2["rho"]),
  ("Ср. число раб. приборов", r"$R=\rho_1+\rho_2$", r"$R=\rho$", t1["R"], p2["R"])]))
D.append(("Длина очереди $l$", [
  ("П1", r"$l_1=\sum (n_1-1)^{+}p$", r"$l=\sum (n-1)^{+}p$", p1["l"][0], p2["l"]),
  ("П2", r"$l_2=\sum (n_2-1)^{+}p$", "--", p1["l"][1], None),
  ("Сумм.", r"$L=l_1+l_2$", r"$L=l$", t1["l"], p2["l"])]))
D.append(("Число заявок $m$", [
  ("П1", r"$m_1=\sum n_1 p$", r"$m=\sum n p$", p1["m"][0], p2["m"]),
  ("П2", r"$m_2=\sum n_2 p$", "--", p1["m"][1], None),
  ("Сумм.", r"$M=m_1+m_2$", r"$M=m$", t1["m"], p2["m"])]))
D.append(("Время ожидания $w$, с", [
  ("П1", r"$w_1=l_1/\lambda'_1$", r"$w=l/\lambda'$", p1["w"][0], p2["w"]),
  ("П2", r"$w_2=l_2/\lambda'_2$", "--", p1["w"][1], None),
  ("Сумм.", r"$W=L/\Lambda'$", r"$W=w$", t1["w"], p2["w"])]))
D.append(("Время пребывания $u$, с", [
  ("П1", r"$u_1=m_1/\lambda'_1$", r"$u=m/\lambda'$", p1["u"][0], p2["u"]),
  ("П2", r"$u_2=m_2/\lambda'_2$", "--", p1["u"][1], None),
  ("Сумм.", r"$U=M/\Lambda'$", r"$U=u$", t1["u"], p2["u"])]))
D.append(("Вероятность потери $\\pi$", [
  ("П1", r"$\pi_1=\sum\limits_{n_1=3}p$", r"$\pi=\sum\limits_{n=4}p$", p1["pi"][0], p2["pi"]),
  ("П2", r"$\pi_2=\sum\limits_{n_2=3}p$", "--", p1["pi"][1], None),
  ("Сумм.", r"$\pi=1-\Lambda'/\lambda$", r"$\pi$", t1["pi"], p2["pi"])]))
D.append(("Произво\\-дитель\\-ность $\\lambda'$, 1/с", [
  ("П1", r"$\lambda'_1=q_1\lambda(1-\pi_1)$", r"$\lambda'=\lambda(1-\pi)$", p1["thr"][0], p2["thr"]),
  ("П2", r"$\lambda'_2=q_2\lambda(1-\pi_2)$", "--", p1["thr"][1], None),
  ("Сумм.", r"$\Lambda'=\lambda'_1+\lambda'_2$", r"$\Lambda'=\lambda'$", t1["thr"], p2["thr"])]))
D.append(("Интенс. потерь $\\lambda''$, 1/с", [
  ("Сумм.", r"$\lambda''=\lambda-\Lambda'$", r"$\lambda''=\lambda\pi$", LAM - t1["thr"], LAM * p2["pi"])]))
lines = []
for name, rs in D:
    for k, (dev, F1, F2, v1, v2) in enumerate(rs):
        first = (r"\multirow{%d}{=}{%s}" % (len(rs), name) if len(rs) > 1 else name) if k == 0 else ""
        dd = 5 if "Загрузка" in name else 4
        lines.append(f"{tr(first)} & {tr(dev)} & {F1} & {F2} & {f(v1,dd)} & {'--' if v2 is None else f(v2,dd)} \\\\")
    lines.append(r"\hline")
open(out + "form2.tex", "w").write("\n".join(lines))

# ---------- Little / balance checks ----------
c1, c2 = s1["chk"], s2["chk"]
L = []
for i in range(2):
    L.append(tr(f"П{i+1} (С1)") + f" & {f(p1['thr'][i],6)} & {f(p1['rho'][i]/B,6)} & {f(p1['u'][i],4)} & {f(p1['w'][i]+B,4)} & {f(p1['m'][i],4)} & {f(p1['l'][i]+p1['rho'][i],4)}\\\\")
L.append(tr("П (С2)") + f" & {f(p2['thr'],6)} & {f(p2['rho']/B,6)} & {f(p2['u'],4)} & {f(p2['w']+B,4)} & {f(p2['m'],4)} & {f(p2['l']+p2['rho'],4)}\\\\")
open(out + "checks.tex", "w").write("\n".join(L))

def sci(x):
    e=int(np.floor(np.log10(x))); return f"{x/10**e:.1f}".replace(".",DEC)+r"\cdot10^{%d}"%e
# ---------- macros with key numbers ----------
M = {
 "SoneThr": f(t1["thr"]), "StwoThr": f(p2["thr"]), "Ratio": f(t1["thr"]/p2["thr"], 2),
 "SonePi": f(t1["pi"]), "StwoPi": f(p2["pi"]), "SoneU": f(t1["u"], 2), "StwoU": f(p2["u"], 2),
 "SoneL": f(t1["l"], 3), "StwoL": f(p2["l"], 3), "SoneRho": f(t1["rho"]), "StwoRho": f(p2["rho"],5),
 "SoneR": f(t1["R"]), "SoneThrA": f(p1["thr"][0]), "SoneThrB": f(p1["thr"][1]),
 "SonePiA": f(p1["pi"][0]), "SonePiB": f(p1["pi"][1]),
 "StwoExpThr": f(sys2(e=1)["tot"]["thr"]), "StwoExpU": f(sys2(e=1)["tot"]["u"], 2),
 "SoneSymThr": f(sys1(q1=0.5)["tot"]["thr"]),
 "SoneZero": f(s1["p"][0], 6), "StwoZero": f(s2["p"][0], 6),
 "SoneFull": f(s1["p"][-1], 6), "StwoFullSum": f(p2["pi"]),
 "SoneMaxRes": sci(np.abs(s1['p']@s1['G']).max()), "StwoMaxRes": sci(np.abs(s2['p']@s2['G']).max()),
}
open(out + "numbers.tex", "w").write("\n".join(r"\newcommand{\%s}{%s}" % (k, v) for k, v in M.items()))
print(M)
