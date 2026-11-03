cat > intrusive.sh << 'EOF'
#!/usr/bin/env bash
# Stage 3: does the measuring tool change the measured time? /usr/bin/time vs perf stat.
# Usage: ./intrusive.sh <N> <out.csv>
set -euo pipefail
cd "$(dirname "$0")"
N=$1; OUT=$2; CORE=2
sudo renice -n -5 -p $$ > /dev/null
declare -A CMD=( [read]="./out/graph_traverse --write 5 graphs/graph-rand-10M.bin"
                 [mmap]="./out/graph_traverse_mmap --write 200 graphs/graph-rand-10M.bin" )
echo "program,tool,round,wall_s" > "$OUT"
for round in $(seq 1 "$N"); do
  for prog in read mmap; do
    for tool in $(printf "time\nperf\n" | shuf); do
      t0=$(date +%s%N)
      if [ "$tool" = time ]; then
        /usr/bin/time -o /dev/null taskset -c $CORE ${CMD[$prog]} 2>/dev/null
      else
        perf stat -e task-clock,context-switches,cpu-migrations,page-faults -o /dev/null \
          taskset -c $CORE ${CMD[$prog]} 2>/dev/null
      fi
      t1=$(date +%s%N)
      echo "$prog,$tool,$round,$(awk -v a="$t0" -v b="$t1" 'BEGIN { printf "%.6f", (b - a) / 1e9 }')" >> "$OUT"
    done
  done
  echo "round $round/$N done"
done
EOF
chmod +x intrusive.sh
./intrusive.sh 22 data/intrusive.csv

python3 -c "
import pandas as pd, numpy as np; from scipy import stats
d = pd.read_csv('data/intrusive.csv'); d = d[d['round'] > 2]
for prog, g in d.groupby('program'):
    a, b = g[g.tool == 'time'].wall_s, g[g.tool == 'perf'].wall_s
    h = lambda x: stats.t.ppf(.975, len(x)-1) * x.std(ddof=1) / np.sqrt(len(x))
    print(f'{prog}: time {a.mean():.4f}+-{h(a):.4f}  perf {b.mean():.4f}+-{h(b):.4f}  '
          f'overhead {100*(b.mean()/a.mean()-1):+.2f}%  Welch p={stats.ttest_ind(b, a, equal_var=False).pvalue:.3g}')
" | tee results/intrusive.txt

for i in 1 2 3; do
  /usr/bin/time -f "read plain  %e s" ./out/graph_traverse --write 5 graphs/graph-rand-1M.bin 2>&1 | tail -1
  /usr/bin/time -f "read strace %e s" strace -c -o /dev/null ./out/graph_traverse --write 5 graphs/graph-rand-1M.bin 2>&1 | tail -1
  /usr/bin/time -f "mmap plain  %e s" ./out/graph_traverse_mmap --write 500 graphs/graph-rand-1M.bin 2>&1 | tail -1
  /usr/bin/time -f "mmap strace %e s" strace -c -o /dev/null ./out/graph_traverse_mmap --write 500 graphs/graph-rand-1M.bin 2>&1 | tail -1
done | tee results/strace_overhead.txt