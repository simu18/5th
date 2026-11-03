#import "report_style.typ": report, title-page
#show: report.with(lang: "en")

#title-page(
  org: "ITMO University",
  faculty: "Faculty of Software Engineering and Computer Systems",
  work: "Laboratory work No. 1",
  topic: "EXP-0 «Introductory experiment»",
  course: "Course «Operating Systems»",
  variant: "Variant: Write, Cache, 10M vs 1M, Rand",
  done-label: "Performed by:",
  student: "Rahaman Md Afifur (Рахаман Мд Афифур)",
  group: "group P3330, ISU 407793",
  teacher-label: "Teacher:",
  teacher: "Klimenkov Sergey Viktorovich (Клименков Сергей Викторович)",
  city-year: "Saint Petersburg, 2026",
)

#set page(numbering: "1", number-align: center)
#counter(page).update(2)

#outline(title: "Contents", indent: auto, depth: 2)
#pagebreak()

= Goal and variant

*Goal.* Measure and compare how fast the two provided programs walk through a graph stored in
a file and update it, and learn to run an OS experiment properly: describe and prepare the
environment, plan the number of runs, and process the results with statistics.

*Variant* «Write, Cache, 10M vs 1M, Rand»: both programs run in write mode (`--write`, every
visited node is updated), the system page cache is used (no `--no-cache`), the graph is a
chain in random physical order (`--topology chain`), and the compared factor is the *file
size*: 1 MiB vs 10 MiB. Question of the variant: *does size matter for a typical case on a
modern system?*

Objects of study: `graph_traverse` (access through `lseek()` + `read()`/`write()`) and
`graph_traverse_mmap` (the file is mapped into memory with `mmap()`).

= Work progress

All scripts, raw data, logs and figures:
#link("https://github.com/simu18/os-course/tree/lab-intro-exp/lab/intro-exp")
(branch `lab-intro-exp`). Every number below can be reproduced with the commands in Appendix A.

== System passport (step 4.1)

The experiment was run in a virtual machine. The guest sees virtual devices only, so the
physical parameters were taken from the host and are marked as such.

#figure(
  table(
    columns: (auto, 1fr, auto),
    align: (left, left, left),
    table.header([*Parameter*], [*Value*], [*Source*]),
    [Host], [MacBook Air, Apple M2: 8 cores (4 performance + 4 efficiency), 16 GB RAM, macOS 26.6.2], [`system_profiler` on host],
    [Hypervisor], [UTM, QEMU backend], [`systemd-detect-virt` = `qemu`],
    [Guest OS], [Ubuntu 26.04.1 LTS, kernel 7.0.0-38-generic, aarch64, PREEMPT_DYNAMIC], [`uname -a`, `os-release`],
    [vCPU], [4 vCPU, 1 thread/core, 1 socket; vendor «Apple», model name hidden («-»); cache sizes not reported], [`lscpu`, `lscpu -e`],
    [Memory model], [1 NUMA node, i.e. *UMA*], [`lscpu`, `numactl --hardware`],
    [RAM], [4 GiB configured, 3.3 GiB usable; swap 3.8 GiB], [`lshw`, `free -h`],
    [Page size], [4096 B], [`getconf PAGESIZE`],
    [Disk], [virtio `vda`, 25 GB, ext4; I/O scheduler `none`; physically an image file on the host's SSD], [`lsblk`, `df -hT`, host],
    [Disk type], [the guest reports `rotational = 1`, which is *not* real: virtio does not report the medium. SMART is unavailable (`Unable to detect device type`)], [`/sys/block/vda/...`, `smartctl`],
    [CPU frequency], [no `cpufreq` interface in the guest: governor and Turbo cannot be read or fixed], [`/sys/.../cpufreq`],
    [PMU (CPU counters)], [not available in the guest (`<not supported>`): cache and TLB misses cannot be counted], [`perf stat`],
    [Writeback (saving changed pages)], [`dirty_background_ratio` 10 % (start saving), `dirty_ratio` 20 % (block writers), `dirty_expire_centisecs` 3000 (save after 30 s); `swappiness` 60], [`sysctl`],
    [Toolchain], [Ubuntu clang 21.1.8, Python 3.14.4], [`clang --version`],
  ),
  caption: [System passport (full output: `logs/passport.txt`)],
)

== Environment preparation (step 4.2)

#figure(
  table(
    columns: (auto, 1fr),
    table.header([*Item*], [*Decision and reason*]),
    [Background load], [GUI apps closed; load average below 1 (`uptime`), all vCPUs ≈ 97 % idle (`mpstat`). Snapshots before/after each series: `logs/snapshot_*.txt`.],
    [CPU frequency (governor, Turbo)], [Cannot be set inside the VM (no `cpufreq`); macOS decides the frequency and whether a vCPU runs on a fast (P) or slow (E) core. Recorded as uncontrolled.],
    [Pinning to one CPU], [`taskset -c 2`: the program cannot move between CPUs. CPU 0 was avoided because it also handles network interrupts.],
    [Priority], [`renice -n -5` for the collection script; children inherit it.],
    [Cache state], [*Warm cache* (the variant). Fresh graphs, `sync`, then one untimed run of every configuration; caches are never dropped during a series.],
    [Data size vs RAM], [1 MiB and 10 MiB ≪ 3.3 GiB, so both files stay entirely in the page cache: 0 major page faults in all 248 final runs.],
    [perf access], [`kernel.perf_event_paranoid` = 1 set temporarily (default 4), reset on reboot.],
  ),
  caption: [Environment checklist],
)

== Test data and build

```sh
python3 ../util/graphgen.py -s 1M  --seed 427 --topology chain -b 0.5 --min-step-pages 2 --verify -o graphs/graph-rand-1M.bin
python3 ../util/graphgen.py -s 10M --seed 427 --topology chain -b 0.5 --min-step-pages 2 --verify -o graphs/graph-rand-10M.bin
clang -o out/graph_traverse src/graph_traverse.c     # README flags
clang -o out/graph_traverse_mmap src/graph_traverse_mmap.c
```

#figure(
  table(
    columns: (auto, auto, auto, auto, 1fr),
    table.header([*Graph*], [*Nodes*], [*Pages (4 KiB)*], [*Root node*], [*sha256 (first 12)*]),
    [1M], [43 689], [256], [9 668], [`6513e809b696`],
    [10M], [436 905], [2 560], [252 929], [`9cbbf5a3804a`],
  ),
  caption: [Generated graphs. Record = 24 B, header = 40 B, every jump ≥ 342 nodes (2 pages); 50.2 % forward / 49.8 % backward jumps]
)

Generating the graphs twice gave identical sha256 sums, so generation is reproducible. Since
`--write` modifies the files, the graphs were regenerated right before the final series.

== Baseline observations (step 4.3)

First, each program was run once with every flag combination, to see how it behaves (full table:
`logs/baseline_step4.3.txt`). *wall* = real elapsed time; *vcs* = voluntary context switches, i.e. how
many times the program had to stop and wait.

#figure(
  table(
    columns: (auto, auto, auto, auto, 1fr),
    table.header([*Program, flags*], [*1M wall, s*], [*10M wall, s*], [*vcs (10M)*], [*What it means*]),
    [read/write, read only], [0.04], [0.30], [1 248], [first run after creating the file is slower (warm-up)],
    [read/write `--no-cache`], [3.02], [30.50], [450 474], [every read goes to the disk: ≈ 70 µs each],
    [read/write `--write`], [0.03], [0.37], [1], [writes stay in RAM, nothing waits],
    [read/write `--write --no-cache`], [9.10], [90.51], [1 326 711], [3 disk operations per node],
    [mmap, any flags], [≤ 0.01], [0.01–0.04], [1–3], [too fast for one pass to be measured],
  ),
  caption: [Baseline: one run per configuration],
)

Main observations:
- *Number of system calls* (`strace -c`, one pass over 1M): `graph_traverse` makes 174 793
  syscalls (87 379 `lseek`, 43 691 `read`, 43 691 `write`), i.e. *4 per node*. `graph_traverse_mmap`
  makes only *37* in total: after `mmap()` the nodes are ordinary memory accesses.
- *Page faults of mmap.* mmap does not use syscalls per node, but the kernel steps in once per
  page: 272 page faults per pass for 1M (256 pages) and 2 721 for 10M (2 560 pages).
- *Memory.* mmap maps the whole file into the process, so its memory use grows with the file
  (2.1 → 11.4 MB); `graph_traverse` always uses 1.2 MB.
- *Warm-up.* Right after the graph was created, a run took 0.30 s; the next runs took 0.17 s.
- *Background load.* With `stress-ng --cpu 4` running, the time grew from 1.70 s to 2.54–2.77 s
  (+57 %), the program was interrupted 15× more often, and the runs became much less consistent.
- *perf stat.* The program uses the CPU all the time (it never waits for the disk) and does not
  move between CPUs. Hardware counters are not available in the VM.

== Hypothesis (step 4.4)

Both files fit in RAM, so the disk is not involved. Size can only matter through the CPU caches
and the TLB: 256 vs 2 560 pages, visited in random order.

- *H1 (read/write):* most of the time goes into the 4 syscalls per node, and they cost the same
  for any file size, so 10M will be at most *5 %* slower per node.
- *H2 (mmap):* there are no syscalls, only memory access, which depends on the caches. 10M will
  be *10–25 %* slower per node, and the difference will be in *user* time.
- *H3:* mmap will be more than 30× faster than read/write.

== Experiment plan (step 4.5)

#figure(
  table(
    columns: (auto, 1fr),
    table.header([*Item*], [*Decision*]),
    [What is measured], [Wall time of one run (`date`, nanosecond resolution), converted to *ns per node* = time ÷ (nodes × passes). `/usr/bin/time` also records user/sys time, page faults and context switches.],
    [Equal work], [10M has 10× more nodes, so 1M gets 10× more passes: read/write 50 vs 5, mmap 2000 vs 200. Every run then does the same amount of work (≈ 1.5–1.9 s).],
    [Cache], [Warm (files in RAM), the same for every run.],
    [Order], [62 rounds; in each round 1M and 10M run once, in a random order. Slow moments then hit both sizes equally.],
    [Warm-up], [The first 2 rounds are thrown away (decided before the final series).],
    [Outliers], [Removed only by the 1.5 × IQR rule; all are listed in Appendix B.],
    [Number of runs], [From a pilot of 10 runs (Table 6), the course formula N ≈ (t·s/E)² gives ≤ 24 runs for ±1 % precision. 60 were used, to be safe.],
    [Tools], [Only `/usr/bin/time` and `date` in the final series; `perf`/`strace` slow the program down.],
  ),
  caption: [Experiment plan],
)

#figure(
  table(
    columns: 6,
    table.header([*Pilot, 10 runs*], [*mean, s*], [*std. dev. s, s*], [*CV = s/mean*], [*runs needed (±1 %)*], [*Comment*]),
    [read/write 1M], [1.688], [0.024], [1.4 %], [8], [],
    [read/write 10M], [1.770], [0.044], [2.5 %], [24], [],
    [mmap 1M], [1.507], [0.037], [2.5 %], [24], [],
    [mmap 10M], [1.919], [0.255], [13.3 %], [680], [two slow early runs; ≈ 24 without them],
  ),
  caption: [Pilot series and the estimated number of runs],
)

The final series was run with `collect.sh` (Appendix C), with system snapshots before and after.
Raw data: `data/final_read.csv`, `data/final_mmap.csv` (one row per run); processing: `analyze.py`.

= Results

How to read the tables: *N* = runs kept; *95 % CI* = the range where the true mean lies with 95 %
confidence (±CI is its half-width in %); *ns/node* = the main result; *user/sys* = CPU time spent in
the program / in the kernel.

== Stage 1: `graph_traverse` (read/lseek/write)

#figure(
  table(
    columns: 9,
    table.header([*Size*], [*N*], [*mean, s*], [*95 % CI, s*], [*±CI*], [*median, s*], [*ns/node*], [*user, s*], [*sys, s*]),
    [1M × 50], [56], [1.7910], [1.7841–1.7979], [0.38 %], [1.7840], [*819.9*], [0.363], [1.414],
    [10M × 5], [55], [1.9289], [1.9177–1.9401], [0.58 %], [1.9173], [*883.0*], [0.366], [1.551],
  ),
  caption: [Stage 1 results (62 runs per size − 2 warm-up − 4/5 outliers)],
)

#figure(image("figures/density_graph_traverse.png", width: 82%),
  caption: [Stage 1: how the run times are distributed (bars = histogram, line = smoothed KDE)])

*Conclusion of stage 1.*
+ *Comparison.* 10M is *7.7 % slower per node* (median 7.5 %; with outliers 8.3 %). A Welch t-test
  (t = 21, p ≈ 0) confirms that the difference is real. This is *more than H1 predicted* (5 %).
  The reason is visible in the table: *user time is the same*, and the *whole difference is in sys
  time* (+9.7 %), the kernel. In this method the kernel copies the node data to and from the cached
  page; with 2 560 random pages that data fits worse in the CPU caches than with 256 pages.
  (Without hardware counters this explanation is based on the user/sys split.)
+ *Precision.* The confidence intervals (±0.38 % and ±0.58 %) do not overlap: the difference
  (0.138 s) is ≈ 12× larger than the interval half-width.
+ *Enough runs?* Yes: the formula needs 9 and 19 runs for ±1 %; there are 56 and 55. More runs
  would make the intervals narrower (∝ 1/√N) but would not change the conclusion.

== Stage 2: `graph_traverse_mmap`

#figure(
  table(
    columns: 9,
    table.header([*Size*], [*N*], [*mean, s*], [*95 % CI, s*], [*±CI*], [*median, s*], [*ns/node*], [*user, s*], [*sys, s*]),
    [1M × 2000], [57], [1.4942], [1.4821–1.5064], [0.81 %], [1.4723], [*17.10*], [1.177], [0.304],
    [10M × 200], [53], [1.7848], [1.7663–1.8033], [1.04 %], [1.7546], [*20.43*], [1.448], [0.323],
  ),
  caption: [Stage 2 results (62 runs per size − 2 warm-up − 3/7 outliers)],
)

#figure(image("figures/density_graph_traverse_mmap.png", width: 82%),
  caption: [Stage 2: how the run times are distributed])

#figure(
  table(
    columns: 5,
    table.header([*Per run*], [*read/write 1M*], [*read/write 10M*], [*mmap 1M*], [*mmap 10M*]),
    [minor page faults], [137], [137], [544 149], [544 265],
    [major page faults (disk)], [0], [0], [0], [0],
    [voluntary context switches], [1.02], [1.04], [1.35], [1.17],
    [involuntary context switches], [14.6], [16.3], [12.3], [14.5],
    [syscalls per pass], [≈ 174 800], [≈ 1 747 600], [≈ 7], [≈ 7],
  ),
  caption: [Page faults and context switches: read/write vs mmap],
)

*Conclusion of stage 2.*
+ *Comparison.* 10M is *19.4 % slower per node* (median 19.2 %; t = 26, p ≈ 0). *H2 is confirmed.*
  This time the difference is in *user* time (+23 %), because with mmap the program itself touches
  the data. The number of page faults is the same for both sizes by design.
+ *read/write vs mmap.* read/write makes ≈ 175 000 syscalls per pass and almost no page faults.
  mmap makes no syscalls per node; instead it has one page fault per page per pass (≈ 544 000
  per run, ≈ 0.56 µs each). Neither program waits for the disk: 0 major faults, ≈ 1 voluntary
  switch per run.
+ *Precision and enough runs.* The intervals (±0.81 % and ±1.04 %) do not overlap; the
  formula needs 38 and 57 runs, and there are 57 and 53.
+ *H3 is confirmed:* mmap is *48×* (1M) and *43×* (10M) faster than read/write.

As the task expected, stage 2 differs from stage 1: with read/write the size effect is small and
sits in the kernel; with mmap it is 2.5× larger (in %) and sits in the program itself.

== Stage 3: all series together

#figure(image("figures/ci_ns_per_node.png", width: 92%),
  caption: [Mean time per node; the whiskers are the 95 % confidence intervals])

#figure(image("figures/all_series_relative.png", width: 78%),
  caption: [All four series, as % of the 1M result of the same program])

#figure(image("figures/timeline.png", width: 100%),
  caption: [Every run in the order it was made: squares = warm-up, crosses = outliers])

- *The data is not normally distributed* (Shapiro–Wilk test p < 0.001): there is a tail of rare
  slow runs on the right. That is why the median is reported too, and why the results were
  checked with the outliers included. The conclusions are the same.
- *Outliers are VM noise:* some slow moments hit both sizes in neighbouring rounds (read/write
  rounds 52–54, mmap rounds 35–40). Because the order was mixed, both sizes were affected equally.
- *Order does not matter:* the first and second run of a round differ by less than the noise.
- *mmap 10M needed a longer warm-up* (rounds 1–8 are slower). The warm-up rule (2 rounds) was
  fixed in advance and not changed; the median gives the same 19 %.

== Do the measuring tools change the result?

#figure(
  table(
    columns: 4,
    table.header([*Tool vs plain `/usr/bin/time`*], [*read/write*], [*mmap*], [*Conclusion*]),
    [`perf stat` (10M, 20 pairs)], [+0.43 % (p = 0.70)], [+5.2 % (p = 0.18)], [no significant effect],
    [`strace -c` (1M, 3 runs)], [0.19 → 79.1 s, ≈ 410× slower], [0.40 → 0.87 s, ≈ 2.2×], [huge for syscall-heavy code],
  ),
  caption: [Overhead of the measuring tools],
)

`strace` stops the program at every system call, so read/write (≈ 874 000 syscalls) becomes ≈ 410×
slower, while mmap (only a few thousand syscalls) is barely affected. So how *intrusive* a tool is
depends on the program being measured. That is why the final runs used only `/usr/bin/time`.

= Conclusion

+ *Answer to the variant:* yes, the size matters even when the file is fully in RAM. With
  read/write, 10 MiB is 7.7 % slower per node than 1 MiB; with mmap, 19.4 % slower. The cause is the
  CPU caches and the TLB. The extra time appears where the code that touches the data runs: in the
  kernel for read/write, in the program for mmap. mmap is 43–48× faster than read/write overall.
+ *What turned out to be critical:* the page cache (writing without it was ≈ 245× slower),
  background load (+57 % time), warm-up after creating a file, equal work per run, and mixing the
  order of runs.
+ *What did not matter here:* the disk itself (0 major page faults: it was never used during the
  measured runs), `perf stat` overhead, and the order within a round.
+ *Not controlled (VM limits):* CPU frequency and whether macOS runs the vCPU on a fast or slow
  core; hardware counters are unavailable, so the cache/TLB explanation is based on user/sys time.

#pagebreak()
= Appendix A. Reproduction

```sh
cd lab/intro-exp
./build.sh                        # clang version + both programs
./gen_graphs.sh                   # graphs + sha256 (must match Table 3)
./passport.sh                     # logs/passport.txt
sync; ./snapshot.sh before_final
./collect.sh graph_traverse      62 data/final_read.csv
./collect.sh graph_traverse_mmap 62 data/final_mmap.csv
./snapshot.sh after_final
python3 analyze.py data/final_read.csv data/final_mmap.csv   # results/, figures/
./intrusive.sh 22 data/intrusive.csv
```

Files: `build.sh`, `gen_graphs.sh`, `passport.sh`, `snapshot.sh`, `collect.sh`,
`intrusive.sh`, `analyze.py`; data in `data/` (pilot, final, intrusiveness); logs in `logs/`
(baseline, perf/stress-ng, passport, snapshots); tables in `results/`; figures in `figures/`.

= Appendix B. Removed outliers (1.5 × IQR)

#figure(
  table(
    columns: 4,
    table.header([*Configuration*], [*Removed (round: wall, s)*], [*Count*], [*Common feature*]),
    [read/write 1M], [20: 2.020; 52: 1.895; 53: 1.913; 54: 1.867], [4], [user and sys both elevated],
    [read/write 10M], [11: 2.255; 16: 2.067; 19: 2.135; 41: 2.242; 54: 2.175], [5], [sys +6–19 %],
    [mmap 1M], [21: 1.701; 23: 1.684; 40: 1.772], [3], [user and sys both elevated],
    [mmap 10M], [3: 2.054; 6: 2.432; 7: 2.388; 8: 2.108; 14: 2.282; 27: 2.296; 37: 2.228], [7], [mostly early rounds],
  ),
  caption: [Outliers (`results/outliers.csv`)],
)

= Appendix C. Collection script `collect.sh`

```bash
#!/usr/bin/env bash
# Usage: ./collect.sh <graph_traverse|graph_traverse_mmap> <N> <out.csv>
set -euo pipefail
cd "$(dirname "$0")"
PROG=$1; N=$2; OUT=$3
CORE=2
if [ "$PROG" = "graph_traverse" ]; then
  declare -A ITER=( [1M]=50   [10M]=5 )
else
  declare -A ITER=( [1M]=2000 [10M]=200 )
fi
declare -A NODES=( [1M]=43689 [10M]=436905 )
sudo renice -n -5 -p $$ > /dev/null
for s in 1M 10M; do                                   # cache warm-up, untimed
  taskset -c $CORE ./out/$PROG --write ${ITER[$s]} graphs/graph-rand-$s.bin 2>/dev/null
done
echo "timestamp,program,size,flags,iter,nodes,core,round,pos,wall_s,user_s,sys_s,minflt,majflt,vcs,ics" > "$OUT"
for round in $(seq 1 "$N"); do
  pos=0
  for s in $(printf "1M\n10M\n" | shuf); do           # random order in every round
    pos=$((pos + 1))
    t0=$(date +%s%N)
    /usr/bin/time -f "%U,%S,%R,%F,%w,%c" -o /tmp/collect_time.txt \
      taskset -c $CORE ./out/$PROG --write ${ITER[$s]} graphs/graph-rand-$s.bin 2>/dev/null
    t1=$(date +%s%N)
    wall=$(awk -v a="$t0" -v b="$t1" 'BEGIN { printf "%.6f", (b - a) / 1e9 }')
    echo "$(date +%s),$PROG,$s,--write,${ITER[$s]},${NODES[$s]},$CORE,$round,$pos,$wall,$(cat /tmp/collect_time.txt)" >> "$OUT"
  done
  echo "round $round/$N done"
done
```
