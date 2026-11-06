"""Plot nominal build responses from ../results/ac_<build>.csv (written by run_all.py)."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, os
fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
for b, c in zip("ABC", ["#1f5fa8", "#c2571a", "#3a8a3a"]):
    fn = f"../results/ac_{b}.csv"
    if not os.path.exists(fn): continue
    a = np.loadtxt(fn, delimiter=",", skiprows=1)
    ax[0].semilogx(a[:, 0], a[:, 1], color=c, label=f"S21 build {b}")
    if b == "A":
        for col, lab, ls in [(2, "S11", "-"), (3, "S22", "--"), (4, "port 2 -> port 3", "-."), (5, "port 2 -> input", ":")]:
            ax[1].semilogx(a[:, 0], a[:, col], ls, color="#333", label=lab + " (A)")
ax[0].set_ylim(-60, 8); ax[0].axvspan(1e4, 50e6, color="#eee"); ax[0].grid(True, which="both", alpha=.3); ax[0].legend(); ax[0].set_ylabel("dB")
ax[1].set_ylim(-130, 0); ax[1].grid(True, which="both", alpha=.3); ax[1].legend(fontsize=8); ax[1].set_ylabel("dB"); ax[1].set_xlabel("Hz")
ax[0].set_title("Rev B simulated response (nominal parts, 50-ohm terminations) - simulation, not measurement")
plt.tight_layout(); plt.savefig("../results/response.png", dpi=110)
