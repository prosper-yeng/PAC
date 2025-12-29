from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"

def main():
    figdir = OUT / "paper" / "figures"
    figdir.mkdir(parents=True, exist_ok=True)

    # Figure: RQ3 latency (baseline vs enforced)
    rq3 = OUT / "metrics" / "rq3_latency.csv"
    if rq3.exists():
        df = pd.read_csv(rq3)
        x = range(len(df))
        plt.figure()
        plt.plot(x, df["p50_ms"], marker="o", label="p50")
        plt.plot(x, df["p95_ms"], marker="o", label="p95")
        plt.xticks(x, df["mode"])
        plt.ylabel("Latency (ms)")
        plt.xlabel("Mode")
        plt.title("Runtime latency (wallet workload)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(figdir / "rq3_latency.pdf")
        plt.close()

    # Figure: RQ1 overall evidence coverage by release
    rq1 = OUT / "metrics" / "rq1_coverage.csv"
    if rq1.exists():
        df = pd.read_csv(rq1)
        plt.figure()
        plt.plot(df["release"], df["coverage_pct"], marker="o")
        plt.ylabel("Coverage (%)")
        plt.xlabel("Release")
        plt.title("Control evidence coverage by release")
        plt.tight_layout()
        plt.savefig(figdir / "rq1_coverage.pdf")
        plt.close()

    # Figure: RQ1 staleness timeline (missing core controls per monitoring window)
    st = OUT / "metrics" / "rq1_staleness.csv"
    if st.exists():
        df = pd.read_csv(st)
        # Use window_start if present; otherwise index
        if "window_start" in df.columns:
            x = df["window_start"]
            plt.figure()
            plt.plot(x, df["missing_core_controls"], marker="o", label="Missing core controls")
            if "deny_count" in df.columns:
                plt.plot(x, df["deny_count"], marker="o", label="Deny count")
            plt.xlabel("Window start (epoch seconds)")
            plt.ylabel("Count")
            plt.title("Monitoring staleness over time (per window)")
            plt.legend()
            plt.tight_layout()
            plt.savefig(figdir / "rq1_staleness_timeline.pdf")
            plt.close()
        else:
            plt.figure()
            plt.plot(range(len(df)), df["missing_core_controls"], marker="o")
            plt.xlabel("Window index")
            plt.ylabel("Missing core controls")
            plt.title("Monitoring staleness over time (per window)")
            plt.tight_layout()
            plt.savefig(figdir / "rq1_staleness_timeline.pdf")
            plt.close()

    # Figure: RQ1 category coverage (stacked bar chart per release)
    cat = OUT / "metrics" / "rq1_category_coverage.csv"
    if cat.exists():
        df = pd.read_csv(cat)
        # Pivot to releases x categories, values=coverage_pct
        pivot = df.pivot(index="release", columns="category", values="coverage_pct").fillna(0.0)
        ax = pivot.plot(kind="bar", stacked=True)
        ax.set_xlabel("Release")
        ax.set_ylabel("Coverage (%)")
        ax.set_title("Coverage by control category (stacked)")
        plt.tight_layout()
        plt.savefig(figdir / "rq1_category_coverage_stacked.pdf")
        plt.close()

    print("Figures saved -> out/paper/figures/")

if __name__ == "__main__":
    main()
