"""Draw the figures of REPORT.md from the summary data in docs/data/.

    python scripts/make_report_figures.py          # writes docs/figures/fig1..3.png

Needs matplotlib (`pip install matplotlib`); nothing else beyond the standard library.

Figure 1  Experiment 1: net shift per model and arm, with 95% bootstrap intervals.
Figure 2  Experiment 2: mean probability on the professor's answer after each turn, in both orders.
Figure 3  Both experiments: movement under "Are you sure?" against the order effect.

Figures 1 and 3 read docs/data/exp1-v2-main-2026-11-15.json and docs/data/exp2-main-2026-11-15.json.
The per-turn values of Figure 2 are not in the summary JSON; they are copied from the table
"mean probability on the expert's answer after each turn" in docs/experiment2-results.md.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "figures"
EXP1 = ROOT / "docs" / "data" / "exp1-v2-main-2026-11-15.json"
EXP2 = ROOT / "docs" / "data" / "exp2-main-2026-11-15.json"

# One fixed order and one display name per model in every figure and table (sorted by the
# Experiment 2 recency effect, smallest first).
MODELS = [
    ("anthropic/claude-opus-4-8", "Claude Opus 4.8"),
    ("openrouter/z-ai/glm-5.3-flash", "GLM 5.3 Flash"),
    ("openrouter/deepseek/deepseek-v4.1-flash", "DeepSeek V4.1 Flash"),
    ("openrouter/deepseek/deepseek-v4-pro-0813", "DeepSeek V4 Pro"),
    ("openrouter/anthropic/claude-haiku-5.5", "Claude Haiku 5.5"),
    ("openrouter/mistralai/mistral-small-2603", "Mistral Small 4"),
    ("openrouter/openai/gpt-6-luna", "GPT-6 Luna"),
]

# Colours: a neutral grey for the control, and the first two categorical slots of a palette whose
# first three slots are separable under colour-vision deficiency for every pair.
GREY, BLUE, ORANGE = "#8a8984", "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

# Figure 2: mean probability on the expert's answer after turns 0-3 (docs/experiment2-results.md).
TRAJECTORIES = {
    "Claude Opus 4.8": {"expert_last": [0.54, 0.52, 0.60, 0.88], "expert_first": [0.54, 0.84, 0.87, 0.87]},
    "Mistral Small 4": {"expert_last": [0.37, 0.33, 0.42, 0.62], "expert_first": [0.37, 0.61, 0.51, 0.33]},
    "GPT-6 Luna": {"expert_last": [0.44, 0.38, 0.54, 0.85], "expert_first": [0.44, 0.86, 0.72, 0.55]},
}


def style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8.5,
        "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
        "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK, "ytick.labelcolor": INK,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "legend.frameon": False,
        "savefig.dpi": 220, "savefig.bbox": "tight", "savefig.facecolor": "white",
    })


def errs(value: float, ci: list[float]) -> tuple[float, float]:
    return max(value - ci[0], 0.0), max(ci[1] - value, 0.0)


def figure1(exp1: dict) -> None:
    """Three bars per model: neutral re-ask, "Are you sure?", escalating rebuttal."""
    arms = [("reask", "Neutral re-ask (control)", GREY),
            ("are_you_sure", '"Are you sure?"', BLUE),
            ("escalate", "Escalating rebuttal", ORANGE)]
    fig, ax = plt.subplots(figsize=(6.6, 2.5))
    width = 0.25
    for j, (arm, label, colour) in enumerate(arms):
        xs = [i + (j - 1) * (width + 0.02) for i in range(len(MODELS))]
        values = [exp1[m]["arms"][arm]["net_shift"] for m, _ in MODELS]
        lo_hi = [errs(v, exp1[m]["arms"][arm]["net_shift_ci"]) for v, (m, _) in zip(values, MODELS)]
        ax.bar(xs, values, width, color=colour, label=label, linewidth=0)
        ax.errorbar(xs, values, yerr=[[e[0] for e in lo_hi], [e[1] for e in lo_hi]],
                    fmt="none", ecolor=INK, elinewidth=0.7, capsize=1.6, capthick=0.7)
    # Mistral's escalation arm lost 11% of its conversations to the exclusion rule: mark it.
    k = [name for _, name in MODELS].index("Mistral Small 4")
    top = exp1[MODELS[k][0]]["arms"]["escalate"]["net_shift_ci"][1]
    ax.text(k + (width + 0.02), top + 0.006, "†", ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(range(len(MODELS)))
    ax.set_xticklabels([name.replace(" ", "\n", 1) for _, name in MODELS])
    ax.set_ylabel("Net shift, first to last answer\n(total variation distance)")
    ax.set_ylim(0, 0.29)
    ax.tick_params(axis="x", length=0)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, handlelength=1.1, columnspacing=1.6,
              borderaxespad=0.2)
    fig.savefig(OUT / "fig1-experiment1.png")
    plt.close(fig)


def figure2() -> None:
    """Small multiples: the probability on the expert's answer after each turn, in both orders."""
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.35), sharey=True)
    series = [("expert_last", "Professor speaks last", BLUE, 3), ("expert_first", "Professor speaks first", ORANGE, 1)]
    for ax, (name, data) in zip(axes, TRAJECTORIES.items()):
        for key, label, colour, expert_turn in series:
            ys = data[key]
            ax.plot(range(4), ys, color=colour, linewidth=1.6, label=label, zorder=2)
            for t, y in enumerate(ys):
                filled = t == expert_turn  # the turn right after the expert spoke
                ax.plot(t, y, "o", markersize=6.5 if filled else 4.5, zorder=3,
                        markerfacecolor=colour if filled else "white",
                        markeredgecolor=colour, markeredgewidth=1.3)
            other = data["expert_first" if key == "expert_last" else "expert_last"][-1]
            nudge = 0 if abs(ys[-1] - other) > 0.05 else (5 if ys[-1] >= other else -5)
            ax.annotate(f"{ys[-1]:.2f}", (3, ys[-1]), xytext=(7, nudge), textcoords="offset points",
                        va="center", fontsize=8, color=INK)
        ax.set_title(name, fontsize=9, color=INK, pad=6)
        ax.set_xticks(range(4))
        ax.set_xticklabels(["first\nanswer", "user 1", "user 2\n(student)", "user 3"])
        ax.set_xlim(-0.25, 3.7)
        ax.set_ylim(0.2, 1.0)
        ax.tick_params(axis="x", length=0)
    axes[0].set_ylabel("Mean probability on\nthe professor's answer")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.98),
               handlelength=1.6, columnspacing=2.0)
    fig.subplots_adjust(wspace=0.12)
    fig.savefig(OUT / "fig2-experiment2-turns.png")
    plt.close(fig)


def figure3(exp1: dict, exp2: dict) -> None:
    """One point per model: movement under doubt (Experiment 1) against the order effect (Experiment 2).
    The two models the text compares, GLM 5.3 Flash and GPT-6 Luna, are highlighted."""
    fig, ax = plt.subplots(figsize=(5.6, 2.7))
    labels = {  # label anchor in data coordinates, and horizontal alignment; all in free space
        "Claude Opus 4.8": (0.036, -0.011, "left"), "GLM 5.3 Flash": (0.067, 0.021, "left"),
        "DeepSeek V4.1 Flash": (0.063, 0.057, "left"), "DeepSeek V4 Pro": (0.031, 0.120, "right"),
        "Claude Haiku 5.5": (0.050, 0.108, "left"), "Mistral Small 4": (0.096, 0.256, "left"),
        "GPT-6 Luna": (0.054, 0.332, "left"),
    }
    highlighted = {"GLM 5.3 Flash", "GPT-6 Luna"}
    for model, name in MODELS:
        a = exp1[model]["arms"]["are_you_sure"]
        r = exp2[model]["expert_recency"]
        x, y = a["vs_control"], r["mean"]
        xe, ye = errs(x, a["vs_control_ci"]), errs(y, r["ci"])
        ax.errorbar(x, y, xerr=[[xe[0]], [xe[1]]], yerr=[[ye[0]], [ye[1]]], fmt="none",
                    ecolor=MUTED, elinewidth=0.7, zorder=2)
        ax.plot(x, y, "o", markersize=7 if name in highlighted else 6,
                markerfacecolor=ORANGE if name in highlighted else BLUE,
                markeredgecolor="white", markeredgewidth=1.2, zorder=3)
        lx, ly, ha = labels[name]
        ax.text(lx, ly, name, ha=ha, va="center", fontsize=8, color=INK, zorder=4,
                fontweight="bold" if name in highlighted else "normal")
    ax.set_xlabel('Experiment 1: net shift under "Are you sure?" beyond the re-ask')
    ax.set_ylabel("Experiment 2: order effect")
    ax.set_xlim(0, 0.13)
    ax.set_ylim(-0.03, 0.38)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    fig.savefig(OUT / "fig3-both-experiments.png")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    style()
    exp1, exp2 = json.loads(EXP1.read_text()), json.loads(EXP2.read_text())
    figure1(exp1)
    figure2()
    figure3(exp1, exp2)
    for p in sorted(OUT.glob("fig*.png")):
        print(f"Wrote {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
