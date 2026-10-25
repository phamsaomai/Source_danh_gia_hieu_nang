
import csv
import re
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt

# ==========================================
# CAU HINH
# ==========================================

NS3_SCRIPT = "scratch/westwood-python.py"

OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Cac TCP du kien thu nghiem
PROTOCOLS = [
    "TcpWestwoodPlus",
    "TcpNewReno",
    "TcpLinuxReno",
]

# Figure 5: Thay doi Packet Error Rate
PER_VALUES = [
    0.0001,
    0.0002,
    0.0005,
    0.001,
    0.002,
    0.005,
    0.01,
    0.02,
    0.05,
]

# Figure 6: Thay doi bottleneck delay (ms)
DELAY_VALUES = [
    0.01,
    1,
    10,
    25,
    50,
    100,
    150,
    200,
    250,
]

# Figure 7: Thay doi bandwidth (Mbps)
BANDWIDTH_VALUES = [
    1, 2, 3, 4, 5, 6, 7, 8
]

# So lan chay moi cau hinh
REPEATS = 1

# Thoi gian mo phong
SIM_TIME = 20.0


# ==========================================
# HAM CHAY NS-3
# ==========================================

def run_simulation(tcp, per, bandwidth, delay):

    command = (
        f"{NS3_SCRIPT} "
        f"--tcp={tcp} "
        f"--per={per} "
        f"--bandwidth={bandwidth} "
        f"--delay={delay} "
        f"--simTime={SIM_TIME}"
    )

    result = subprocess.run(
        ["./ns3", "run", command],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"NS-3 simulation failed:\n"
            f"{result.stdout}\n{result.stderr}"
        )

    match = re.search(
        r"^Throughput:\s*([0-9.eE+-]+)",
        result.stdout,
        re.MULTILINE
    )

    if match is None:
        raise RuntimeError(
            "Khong tim thay throughput:\n"
            + result.stdout
        )

    return float(match.group(1))


# ==========================================
# HAM CHAY THI NGHIEM
# ==========================================

def run_experiment(figure_name, values, parameter):

    results = []

    print(f"\n===== START {figure_name} =====")

    for tcp in PROTOCOLS:

        for value in values:

            throughput_samples = []

            for repeat in range(REPEATS):

                per = 0.005
                bandwidth = "2Mbps"
                delay = "0.01ms"

                if parameter == "per":
                    per = value

                elif parameter == "delay":
                    delay = f"{value}ms"

                elif parameter == "bandwidth":
                    bandwidth = f"{value}Mbps"

                throughput = run_simulation(
                    tcp=tcp,
                    per=per,
                    bandwidth=bandwidth,
                    delay=delay
                )

                throughput_samples.append(throughput)

                print(
                    f"{figure_name} | "
                    f"TCP={tcp} | "
                    f"{parameter}={value} | "
                    f"Run={repeat + 1}/{REPEATS} | "
                    f"Throughput={throughput:.6f} Mbps",
                    flush=True
                )

            avg_throughput = (
                sum(throughput_samples)
                / len(throughput_samples)
            )

            results.append({
                "tcp": tcp,
                "x": value,
                "throughput_mbps": avg_throughput
            })

    # ======================================
    # LUU CSV
    # ======================================

    csv_file = OUTPUT_DIR / f"{figure_name}.csv"

    with open(csv_file, "w", newline="") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "tcp",
                "x",
                "throughput_mbps"
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    print(f"Saved CSV: {csv_file}")

    # ======================================
    # VE BIEU DO
    # ======================================

    plt.figure(figsize=(9, 6))

    for tcp in PROTOCOLS:

        tcp_results = [
            row for row in results
            if row["tcp"] == tcp
        ]

        x_values = [
            row["x"]
            for row in tcp_results
        ]

        y_values = [
            row["throughput_mbps"]
            for row in tcp_results
        ]

        plt.plot(
            x_values,
            y_values,
            marker="o",
            linewidth=2,
            label=tcp
        )

    if parameter == "per":
        plt.xscale("log")
        plt.xlabel("Packet Error Rate (PER)")

    elif parameter == "delay":
        plt.xlabel("Bottleneck Delay (ms)")

    elif parameter == "bandwidth":
        plt.xlabel("Bottleneck Bandwidth (Mbps)")

    plt.ylabel("Average Throughput (Mbps)")
    plt.title(f"{figure_name} - NS-3.47")

    plt.legend()
    plt.grid(True, alpha=0.4)
    plt.tight_layout()

    png_file = OUTPUT_DIR / f"{figure_name}.png"

    plt.savefig(png_file, dpi=300)
    plt.close()

    print(f"Saved PNG: {png_file}")
    print(f"===== FINISHED {figure_name} =====\n")


# ==========================================
# CHUONG TRINH CHINH
# ==========================================

if __name__ == "__main__":

    run_experiment(
        figure_name="figure5",
        values=PER_VALUES,
        parameter="per"
    )

    run_experiment(
        figure_name="figure6",
        values=DELAY_VALUES,
        parameter="delay"
    )

    run_experiment(
        figure_name="figure7",
        values=BANDWIDTH_VALUES,
        parameter="bandwidth"
    )

    print("\nALL EXPERIMENTS COMPLETED!")
