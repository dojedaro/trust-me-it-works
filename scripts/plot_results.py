"""Draw the README chart from the saved traces: final correctness per variant with 95% Wilson intervals.

pip install -e ".[plot]"
python scripts/plot_results.py            # writes assets/final_correct.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from trustme.runner import load_traces, summarize  # noqa: E402

RUN = Path("runs/claude-2026-11-13")
LABELS = {
    "A": "A. Single pass",
    "B": "B. Self-check",
    "C": "C. Separate model\nscores the code",
    "D": "D. Separate model\nwrites tests",
    "E": "E. Hidden-test\nfailures shown",
    "F": "F. D + disputes",
}
COLORS = {"A": "#9aa5b1", "B": "#e0a040"}


def main() -> None:
    rows = {r["variant"]: r for r in summarize(load_traces(RUN))}
    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    for i, v in enumerate(LABELS):
        r = rows[v]
        rate = 100 * r["final_correct_rate"]
        lo, hi = (100 * x for x in r["final_correct_ci"])
        ax.bar(i, rate, 0.6, color=COLORS.get(v, "#1f9d55"))
        ax.errorbar(i, rate, yerr=[[rate - lo], [hi - rate]], color="#333", capsize=4, lw=1)
        ax.text(i, hi + 2, f"{r['final_correct']}/{r['runs']}", ha="center", fontsize=8)
    ax.set_xticks(range(len(LABELS)), list(LABELS.values()), fontsize=8)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Final code correct (%)")
    ax.set_title("Hidden tests on 12 trap tasks x 2 samples; whiskers show 95% Wilson intervals", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = Path("assets/final_correct.png")
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
