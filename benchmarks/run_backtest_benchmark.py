import time
import os
import sys
import json

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.indicators import enrich_dataframe
from app.core.backtester import run_comparative_backtest, run_strategy_backtest

def generate_synthetic_bars(n: int = 500) -> pd.DataFrame:
    """Generates synthetic daily OHLCV bars."""
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    returns = np.random.normal(0.0008, 0.018, n)
    price = 120.0 * np.cumprod(1 + returns)
    high = price * (1 + np.abs(np.random.normal(0.008, 0.004, n)))
    low = price * (1 - np.abs(np.random.normal(0.008, 0.004, n)))
    open_p = price * (1 + np.random.normal(0, 0.003, n))
    volume = np.random.randint(500000, 8000000, n)
    return pd.DataFrame({
        "Open": open_p,
        "High": high,
        "Low": low,
        "Close": price,
        "Volume": volume
    }, index=dates)

def run_performance_benchmarks():
    print("=" * 75)
    print("[BENCHMARK] ALPHAPULSE QUANTITATIVE ENGINE & BACKTEST BENCHMARK SUITE")
    print("=" * 75)

    num_iterations = 150
    bars_per_test = 365  # 1 year of daily bars

    # 1. Warmup
    print("\n[1/3] Warming up indicator calculation and backtester...")
    warm_df = generate_synthetic_bars(200)
    for _ in range(5):
        run_comparative_backtest(warm_df)
    print("      Warmup complete.")

    # 2. Indicator Enrichment Throughput Benchmark
    print(f"\n[2/3] Benchmarking indicator pipeline throughput across 10,000 bars...")
    large_df = generate_synthetic_bars(10000)
    t0_enrich = time.perf_counter()
    enrich_dataframe(large_df)
    t1_enrich = time.perf_counter()
    enrich_time_sec = t1_enrich - t0_enrich
    enrich_throughput = 10000.0 / enrich_time_sec

    # 3. Comparative Backtest Latency Percentiles (150 runs on 1-year data)
    print(f"\n[3/3] Benchmarking multi-strategy comparative backtest ({num_iterations} runs)...")
    latencies_ms = []
    test_df = generate_synthetic_bars(bars_per_test)

    t0_total = time.perf_counter()
    for _ in range(num_iterations):
        t0 = time.perf_counter()
        run_comparative_backtest(test_df, initial_capital=10000.0)
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)
    total_time = time.perf_counter() - t0_total
    backtest_ops = num_iterations / total_time

    p50 = float(np.percentile(latencies_ms, 50))
    p95 = float(np.percentile(latencies_ms, 95))
    p99 = float(np.percentile(latencies_ms, 99))
    min_lat = float(np.min(latencies_ms))
    max_lat = float(np.max(latencies_ms))

    # 4. Run an institutional strategy comparison sample
    comparison = run_comparative_backtest(test_df)
    tbl = comparison["comparison_table"]

    print("\n" + "=" * 75)
    print("ENGINE LATENCY & THROUGHPUT SCORECARD")
    print("=" * 75)
    print(f"{'Metric':<32} | {'Value':<18} | {'Unit':<15}")
    print("-" * 75)
    print(f"{'Indicator Ingestion Throughput':<32} | {enrich_throughput:15.1f}  | bars/second")
    print(f"{'Comparative Backtest p50':<32} | {p50:15.2f}  | ms/run")
    print(f"{'Comparative Backtest p95':<32} | {p95:15.2f}  | ms/run")
    print(f"{'Comparative Backtest p99':<32} | {p99:15.2f}  | ms/run")
    print(f"{'Comparative Throughput':<32} | {backtest_ops:15.1f}  | runs/second")
    print("=" * 75)

    print("\n" + "=" * 75)
    print("STRATEGY COMPARISON BENCHMARK (1-YEAR HORIZON)")
    print("=" * 75)
    print(f"{'Strategy':<26} | {'Return %':<10} | {'Sharpe':<8} | {'Sortino':<8} | {'Max DD %':<10}")
    print("-" * 75)
    for row in tbl:
        print(f"{row['strategy']:<26} | {row['net_return_pct']:+8.2f}% | {row['sharpe_ratio']:6.2f} | {row['sortino_ratio']:6.2f} | {row['max_drawdown_pct']:8.2f}%")
    print("=" * 75)
    print(f"Alpha vs Benchmark: {comparison['alpha_vs_buy_and_hold']:+5.2f}%")
    print(f"Drawdown Mitigation: {comparison['drawdown_mitigation_vs_benchmark']:+5.2f}%")
    print(f"Top Risk-Adjusted Performer: {comparison['best_performing_strategy']}")
    print("=" * 75)

    report = {
        "num_iterations": num_iterations,
        "bars_evaluated": bars_per_test,
        "indicator_throughput_bars_per_sec": round(enrich_throughput, 1),
        "backtest_latency_ms": {
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "min": round(min_lat, 2),
            "max": round(max_lat, 2)
        },
        "backtest_throughput_runs_per_sec": round(backtest_ops, 1),
        "sample_strategy_comparison": comparison["comparison_table"],
        "alpha_vs_buy_and_hold_pct": comparison["alpha_vs_buy_and_hold"],
        "drawdown_mitigation_pct": comparison["drawdown_mitigation_vs_benchmark"]
    }

    out_file = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[OK] Benchmark report saved to: {out_file}\n")

if __name__ == "__main__":
    run_performance_benchmarks()
