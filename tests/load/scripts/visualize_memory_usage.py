# This script visualizes memory usage over time from the CSV file produced when
# running scramble_data.py.

import csv

import matplotlib.pyplot as plt

timestamps = []
memory_bytes = []

with open("memory_trace.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        timestamps.append(float(row["time_seconds"]))
        memory_bytes.append(int(row["memory_bytes"]))

# Convert memory to MB for readability
memory_mb = [m / 1024 / 1024 for m in memory_bytes]

plt.figure(figsize=(10, 6))
plt.plot(timestamps, memory_mb, marker="o", linestyle="-")
plt.title("Memory Usage Over Time")
plt.xlabel("Time (seconds)")
plt.ylabel("Memory Usage (MB)")
plt.grid(True)
plt.tight_layout()
plt.savefig("memory_usage_plot.png")
plt.show()
