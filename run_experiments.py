
import subprocess
import csv
import re
import os

TCP_TYPES = [
    "Westwood",
    "WestwoodPlus",
    "Reno",
    "NewReno",
    "Tahoe"
]

PER_VALUES = [
    0.0001, 0.0002, 0.0005,
    0.001, 0.002, 0.005,
    0.01, 0.02, 0.05
]

DELAY_VALUES = [
    0.01, 1, 10, 25, 50,
    100, 150, 200, 250
]

BANDWIDTH_VALUES = [
    1, 2, 3, 4, 5, 6, 7, 8
]

ACK_VALUES = [1, 2, 4, 8]

os.makedirs("results", exist_ok=True)


def run_simulation(tcp, per=0.005,
                   bandwidth="2Mbps",
                   delay="0.01ms",
                   del_ack=1):

    arguments = (
        "scratch/westwood-experiment "
        "--tcp={} --per={} "
        "--bandwidth={} --delay={} "
        "--delAck={}"
    ).format(tcp, per, bandwidth, delay, del_ack)

    result = subprocess.check_output(
        ["./waf", "--run", arguments],
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    match = re.search(
        r"Throughput:\s*([0-9.eE+-]+)\s*Mbps",
        result
    )

    if not match:
        raise RuntimeError(
            "Cannot read throughput:\n" + result
        )

    return float(match.group(1))


def save_csv(filename, header, rows):
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def run_figure_5():
    rows = []

    for per in PER_VALUES:
        row = [per]

        for tcp in TCP_TYPES:
            throughput = run_simulation(
                tcp, per=per
            )
            row.append(throughput)
            print("Fig5", tcp, per, throughput)

        rows.append(row)

    save_csv(
        "results/figure5.csv",
        ["PER"] + TCP_TYPES,
        rows
    )


def run_figure_6():
    rows = []

    for delay in DELAY_VALUES:
        row = [delay]

        for tcp in TCP_TYPES:
            throughput = run_simulation(
                tcp, delay="{}ms".format(delay)
            )
            row.append(throughput)
            print("Fig6", tcp, delay, throughput)

        rows.append(row)

    save_csv(
        "results/figure6.csv",
        ["Delay_ms"] + TCP_TYPES,
        rows
    )


def run_figure_7():
    rows = []

    for bw in BANDWIDTH_VALUES:
        row = [bw]

        for tcp in TCP_TYPES:
            throughput = run_simulation(
                tcp, bandwidth="{}Mbps".format(bw)
            )
            row.append(throughput)
            print("Fig7", tcp, bw, throughput)

        rows.append(row)

    save_csv(
        "results/figure7.csv",
        ["Bandwidth_Mbps"] + TCP_TYPES,
        rows
    )


def run_figure_8(tcp, filename):
    rows = []

    for per in PER_VALUES:
        row = [per]

        for ack in ACK_VALUES:
            throughput = run_simulation(
                tcp, per=per, del_ack=ack
            )
            row.append(throughput)
            print("Fig8", tcp, per, ack, throughput)

        rows.append(row)

    save_csv(
        filename,
        ["PER"] + [
            "ACK_{}".format(x) for x in ACK_VALUES
        ],
        rows
    )


if __name__ == "__main__":
    run_figure_5()
    run_figure_6()
    run_figure_7()

    run_figure_8(
        "Westwood", "results/figure8a.csv"
    )

    run_figure_8(
        "WestwoodPlus", "results/figure8b.csv"
    )

    run_figure_8(
        "Reno", "results/figure8c.csv"
    )

    print("All experiments completed.")
