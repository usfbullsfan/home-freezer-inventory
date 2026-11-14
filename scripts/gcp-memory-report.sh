#!/bin/bash
# Read-only memory snapshot for the GCP VM. Changes nothing.
#
# Run it before and after the low-memory changes and compare the two reports:
#   bash scripts/gcp-memory-report.sh 2>&1 | tee ~/mem-before.txt
#   ...apply the changes, wait 10+ minutes for things to settle...
#   bash scripts/gcp-memory-report.sh 2>&1 | tee ~/mem-after.txt
#   diff ~/mem-before.txt ~/mem-after.txt
#
# See docs/deployment/gcp-memory.md.

to_mib() { case "$1" in ''|'[not set]'|infinity) echo '-';; *) echo $(( $1 / 1048576 ));; esac; }

SERVICES="freezer-backend freezer-backend-dev freezer-frontend freezer-frontend-dev nginx"

echo "=== $(date -Is) on $(hostname) ==="
echo
echo "--- free -m ---"
free -m
echo
echo "--- swap ---"
swapon --show 2>/dev/null || cat /proc/swaps
echo "vm.swappiness = $(cat /proc/sys/vm/swappiness)"
echo "vm.vfs_cache_pressure = $(cat /proc/sys/vm/vfs_cache_pressure)"
echo
echo "--- memory per systemd service (cgroup, includes child processes) ---"
printf '%-24s %-10s %10s %10s\n' SERVICE STATE MEM_MiB SWAP_MiB
for s in $SERVICES; do
    state=$(systemctl is-active "$s" 2>/dev/null)
    mem=$(systemctl show -p MemoryCurrent --value "$s" 2>/dev/null)
    swp=$(systemctl show -p MemorySwapCurrent --value "$s" 2>/dev/null)
    printf '%-24s %-10s %10s %10s\n' "$s" "${state:-?}" "$(to_mib "$mem")" "$(to_mib "$swp")"
done
echo
echo "--- top 20 processes by resident memory (RSS, KiB) ---"
ps -eo pid,user,rss,vsz,etime,cmd --sort=-rss | cut -c1-160 | head -21
echo
echo "--- swap used per process (KiB, top 15) ---"
for f in /proc/[0-9]*/status; do
    awk -v pid="${f//[^0-9]/}" '/^Name:/{n=$2} /^VmSwap:/{if ($2>0) print $2, pid, n}' "$f" 2>/dev/null
done | sort -rn | head -15
echo
echo "--- totals by command name (RSS MiB; shared pages are counted more than once) ---"
ps -eo rss,comm --no-headers | awk '{m[$2]+=$1} END {for (c in m) if (m[c] > 10240) printf "%8.1f  %s\n", m[c]/1024, c}' | sort -rn
echo
echo "--- vmstat 1 5 (si/so = swap in/out per second, wa = iowait %) ---"
vmstat 1 5
