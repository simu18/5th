# UIR-2 — Markov models of queueing systems (variant 51/51/30)

## Layout
- `report.tex` → `report.pdf` — the report in Russian. Build: `xelatex report.tex` twice.
- `report_en.tex` → `report_en.pdf` — the same report in English (uses `tex_en/`, `figures_en/`).
- `tex/`, `tex_en/` — tables, matrices and graphs, generated from the model (don't edit; regenerate).
- `figures/`, `figures_en/` — comparison plots (PDF).
- `code/model.py` — both Markov models + all characteristics + Little checks.
- `code/plots.py`, `code/gen_tex.py` — regenerate figures / tables:
  `cd code && python3 plots.py && python3 plots.py en && python3 gen_tex.py && python3 gen_tex.py en`

## Key results (λ = 0.5, b = 10)
| | SYSTEM_1 (2 servers, 2/2) | SYSTEM_2 (1 server E3, 3) |
|---|---|---|
| States | 16 | 13 |
| Throughput λ', 1/s | **0.1890** | 0.1000 |
| Loss probability | 0.6220 | 0.8000 |
| Time in system, s | 25.06 | 37.88 |
Criterion (а) max throughput → **SYSTEM_1**.

## Entering into WinMark (Windows only)
SYSTEM_1 parameters: λ1 = 0.325, λ2 = 0.175, μ = 0.1. 16 states, E(4·n1+n2+1).
SYSTEM_2 parameters: λ = 0.5, 3μ = 0.3. 13 states: E1 = 0, E2..E4 = 1₁..1₃, E5..E7 = 2₁..2₃, E8..E10 = 3₁..3₃, E11..E13 = 4₁..4₃.
Full list of transitions is in the report (section 5). MARK's stationary probabilities must match Form 1.
If you take screenshots, save them as figures/mark_sys1.png and figures/mark_sys2.png
and uncomment the two figure lines in section 6 of report.tex.
