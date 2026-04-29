import io
import base64

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def _to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{data}"


def animal_chart(animal) -> str | None:
    has_weight = bool(animal.weights)
    has_growth = bool(animal.growths)
    if not has_weight and not has_growth:
        return None

    n_panels = int(has_weight) + int(has_growth)
    fig, axes = plt.subplots(n_panels, 1, figsize=(11, 3.5 * n_panels), squeeze=False)
    fig.patch.set_facecolor("white")

    idx = 0
    if has_weight:
        ax = axes[idx][0]
        dates = [r.recorded for r in animal.weights]
        weights = [r.weight for r in animal.weights]
        ax.plot(dates, weights, "o-", color="#1d4ed8", markersize=5, linewidth=1.8, label="Weight")
        ax.set_ylabel("Weight (kg)", fontsize=10)
        ax.set_title(f"Weight  —  {animal.eid}", fontsize=11, fontweight="bold", pad=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=10))
        fig.autofmt_xdate(rotation=25, ha="right")
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.set_axisbelow(True)

        # Annotate first and last weight
        if len(weights) >= 2:
            ax.annotate(f"{weights[0]:.0f} kg", (dates[0], weights[0]),
                        textcoords="offset points", xytext=(6, 6), fontsize=8, color="#374151")
            ax.annotate(f"{weights[-1]:.0f} kg", (dates[-1], weights[-1]),
                        textcoords="offset points", xytext=(-30, 6), fontsize=8, color="#374151")
        idx += 1

    if has_growth:
        ax = axes[idx][0]
        dates = [r.recorded for r in animal.growths]
        growths = [r.growth for r in animal.growths]
        ax.plot(dates, growths, "o-", color="#dc2626", markersize=4, linewidth=1.8, label="Growth")
        ax.axhline(0, color="#6b7280", linewidth=0.8, linestyle="--")
        ax.set_ylabel("Growth (g/day)", fontsize=10)
        if not has_weight:
            ax.set_title(f"Growth  —  {animal.eid}", fontsize=11, fontweight="bold", pad=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=10))
        fig.autofmt_xdate(rotation=25, ha="right")
        ax.grid(True, alpha=0.25, linestyle="--", axis="y")
        ax.set_axisbelow(True)

    plt.tight_layout(pad=1.2)
    return _to_b64(fig)
