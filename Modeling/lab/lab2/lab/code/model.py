"""UIR-2, variant 51/51/30: Markov models of two queueing systems.
SYSTEM_1: 2 exponential servers, separate buffers 2/2, routing q1=0.65, q2=0.35.
SYSTEM_2: 1 server with Erlang-3 service, buffer 3.
Load (group 30): lambda=0.5 1/s, b=10 s.
"""
import numpy as np

LAM, B = 0.5, 10.0
Q1, Q2 = 0.65, 0.35          # P2 = 0.2 + 0.15 for a two-server system
K1 = K2 = 2                  # buffer sizes of SYSTEM_1
K = 3                        # shared buffer of SYSTEM_2
ERL = 3                      # Erlang order

def stationary(G):
    """Solve p G = 0, sum p = 1 (G with diagonal = -row sums)."""
    n = G.shape[0]
    A = G.T.copy()
    A[-1, :] = 1.0
    rhs = np.zeros(n); rhs[-1] = 1.0
    return np.linalg.solve(A, rhs)

def finalize(G):
    np.fill_diagonal(G, 0.0)
    np.fill_diagonal(G, -G.sum(axis=1))
    return G

# ---------------- SYSTEM_1 ----------------
def sys1_states(k1=K1, k2=K2):
    return [(a, c) for a in range(k1 + 2) for c in range(k2 + 2)]

def sys1(lam=LAM, b=B, q1=Q1, k1=K1, k2=K2):
    mu = 1 / b; l1, l2 = q1 * lam, (1 - q1) * lam
    S = sys1_states(k1, k2); idx = {s: i for i, s in enumerate(S)}
    G = np.zeros((len(S), len(S)))
    sym = [["" for _ in S] for _ in S]
    for (a, c), i in idx.items():
        if a < k1 + 1: G[i, idx[(a + 1, c)]] += l1; sym[i][idx[(a + 1, c)]] = r"\lambda_1"
        if c < k2 + 1: G[i, idx[(a, c + 1)]] += l2; sym[i][idx[(a, c + 1)]] = r"\lambda_2"
        if a > 0:      G[i, idx[(a - 1, c)]] += mu; sym[i][idx[(a - 1, c)]] = r"\mu"
        if c > 0:      G[i, idx[(a, c - 1)]] += mu; sym[i][idx[(a, c - 1)]] = r"\mu"
    G = finalize(G); p = stationary(G)
    P = dict(zip(S, p))
    r = {}
    r["y"] = [l1 * b, l2 * b]
    r["rho"] = [sum(v for (a, c), v in P.items() if a > 0), sum(v for (a, c), v in P.items() if c > 0)]
    r["l"] = [sum(max(a - 1, 0) * v for (a, c), v in P.items()), sum(max(c - 1, 0) * v for (a, c), v in P.items())]
    r["m"] = [sum(a * v for (a, c), v in P.items()), sum(c * v for (a, c), v in P.items())]
    r["pi"] = [sum(v for (a, c), v in P.items() if a == k1 + 1), sum(v for (a, c), v in P.items() if c == k2 + 1)]
    r["thr"] = [l1 * (1 - r["pi"][0]), l2 * (1 - r["pi"][1])]
    r["w"] = [r["l"][i] / r["thr"][i] for i in range(2)]
    r["u"] = [r["m"][i] / r["thr"][i] for i in range(2)]
    T = {}
    T["y"] = sum(r["y"]); T["rho"] = sum(r["rho"]) / 2; T["R"] = sum(r["rho"])
    T["l"] = sum(r["l"]); T["m"] = sum(r["m"]); T["thr"] = sum(r["thr"])
    T["pi"] = 1 - T["thr"] / lam
    T["w"] = T["l"] / T["thr"]; T["u"] = T["m"] / T["thr"]
    # checks (Little etc.)
    chk = {
        "thr_vs_rho/b": [(r["thr"][i], r["rho"][i] / b) for i in range(2)],
        "m=l+rho": [(r["m"][i], r["l"][i] + r["rho"][i]) for i in range(2)],
        "u=w+b": [(r["u"][i], r["w"][i] + b) for i in range(2)],
        "pi_total=q1pi1+q2pi2": (T["pi"], q1 * r["pi"][0] + (1 - q1) * r["pi"][1]),
    }
    return dict(S=S, G=G, sym=sym, p=p, per=r, tot=T, chk=chk)

# ---------------- SYSTEM_2 ----------------
def sys2_states(k=K, e=ERL):
    return [(0, 0)] + [(n, j) for n in range(1, k + 2) for j in range(1, e + 1)]

def sys2(lam=LAM, b=B, k=K, e=ERL):
    nu = e / b                      # phase rate
    S = sys2_states(k, e); idx = {s: i for i, s in enumerate(S)}
    G = np.zeros((len(S), len(S)))
    sym = [["" for _ in S] for _ in S]
    for (n, j), i in idx.items():
        if n == 0:
            G[i, idx[(1, 1)]] += lam; sym[i][idx[(1, 1)]] = r"\lambda"; continue
        if n < k + 1: G[i, idx[(n + 1, j)]] += lam; sym[i][idx[(n + 1, j)]] = r"\lambda"
        if j < e:     G[i, idx[(n, j + 1)]] += nu; sym[i][idx[(n, j + 1)]] = r"%d\mu" % e
        else:
            t = (0, 0) if n == 1 else (n - 1, 1)
            G[i, idx[t]] += nu; sym[i][idx[t]] = r"%d\mu" % e
    G = finalize(G); p = stationary(G)
    P = dict(zip(S, p))
    r = {}
    r["y"] = lam * b
    r["rho"] = 1 - P[(0, 0)]; r["R"] = r["rho"]
    r["l"] = sum(max(n - 1, 0) * v for (n, j), v in P.items())
    r["m"] = sum(n * v for (n, j), v in P.items())
    r["pi"] = sum(v for (n, j), v in P.items() if n == k + 1)
    r["thr"] = lam * (1 - r["pi"])
    r["w"] = r["l"] / r["thr"]; r["u"] = r["m"] / r["thr"]
    chk = {
        "thr_vs_rho/b": (r["thr"], r["rho"] / b),
        "thr_vs_phase3": (r["thr"], nu * sum(v for (n, j), v in P.items() if j == e)),
        "m=l+rho": (r["m"], r["l"] + r["rho"]),
        "u=w+b": (r["u"], r["w"] + b),
    }
    return dict(S=S, G=G, sym=sym, p=p, per=r, tot=r, chk=chk)

if __name__ == "__main__":
    np.set_printoptions(linewidth=200, precision=4, suppress=True)
    s1, s2 = sys1(), sys2()
    for name, s in (("SYSTEM_1", s1), ("SYSTEM_2", s2)):
        print("=" * 20, name, len(s["S"]), "states")
        for st, v in zip(s["S"], s["p"]): print(st, f"{v:.6f}")
        print("sum p =", s["p"].sum(), " max|pG| =", np.abs(s["p"] @ s["G"]).max())
        print("per:", s["per"]); print("tot:", s["tot"]); print("chk:", s["chk"])
    print("SYSTEM_2 with exponential service (E1):", sys2(e=1)["tot"])
