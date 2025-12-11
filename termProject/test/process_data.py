import pandas as pd
import csv
import argparse
import re
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# --- Configuration ---
# Source directory containing raw CSV files
SOURCE_DIR = Path("./csv_results")
# Target directory for processed files
TARGET_DIR = Path("./processed_data")
# Directory to save generated plots
PLOTS_DIR = Path("./plots")

# Workload tags corresponding to experiment order
WORKLOAD_ORDER = ["std", "heavy", "light"]

# LLM Name Mapping
LLM_NAME_MAPPING = {
    "gpt": "GPT-5.1 Thinking",
    "gemini": "Gemini 3.0 Pro",
    "deepseek": "DeepSeek V3.2",
}

# --- AWS Pricing Constants (USD per GB-Second) ---
# Based on user provided data (First Tier)
PRICE_X86 = 0.0000166667
PRICE_ARM = 0.0000133334
# Calculated Price Ratio (ARM / X86) ~= 0.8
PRICE_RATIO = PRICE_ARM / PRICE_X86


def enrich_and_save_csv(source_path: Path, target_path: Path, metadata: Dict[str, str]) -> None:
    """
    Reads the source CSV, appends metadata columns, and saves to target.
    """
    new_headers: List[str] = ["LLM_Source", "Architecture", "Workload_Type"]
    new_values: List[str] = [
        metadata.get("llm", "Unknown"),
        metadata.get("arch", "Unknown"),
        metadata.get("workload", "Unknown")
    ]

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with source_path.open(mode='r', encoding='utf-8', newline='') as infile, \
                target_path.open(mode='w', encoding='utf-8', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            try:
                headers = next(reader)
            except StopIteration:
                return
            writer.writerow(headers + new_headers)
            for row in reader:
                writer.writerow(row + new_values)
    except Exception as e:
        print(f"[!] Error processing CSV {source_path.name}: {e}")


def process_raw_data(source_dir: Path, target_dir: Path) -> None:
    """
    Scans raw CSV files, groups by experiment, and enriches data.
    """
    print(f"[*] Scanning source directory: {source_dir} ...")
    if not source_dir.exists():
        print(f"[!] Source directory {source_dir} does not exist.")
        return

    pattern = re.compile(
        r"results_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)_(\d{8})_(\d{6})\.csv")
    file_groups: Dict[Tuple[str, str, str],
                      List[Dict[str, Any]]] = defaultdict(list)

    for file_path in list(source_dir.glob("*.csv")):
        match = pattern.match(file_path.name)
        if match:
            model, arch, date, time_str = match.groups()
            file_groups[(model, arch, date)].append({
                "time": time_str,
                "original_name": file_path.name,
                "full_path": file_path,
                "model": model,
                "arch": arch,
                "date": date
            })

    processed_count = 0
    for (model, arch, date), items in file_groups.items():
        sorted_items = sorted(items, key=lambda x: x["time"])
        if len(sorted_items) != 3:
            continue

        for index, item in enumerate(sorted_items):
            workload_tag = WORKLOAD_ORDER[index]
            llm_display_name = LLM_NAME_MAPPING.get(model.lower(), model)

            new_filename = f"results_{model}_{arch}_{workload_tag}_{date}_{item['time']}.csv"
            target_file = target_dir / new_filename

            enrich_and_save_csv(
                item["full_path"],
                target_file,
                {"llm": llm_display_name, "arch": arch, "workload": workload_tag}
            )
            processed_count += 1
            print(
                f"    [OK] {item['original_name']} -> {new_filename} ({llm_display_name})")

    print(f"[*] Processed {processed_count} files.")


def load_all_data(source_dir: Path) -> pd.DataFrame:
    """
    Loads all processed CSV files into a DataFrame and SYNTHESIZES Pipeline_Total.
    """
    all_files = list(source_dir.glob("*.csv"))
    if not all_files:
        return pd.DataFrame()

    df_list = []
    for f in all_files:
        try:
            df_list.append(pd.read_csv(f))
        except Exception:
            pass

    if not df_list:
        return pd.DataFrame()

    combined_df = pd.concat(df_list, ignore_index=True)

    # Convert numeric columns
    cols_to_numeric = ['Logic_Time_ms', 'Round_Trip_ms']
    for col in cols_to_numeric:
        if col in combined_df.columns:
            combined_df[col] = pd.to_numeric(
                combined_df[col], errors='coerce').fillna(0.0)

    # --- FIX: Synthesize 'Pipeline_Total' from steps ---
    # Group by key identifiers to calculate sum for each run
    # Assuming 'Run_ID' is unique within a specific file context,
    # but since we merged files, we need to group by metadata too to be safe.
    group_cols = ['LLM_Source', 'Architecture', 'Workload_Type', 'Run_ID']

    # Check if necessary columns exist
    if all(col in combined_df.columns for col in group_cols):
        # Filter for BENCHMARK steps only to avoid double counting if Total exists
        benchmark_steps = combined_df[
            (combined_df['Type'] == 'BENCHMARK') &
            (combined_df['Step'] != 'Pipeline_Total')
        ]

        # Calculate Sums
        total_times = benchmark_steps.groupby(
            group_cols)[cols_to_numeric].sum().reset_index()

        # Assign static columns for the summary rows
        total_times['Step'] = 'Pipeline_Total'
        total_times['Type'] = 'BENCHMARK'  # Or 'SUMMARY'
        total_times['Function_Name'] = 'Aggregated'
        # Assume success if steps exist, or refine logic
        total_times['Success'] = True

        # Concatenate original data with new totals
        combined_df = pd.concat([combined_df, total_times], ignore_index=True)
        print(f"[*] Synthesized {len(total_times)} 'Pipeline_Total' rows.")

    return combined_df


def analyze_primary_objective_llm_comparison(df: pd.DataFrame) -> None:
    """
    Comparison of LLM Code Performance (Absolute Time).
    """
    print("\n" + "="*80)
    print("PRIMARY OBJECTIVE: LLM CODE PERFORMANCE")
    print("="*80)

    if df.empty or 'Success' not in df.columns:
        return

    clean_df = df[df['Success'].astype(str).str.lower() == 'true'].copy()
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # 1. Total Pipeline Analysis & Plot
    pipeline_df = clean_df[clean_df['Step'] == 'Pipeline_Total']
    if not pipeline_df.empty:
        # --- [RESTORED] Text Output ---
        print("\n--- View 1: Total Pipeline Execution Time (Lower is Better) ---")
        summary = pipeline_df.groupby(['Workload_Type', 'Architecture', 'LLM_Source'])['Logic_Time_ms'].agg(
            Mean='mean', Std_Dev='std'
        )
        summary['CV_%'] = (summary['Std_Dev'] / summary['Mean']) * 100
        print(summary.round(2))
        # ------------------------------

        plt.figure(figsize=(12, 6))
        g = sns.catplot(
            data=pipeline_df, kind="bar", x="Workload_Type", y="Logic_Time_ms",
            hue="LLM_Source", col="Architecture", order=WORKLOAD_ORDER,
            errorbar="sd", palette="muted", height=5, aspect=1.2
        )
        g.fig.subplots_adjust(top=0.85)
        g.fig.suptitle('Total Pipeline Execution Time (Lower is Better)')
        g.savefig(PLOTS_DIR / "primary_llm_Pipeline_Total.png")
        plt.close()

    # 2. Per-Function Analysis & Plots
    step_df = clean_df[clean_df['Type'] == 'BENCHMARK']

    # --- [RESTORED] Text Output for Granular Breakdown ---
    if not step_df.empty:
        print("\n--- View 2: Per-Function Granular Breakdown ---")
        step_summary = step_df.groupby(['Workload_Type', 'Architecture', 'Step', 'LLM_Source'])['Logic_Time_ms'].agg(
            Mean='mean'
        ).unstack()
        print(step_summary.round(2))
    # -----------------------------------------------------

    for step in step_df['Step'].unique():
        current_step_df = step_df[step_df['Step'] == step]
        if current_step_df.empty:
            continue

        plt.figure(figsize=(12, 6))
        g = sns.catplot(
            data=current_step_df, kind="bar", x="Workload_Type", y="Logic_Time_ms",
            hue="LLM_Source", col="Architecture", order=WORKLOAD_ORDER,
            errorbar="sd", palette="muted", height=5, aspect=1.2
        )
        g.fig.subplots_adjust(top=0.85)
        g.fig.suptitle(f'{step} Execution Time (Lower is Better)')
        sanitized_step = "".join(
            [c for c in step if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        g.savefig(PLOTS_DIR / f"primary_llm_{sanitized_step}.png")
        plt.close()


def analyze_secondary_objective_architecture(df: pd.DataFrame) -> None:
    """
    Comparison of Architecture (Speedup AND Cost Savings).
    """
    print("\n" + "="*80)
    print("SECONDARY OBJECTIVE: ARCHITECTURE (SPEEDUP & COST)")
    print("="*80)

    if df.empty or 'Success' not in df.columns:
        return
    clean_df = df[df['Success'].astype(str).str.lower() == 'true'].copy()

    grouped = clean_df.groupby(['Workload_Type', 'LLM_Source', 'Type', 'Step', 'Architecture'])[
        'Logic_Time_ms'].mean().reset_index()

    pivot_df = grouped.pivot_table(
        index=['Workload_Type', 'LLM_Source', 'Type', 'Step'],
        columns='Architecture',
        values='Logic_Time_ms'
    )

    if 'x86' not in pivot_df.columns or 'arm' not in pivot_df.columns:
        print("[!] Missing x86 or arm data.")
        return

    # --- Metrics Calculation ---
    # 1. Performance Speedup %
    pivot_df['Speedup_%'] = (
        (pivot_df['x86'] - pivot_df['arm']) / pivot_df['x86']) * 100

    # 2. Cost Saving % (Using Real Pricing Data)
    # Formula: 1 - ( (Time_ARM * Price_ARM) / (Time_X86 * Price_X86) )
    # Since Memory is constant, Cost Ratio = (Time_ARM / Time_X86) * (Price_ARM / Price_X86)
    pivot_df['Cost_Ratio'] = (pivot_df['arm'] / pivot_df['x86']) * PRICE_RATIO
    pivot_df['Cost_Saving_%'] = (1 - pivot_df['Cost_Ratio']) * 100

    pivot_df.sort_index(inplace=True)

    # --- Text Summary ---
    print("\n--- Architecture Comparison (Pipeline Total) ---")
    total_only = pivot_df[pivot_df.index.get_level_values(
        'Step') == 'Pipeline_Total']
    with pd.option_context('display.float_format', '{:.2f}'.format):
        print(total_only[['x86', 'arm', 'Speedup_%', 'Cost_Saving_%']])

    # --- Plotting ---
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    plot_data = pivot_df.reset_index()

    # Plot 1: Speedup (Performance)
    for step in plot_data['Step'].unique():
        step_data = plot_data[plot_data['Step'] == step]
        if step_data.empty:
            continue

        plt.figure(figsize=(10, 6))
        ax = sns.barplot(
            data=step_data, x="Workload_Type", y="Speedup_%", hue="LLM_Source",
            order=WORKLOAD_ORDER, palette="viridis"
        )

        # Reference Line: 0% (Performance Parity)
        ax.axhline(0, color='black', linewidth=1)
        # Reference Line: 20% (Magnitude of Price Diff - Just for context)
        ax.axhline(20, color='red', linestyle='--', linewidth=1,
                   label='Reference: 20% Magnitude')

        ax.set_title(f'{step}: ARM Speedup (Performance Only)')
        ax.set_ylabel('Speedup (%)')
        ax.legend(title="LLM Source")
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f%%')

        sanitized = "".join([c for c in step if c.isalnum()
                            or c in (' ', '_')]).strip().replace(" ", "_")
        plt.savefig(PLOTS_DIR / f"secondary_speedup_{sanitized}.png")
        plt.close()

    # Plot 2: Real Cost Savings (The Money Plot)
    # Only plot Total Pipeline Cost Savings as that's what matters for the bill
    total_data = plot_data[plot_data['Step'] == 'Pipeline_Total']
    if not total_data.empty:
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(
            data=total_data, x="Workload_Type", y="Cost_Saving_%", hue="LLM_Source",
            order=WORKLOAD_ORDER, palette="Greens_d"
        )

        # Breakeven Line at 0% Cost Savings
        ax.axhline(0, color='black', linewidth=1.5)
        # 20% Line (Savings if Performance is Identical)
        ax.axhline(20, color='blue', linestyle='--', linewidth=1,
                   label='20% Baseline (If Speed is Equal)')

        ax.set_title('Real Cost Savings: ARM vs x86 (Including Price & Speed)')
        ax.set_ylabel('Cost Saving (%)')
        ax.set_xlabel('Workload Type')
        ax.legend(title="LLM Source")

        # Add labels
        for container in ax.containers:
            ax.bar_label(container, fmt='%.1f%%')

        print(f"    [Plotting] Generated Cost Savings plot.")
        plt.savefig(PLOTS_DIR / "secondary_cost_savings.png")
        plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--process', action='store_true')
    parser.add_argument('--source', type=Path, default=SOURCE_DIR)
    parser.add_argument('--target', type=Path, default=TARGET_DIR)
    args = parser.parse_args()

    if args.process:
        process_raw_data(args.source, args.target)

    full_data = load_all_data(args.target)
    if not full_data.empty:
        analyze_primary_objective_llm_comparison(full_data)
        analyze_secondary_objective_architecture(full_data)
    else:
        print("[!] No data found.")


if __name__ == "__main__":
    main()
