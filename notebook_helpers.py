import numpy as np
import matplotlib.pyplot as plt

import numpy as np
import matplotlib.pyplot as plt


# Shared plotting style

SIR_COLORS = {
    "Susceptible": "#1F77B4",  # Blue
    "Infectious": "#D62728",   # Red
    "Removed": "#2CA02C",      # Green
}

BACKGROUND = "#FFFFFF"


def style_outbreak_axis(ax, title=None):
    """Apply consistent formatting to outbreak plots"""

    ax.set_facecolor("white")
    ax.set_title(title, pad=12)
    ax.set_xlabel("Days since introduction")
    ax.set_ylabel("Population (%)")

    ax.set_ylim(0, 100)

    ax.grid(
        True,
        color="#D0D0D0",
        alpha=0.35,
        linewidth=0.6,
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return ax


# Independent SIR curves

def sir_curves_plot(results, N, *, ax=None, title=None,
                    figsize=(10, 4)):
    """
    Plot S, I, and R as independent epidemic curves
    """

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    days = results["day"].to_numpy()

    for compartment in ["S", "I", "R"]:
        label = {
            "S": "Susceptible",
            "I": "Infectious",
            "R": "Removed",
        }[compartment]

        values = 100 * results[compartment].to_numpy() / N

        ax.plot(
            days,
            values,
            color=SIR_COLORS[label],
            linewidth=2.5,
            label=label,
        )

    style_outbreak_axis(ax, title)

    ax.set_xlim(days.min(), days.max())
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        frameon=False,
    )

    return ax


# Stacked SIR composition

def sir_stacked_plot(results, N, *, ax=None, title=None,
                     figsize=(10, 4)):
    """
    Plot S, I, and R as stacked population percentages
    """

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    days = results["day"].to_numpy()

    S = 100 * results["S"].to_numpy() / N
    I = 100 * results["I"].to_numpy() / N
    R = 100 * results["R"].to_numpy() / N

    if not np.allclose(S + I + R, 100, atol=1e-5):
        raise ValueError("S + I + R must equal 100%")

    ax.stackplot(
        days,
        R, I, S,
        colors=[
            SIR_COLORS["Removed"],
            SIR_COLORS["Infectious"],
            SIR_COLORS["Susceptible"],
        ],
        labels=["Removed", "Infectious", "Susceptible"],
        linewidth=0,
    )

    ax.plot(days, R, color="#333333", linewidth=0.8)
    ax.plot(days, R + I, color="#333333", linewidth=0.8)

    style_outbreak_axis(ax, title)

    ax.set_xlim(days.min(), days.max())
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        frameon=False,
    )

    return ax