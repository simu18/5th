# EXP-0 defense guide — Rahaman Md Afifur, P3330

Variant: **Write, Cache, 10M vs 1M, Rand**. Your numbers are in **bold** — learn those.

---

## 0. The 6 numbers to know by heart

| | 1M | 10M | 10M slower by |
|---|---|---|---|
| read/lseek/write, ns per node | **820** | **883** | **+7.7 %** (all of it in **sys** time) |
| mmap, ns per node | **17.1** | **20.4** | **+19.4 %** (all of it in **user** time) |

- mmap is **≈ 45× faster** (48× on 1M, 43× on 10M).
- **N = 60** runs per configuration (62 rounds − 2 warm-up), CI ±0.4–1 %.
- seed **427**, graphs **43 689** and **436 905** nodes, CPU **2**, warm cache, **0 major faults**.

---

## 1. Opening script (≈ 2 minutes, while showing the report)

Speak slowly and point at the page. You don't need to memorise it word for word; learn the order.

**English**

1. *(Title page)* "My variant is Write, Cache, 10M vs 1M, Rand. The question is: does file size
   matter when the file is cached and we modify random records?"
2. *(Passport, page 3)* "I ran it in an Ubuntu VM in UTM on a MacBook Air M2. Inside the VM some
   things are hidden: the CPU model, the frequency, and hardware counters. The disk says
   'rotational' but that's false: it's a virtual disk on the Mac's SSD. I took the real data
   from the host."
3. *(Method, page 5)* "To compare fairly, I gave the small file 10× more passes, so every run does
   the same number of node visits, and I compare nanoseconds per node. The cache is warm, both
   sizes run in random order in every round, the first 2 rounds are discarded, and I chose
   N = 60 from a pilot of 10 runs using the formula N = (t·s/E)²."
4. *(Figure 3)* "Result: with read/write, 10M is 7.7 % slower per node; with mmap, 19.4 %.
   The confidence intervals don't overlap. mmap is about 45 times faster overall."
5. *(Stage 1 conclusion)* "My hypothesis said read/write would differ by less than 5 %. It came
   out 7.7 %. The time split explains it: user time is identical, and the whole difference is in
   sys time. In read/write the kernel copies the data, so the kernel feels the bigger working set.
   In mmap the program touches the memory itself, so the difference is in user time."
6. *(Intrusiveness)* "perf stat added no measurable overhead, but strace made read/write 410×
   slower, because it stops at every one of ~175 000 syscalls per pass. mmap almost doesn't
   suffer, because it has almost no syscalls."
7. "Conclusion: even with no disk involved, size matters through the CPU caches and the TLB, and the
   access method decides how much."

**Русский (если попросит по-русски)**

1. «Мой вариант — Write, Cache, 10M vs 1M, Rand. Вопрос: важен ли размер файла, если файл в
   кэше и мы изменяем случайные записи?»
2. «Эксперимент — в виртуальной машине Ubuntu (UTM) на MacBook Air M2. В ВМ скрыты модель CPU,
   частота и аппаратные счётчики. Диск показывает rotational = 1, но это неправда: это
   виртуальный диск на SSD мака. Реальные данные я взял с хоста.»
3. «Чтобы сравнение было честным, маленькому файлу я дал в 10 раз больше проходов: каждый
   запуск посещает одинаковое число вершин, сравниваю наносекунды на вершину. Кэш тёплый,
   порядок 1M/10M в каждом раунде случайный, первые 2 раунда отбрасываю, N = 60 выбрал по
   пилоту из 10 запусков по формуле N = (t·s/E)².»
4. «Результат: у read/write 10M медленнее на 7,7 % на вершину, у mmap — на 19,4 %.
   Доверительные интервалы не пересекаются. mmap примерно в 45 раз быстрее.»
5. «Гипотеза для read/write была меньше 5 %, получилось 7,7 %. Объяснение: user time
   одинаковый, вся разница в sys — данные копирует ядро. У mmap к памяти обращается сама
   программа, поэтому разница в user.»
6. «perf stat заметных накладных расходов не дал, а strace замедлил read/write в 410 раз —
   он останавливается на каждом из ~175 тысяч вызовов за проход. mmap почти не пострадал.»
7. «Вывод: даже без диска размер важен — через кэши процессора и TLB, а насколько — зависит от
   способа доступа.»

---

## 2. Questions your friend got (most likely to be asked)

### Почему read/lseek медленнее mmap? (why is read/lseek slower than mmap)
- **read/write:** every node needs **4 system calls** (lseek, read, lseek, write). Each one is a
  trip into the kernel and back: switch to kernel mode, check arguments, find the page in the
  page cache, copy 24 or 8 bytes, return. That's ≈ 190 ns × 4 ≈ **820 ns per node**.
- **mmap:** the file is mapped into the program's memory once, and after that a node is a normal
  memory access, **≈ 17 ns**, with **no syscalls and no copying**. The kernel only steps in on a page
  fault, the first touch of each page in a pass (272 faults per pass for 1M).
- **Proof from my data:** strace showed **174 793 syscalls** for one pass of read/write vs **37**
  for the whole mmap program; sys time **1.41 s vs 0.30 s** per run.

### Какой командой понять, SSD или HDD? (how to tell SSD from HDD)
- `cat /sys/block/vda/queue/rotational` gives `0` = SSD, `1` = HDD (also `lsblk -d -o NAME,ROTA`).
- `sudo smartctl -a /dev/sda` prints "Rotation Rate: Solid State Device" or the RPM.
- `sudo lshw -class disk` shows the model.
- **My case:** the VM says `1`, but that's **wrong**. virtio doesn't pass the real type through, and
  smartctl can't read a virtual disk. The real disk is the Mac's SSD. To show it, run on the
  **Mac**: `system_profiler SPStorageDataType | grep -i medium` gives "Medium Type: SSD".
  **Do this before the defense and save the output.**

### Сравнить число вызовов через strace (compare syscall counts with strace)
- `strace -c ./out/graph_traverse --write 1 graphs/graph-rand-1M.bin` gives lseek 87 379,
  read 43 691, write 43 691, total **174 793** (4 per node + 7 extra: header, libc, 2 messages).
- The same for `graph_traverse_mmap` gives **37 in total**: open, fstat, mmap, munmap, close, 2
  messages, plus program start-up.
- Useful flags: `-c` gives a summary table, `-e trace=read,write,lseek` traces only those calls,
  `-f` follows child processes, `-o file` saves the output.

### Влияние фоновых процессов на метрики (effect of background processes)
- With `stress-ng --cpu 4` my run went **1.70 s → 2.54–2.77 s (+57 %)**.
- Involuntary context switches went **15 → 180–266**, because the scheduler took the CPU away.
- The spread of the runs went **0.01 s → 0.23 s**, i.e. the measurements became inconsistent.
- user + sys also grew by ≈ 20 %: when two processes share a CPU they evict each other's data from
  the CPU caches, and in a VM the vCPUs also compete for the M2's real cores.
- **That's why** I closed apps, pinned the process with taskset, used renice −5, interleaved the
  configurations and took snapshots before and after.

### Про кэши (many cache questions)
**The cache levels, from fastest to slowest:**
| Cache | Where | What it stores | Typical time |
|---|---|---|---|
| L1/L2/L3 | inside the CPU | recently used memory (64-byte lines) | 1–40 ns |
| TLB | inside the CPU | virtual → physical address translations | ~1 ns hit; a miss = page-table walk |
| **page cache** | RAM, managed by the kernel | copies of file pages (4 KiB) | ~100 ns |
| disk's own cache | inside the SSD | recent blocks | µs |

- **Page cache, reading:** `read()` checks the page cache first. A hit means a copy from RAM; a miss
  means reading from disk (≈ 70 µs on my VM).
- **Page cache, writing ("write-back"):** `write()` changes the page in RAM, marks it **dirty** and
  returns at once. Kernel flusher threads write it to disk later: after **30 s**
  (`dirty_expire_centisecs`), or when dirty pages reach **10 %** of RAM
  (`dirty_background_ratio`). At **20 %** (`dirty_ratio`) the writing program itself is blocked.
- **Clearing the cache:** `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches`, where 1 = page
  cache, 2 = dentries/inodes, 3 = both. `sync` comes first because dirty pages can't be dropped.
- **Checking the cache:** `fincore file`, `free -h` (column buff/cache), `/proc/meminfo` (Cached,
  Dirty).
- **`--no-cache`:** in graph_traverse it's `O_DIRECT`, which bypasses the **page cache** but not the
  CPU caches or the disk's own cache. It needs aligned 4 KiB blocks, so writing 8 bytes becomes
  read block + write block. In mmap it's only an `madvise` hint, and mmap still uses the page cache.
- **Readahead:** for sequential reads the kernel loads the next pages in advance. My graph is
  random with jumps of ≥ 2 pages, so readahead doesn't help.
- **Why is 10M slower if both are in the page cache?** Because of the **CPU caches and the TLB**: 2 560
  random pages fit worse than 256. My result: +7.7 % / +19.4 %.
- **Warm vs cold cache:** warm = data already in the page cache (my variant); cold = dropped before each
  run, which measures the disk.

### Какой метод быстрее, если файл больше оперативной памяти? (which method is faster if the file is bigger than RAM)
- Then the page cache can't hold the file. Pages get evicted and re-read from disk all the time,
  and for random access almost every node becomes a **disk read (≈ 70 µs on my disk)**.
- The disk then dominates both methods (70 µs ≫ 0.8 µs of syscalls), so **the 45× difference
  mostly disappears** and both become about equally slow.
- mmap can even become **worse**: every miss is a **major page fault**, a synchronous one-page
  read without batching. Fault-around/readahead may load useless neighbour pages for random
  access, the kernel decides on its own what to evict, and dirty pages must be written back
  before eviction. Databases avoid mmap for this reason; there's a known paper, "Are You Sure
  You Want to Use MMAP in Your DBMS?" (2022).
- read/pread gives more control: you can use `O_DIRECT`, your own cache, or large batched reads.
- **Say:** "I didn't measure it; I'd test it by limiting memory, e.g.
  `systemd-run --scope -p MemoryMax=4M ./out/...`, or with a file larger than 3.3 GiB."

---

## 3. Have this ready on the laptop (live demo)

Open: the report PDF, plus a VM terminal in `~/os-course/lab/intro-exp`.

```bash
./build.sh && ./gen_graphs.sh                         # rebuild + regenerate (same sha256)
strace -c ./out/graph_traverse --write 1 graphs/graph-rand-1M.bin        # 174 793 syscalls
strace -c ./out/graph_traverse_mmap --write 1 graphs/graph-rand-1M.bin   # 37 syscalls
/usr/bin/time -v ./out/graph_traverse_mmap --write 200 graphs/graph-rand-10M.bin 2>&1 | tail -20
lsblk -d -o NAME,ROTA,SIZE,MODEL; cat /sys/block/vda/queue/rotational
fincore graphs/*.bin; free -h
lscpu | head -20; nproc; numactl --hardware
./collect.sh graph_traverse 5 /tmp/demo.csv && cat /tmp/demo.csv          # quick re-run
python3 analyze.py data/final_read.csv data/final_mmap.csv                # recomputes everything
```

---

## 4. The 24 understanding questions

1. **Why many measurements if the program is deterministic?** The program is deterministic, but
   the system isn't: interrupts, other processes, migrations, CPU frequency, cache state, the host
   OS. My runs of the same configuration varied from 1.74 to 2.26 s. One run is a random sample;
   a series gives the mean and its uncertainty.
2. **Stages of an experiment, and typical mistakes.** Stages: passport → environment → baseline →
   hypothesis → plan → measurements → analysis → conclusion. Mistakes: conclusions from 1–3 runs,
   running configurations in blocks (drift), choosing warm-up or outliers after seeing the
   results, using intrusive tools in the final series, mixing warm and cold cache, comparing
   unequal work.
3. **Is the mean enough? What does the CI say?** No. The mean says nothing about how sure we are.
   The 95 % CI is the range that contains the true mean with 95 % confidence. If two CIs don't
   overlap, the difference is significant. Mine: ±0.38–1.04 %, not overlapping.
4. **Why the t-distribution and not the normal one?** We don't know the true spread; we estimate
   *s* from a finite sample. The t-distribution accounts for that extra uncertainty and gives a
   wider interval for small N. For N ≥ 30 the two are almost equal (t = 2.00 vs 1.96 for my N).
5. **What does time show? sys vs user?** real = stopwatch; user = CPU time in the program's code;
   sys = CPU time in the kernel on its behalf (syscalls, page faults). read/write: sys 1.41 s of
   1.79 s. mmap: user 1.18 of 1.49 s.
6. **Why not measure everything with perf?** It adds overhead (intrusiveness), it's heavy for many
   runs, and in my VM the hardware counters aren't supported. Use it for understanding, not for
   the final timing.
7. **What causes variation, can it be removed? Why interleave?** Causes: background processes,
   interrupts, scheduler, frequency/heat, caches, the host. It can only be reduced, not removed.
   Interleaving: if something slows the system for a while, it hits both configurations equally
   instead of only one. I saw this in rounds 52–54.
8. **Why prepare the environment instead of "normal" conditions?** To measure the program and not the
   noise. Prepared conditions are reproducible; "normal" ones change all the time.
9. **What are read()/seek() and mmap()?** read/write copy bytes between the file (via the page cache)
   and a program buffer, at a position set by lseek. mmap maps the file into the address space,
   so it's accessed as memory and the kernel loads pages on page faults.
10. **Why do read and write differ? With or without cache?** A write additionally makes pages dirty, which
    means later disk writeback, and in my program costs 2 extra syscalls per node. With cache: the write
    is cheap (only RAM). Without cache (O_DIRECT): the write is read-modify-write of a 4 KiB block, 3
    disk operations per node, so 9.10 s vs 3.02 s for a read (1M).
11. **What is intrusiveness?** The measuring tool changes what it measures. Mine: strace made
    read/write 410× slower. From life: a thermometer cools the water it measures; a person behaves
    differently when watched. Most intrusive: strace, then perf record. Least: /usr/bin/time, date, a
    timer inside the program.
12. **How does stress-ng change the results?** Wall time +57 %, involuntary switches ×15, spread ×23. It
    depends on the options: `--cpu` competes for CPU, `--vm` for memory (it can evict the page cache),
    `--io` calls sync (disk).
13. **Why the passport, what's in it? lscpu? UMA/NUMA?** For reproducibility and correct
    interpretation. It contains: OS/kernel, CPU, cores, caches, RAM, disk, VM or not, compiler.
    lscpu shows cores/threads, sockets, NUMA nodes, cache sizes, flags. **Mine is UMA** (1 NUMA node).
14. **How to drop file caches?** `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches`.
15. **Why taskset and nice?** taskset pins the process to one CPU, so no migrations and the CPU caches
    stay warm. nice/renice sets priority, so the scheduler prefers us. I used `taskset -c 2` and
    `renice -5`.
16. **Context switches: kinds, and the difference from migrations?** A context switch means the CPU stops
    running our process. Voluntary: we wait for something (I/O). Involuntary: the scheduler takes
    the CPU. A migration means the process moves to *another* CPU. A switch can happen without a
    migration.
17. **cache-misses?** The data wasn't in the CPU cache and had to come from RAM. It explains a slowdown
    with a bigger working set. In my VM it's not supported.
18. **%CPU?** The share of one CPU's time the process used. ≈ 100 % = CPU-bound; much less means it
    was waiting.
19. **Disk IO utility?** `iostat -x 1` (%util, await), `pidstat -d`, `vmstat` (bi/bo), `iotop`.
20. **What is an OS, why is it needed, can you do without it?** A program that manages the hardware and
    gives programs safe, uniform abstractions (processes, files, memory). Without an OS you write
    directly to the hardware, possibly through a HAL/firmware layer, as in microcontrollers.
21. **Two areas of an OS?** User space and kernel space. Reason: protection. Programs can't touch
    hardware or other programs' memory; only the kernel can.
22. **What is a syscall? Examples? How to see them?** A request from a program to the kernel. Mine:
    open, lseek, read, write, mmap, munmap, close. You see them with `strace`.
23. **Interrupt types (from BEVM / the lecture)?** Hardware (asynchronous: timer, disk, network),
    software / traps (synchronous: syscalls, page faults, division by zero), exceptions. Page faults
    are a synchronous exception.
24. **How to see all running applications?** `ps aux`, `top`/`htop`, `/proc`.

---

## 5. The 129 short questions (one-line answers)

| # | Answer |
|---|---|
| 1 | `/usr/bin/time -v` (also `perf stat`) |
| 2, 94 | seed **427** |
| 3 | CSV columns `program` and `size`; the file is `graphs/graph-rand-<size>.bin` |
| 4 | half-width/mean = 0.38–1.04 % → narrow |
| 5 | `lab/util/graphgen.py` |
| 6, 127 | `read()/lseek()/write()` vs `mmap()` |
| 7 | trick: it doesn't measure, it **generates load** |
| 8 | graph_traverse: `O_DIRECT` (bypasses page cache); mmap: only an `madvise` hint, still cached |
| 9 | mmap (RSS 11.4 MB vs 1.2 MB, because file pages are mapped into the process) |
| 10 | `-O2` itself (I used the README default: no flag = `-O0`) |
| 11, 55, 102 | `time` / `/usr/bin/time`; I also used `date +%s%N` |
| 12 | `fincore graphs/*.bin` (or `vmtouch`), `/proc/meminfo` |
| 13, 71, 99 | **4** series: 2 programs × 2 sizes |
| 14 | no: they'd compete for CPU and caches and distort each other |
| 15 | each node also gets value+1: 2 extra syscalls, dirty pages, the file changes |
| 16 | with `--no-cache` (1M read: 3.02 s vs 0.04 s) |
| 17 | hypothesis → plan → measurements → analysis → conclusion |
| 18, 45 | `taskset -c 2 <cmd>`; in `collect.sh` `CORE=2`; avoids migrations |
| 19 | no |
| 20 | `clang -o out/graph_traverse src/graph_traverse.c` |
| 21 | **1**: runs are strictly sequential |
| 22 | the 95 % confidence interval of the mean |
| 23, 58 | discard the first **K = 2** rounds, decided in advance (I saw a warm-up after creating the files) |
| 24, 60 | C |
| 25 | stress-ng |
| 26 | 4 final configurations (16 explored in the baseline) |
| 27, 41 | mean, sd, CI, median, IQR, N |
| 28 | CPU 2 (`CORE=2`) |
| 29 | one run is a random sample: no spread, no confidence |
| 30 | fastest: **mmap 1M** (17.1 ns/node) |
| 31, 108 | one process run: its wall time (→ ns per node) |
| 32 | program, size, flags, iterations, nodes, core, round, position, user, sys, faults, switches, timestamp |
| 33, 98 | generating the graphs comes first |
| 34 | each graph once per loop iteration |
| 35 | `lab/intro-exp/src/graph_traverse.c` |
| 36, 46 | mean ± t(0.975, N−1)·s/√N (scipy) |
| 37 | 62 rounds × 2 sizes × 2 programs = **248** final runs |
| 38 | `--no-cache` |
| 39 | allowed, if explained (my H1) |
| 40 | traversal time (ns per node) |
| 42 | how the access method and the file size affect traversal time |
| 43, 111 | random order in every round (`shuf`) |
| 44 | run without arguments (prints usage), `graphgen.py --help` |
| 47, 126 | with a cold cache **mmap** gets more major faults (each first touch of an uncached page); read() does I/O inside the syscall. In my warm runs: 0 for both |
| 48 | traverses a graph stored in a file and (with --write) updates every node |
| 49 | no universal value: computed from a pilot; 30 is a heuristic; I used 60 |
| 50 | clang |
| 51 | 4 (read/mmap × seq/rand in the README; read/mmap × 1M/10M in mine) |
| 52 | **no**: Shapiro–Wilk p < 0.001, right tail |
| 53 | builtin of bash vs a separate program with `-v`, `-f`, `-o`, faults, switches |
| 54 | HDD: random access much slower (head seek, ms); SSD: no seek |
| 56 | virtual virtio disk; rotational=1 is misleading; really the Mac's SSD (from the host) |
| 57, 95 | describe the environment first (passport, preparation, hypothesis, plan) |
| 59 | `collect.sh` once per program, 1M and 10M interleaved |
| 61 | small N and unknown variance → an honest, wider CI |
| 62 | `nproc`, `lscpu` |
| 63 | `/usr/bin/time -v`, `perf stat -e page-faults`, `ps -o min_flt,maj_flt` |
| 64 | the `time` package was already installed (`/usr/bin/time`); the bash builtin always exists |
| 65 | strace |
| 66, 106 | `lscpu`, `/proc/cpuinfo` |
| 67 | first runs while the system and caches settle; discarded |
| 68 | total/used/free/buff-cache/available RAM and swap; `-h` = human-readable units (KiB/MiB/GiB) |
| 69 | `--write` |
| 70, 122 | right before the final series (snapshot before), and after |
| 72, 93 | **before** |
| 73 | context switches and page faults |
| 74 | to avoid adjusting the method to the expected answer (confirmation bias) |
| 75, 115 | **2** graphs |
| 76 | characteristics (time) were measured; parameters (size, flags) were set |
| 77 | `<iterations>` |
| 78 | 2nd argument of `collect.sh` (62 rounds) |
| 79 | both: the loop in user space, syscalls/faults in the kernel; for read/write mostly kernel (sys 1.4 of 1.8 s) |
| 80 | `/usr/bin/time -v`, `perf stat` |
| 81 | to see what noisy measurements look like and why isolation matters |
| 82, 85 | they add overhead (strace: 410×) |
| 83 | statistical processing first |
| 84 | `graph-rand-1M.bin`, `graph-rand-10M.bin` |
| 86 | `free -h` |
| 87, 112 | Python |
| 88 | `--cpu N`: `stress-ng --cpu 4 --timeout 60s` |
| 89 | slowest: **read/write 10M** (883 ns/node) |
| 90 | Ubuntu 26.04.1 LTS (Linux 7.0) in a UTM/QEMU VM on macOS |
| 91 | cache-misses: data not in the CPU cache; page-faults: page not mapped; explain *why* it's slower |
| 92 | with stress-ng: more (involuntary) switches; more faults only if `--vm` causes memory pressure |
| 96 | `ITER=5` |
| 97 | task-clock, context-switches, cpu-migrations, page-faults, cycles, instructions, branches, branch-misses |
| 100 | syscalls ~175 000 → ~7 per pass, faults 137 → 544 000 per run, 45× faster, the size effect moved from sys to user |
| 101 | 1 file per run |
| 103 | so that drift doesn't hit only one configuration |
| 104 | 8 B per node into the page cache (1M: 43 689 × 8 ≈ 350 KB per pass); the disk later gets whole dirty pages (≤ the file size). With `--no-cache` a whole 4 KiB block per node |
| 105 | `sync; echo 3 \| sudo tee /proc/sys/vm/drop_caches` |
| 107 | `graph_traverse`, `graph_traverse_mmap` |
| 109 | 3 stages (README sections 0–9) |
| 110 | the range of the true mean; shows whether a difference is real |
| 113 | to recompute statistics, check outliers, reproduce |
| 114 | both before measuring (I built first, then generated) |
| 116 | the measured time (noise), parameters are fixed |
| 117 | to make the result reproducible and about the program, not the noise |
| 118 | the whole file: 1 MiB and 10 MiB |
| 119 | the same traversal logic, file format and options |
| 120 | `sequential` and `chain` (mine: chain for both, different sizes) |
| 121 | compare times + learn how to run an OS experiment |
| 123 | answer honestly: "I ran everything myself; I used AI as a tutor and for plots (the README allows it); I can explain every step." |
| 124 | trick: no error; the process may migrate between CPUs → more noise |
| 125 | it narrows ∝ 1/√N (4× N → half the width) |
| 128 | one final run ≈ 1.5–1.9 s; one pass over 1M ≈ 0.035 s |
| 129 | open, fstat, read the header; per node: lseek + read 24 B, lseek + write 8 B, go to the child; close |
