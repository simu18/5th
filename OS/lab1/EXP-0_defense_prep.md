# EXP-0 Defense Prep: Write, Cache, 10M vs 1M, Rand

How to use this file:
1. Learn **Part 1** (the opening speech) almost by heart. It is how you start.
2. Read **Part 2** once: it answers every `(Q: …)` you wrote in the report.
3. **Part 3** contains the questions your friend's teacher actually asked. Practise saying those answers out loud.
4. **Part 7** (key numbers) is the page to re-read just before you walk in.
5. Parts 5–6 are the full official question list, for revision.

---

## Part 1. How to start the defense (your opening speech)

You walk in with the laptop and the PDF open on page 3. Speak for **2–3 minutes**, pointing at the
report as you go. Stop when the teacher interrupts; that is normal.

### English version

> "My variant is **Write, Cache, 10M vs 1M, Rand**. Both programs update every node they visit,
> the page cache is on, the graph is a random chain, and the factor I compare is the **file
> size**: 1 MiB versus 10 MiB.
>
> *(passport)* I ran it in an **Ubuntu VM in UTM on a MacBook Air M2**. Because it's a VM, some
> things can't be seen or controlled from inside: the guest reports the disk as rotational, but it's
> really a file on the Mac's SSD, there's no CPU frequency control, and perf hardware counters are not
> supported. I wrote all of that in the passport and took the host data from macOS.
>
> *(environment)* I pinned the program to CPU 2 with `taskset`, raised its priority with `renice -5`,
> closed background apps, and used a **warm cache**: fresh graphs, `sync`, and one untimed run before
> each series.
>
> *(baseline)* In the first runs I saw that `graph_traverse` makes **4 syscalls per node** (lseek,
> read, lseek, write): 174,793 syscalls for one pass of the 1M graph. The mmap version makes only 37
> syscalls in total. Without the cache, writing 10M took 90 s instead of 0.37 s. With `stress-ng` in
> the background, the time grew by 57 %.
>
> *(plan)* Bigger files obviously take longer, so I made every run do the **same amount of work**:
> the 1M graph gets 10 times more passes than the 10M graph. I compare **nanoseconds per node**. I ran
> 62 rounds per program, with 1M and 10M in **random order in each round**, threw away the first 2
> rounds as warm-up, and removed outliers with the 1.5×IQR rule. N was computed from a pilot series of
> 10 runs.
>
> *(results)* Result: with read/write, 10M is **7.7 % slower** per node. That is more than my hypothesis
> of 5 %, and the whole difference is in **sys** time, the kernel. With mmap, 10M is **19.4 % slower**,
> and the difference is in **user** time. mmap is about **45 times faster** than read/write. The
> confidence intervals don't overlap.
>
> *(conclusion)* So size matters even when everything is in RAM, because of the CPU caches and the
> TLB. The extra cost appears wherever the code that touches the data runs: in the kernel for
> read/write, in the program for mmap."

### Russian version (if the defense is in Russian)

> «Мой вариант — **Write, Cache, 10M vs 1M, Rand**: обе программы изменяют каждую посещённую
> вершину, страничный кэш включён, граф — случайная цепочка, а сравниваю я **размер файла**: 1 МиБ
> и 10 МиБ.
>
> *(паспорт)* Эксперимент выполнен в **виртуальной машине Ubuntu в UTM на MacBook Air M2**. Из
> гостевой системы часть параметров не видна: диск показывается как вращающийся, хотя на самом деле
> это файл на SSD мака, частотой процессора управлять нельзя, аппаратные счётчики perf не
> поддерживаются. Всё это указано в паспорте, данные хоста взяты из macOS.
>
> *(окружение)* Процесс закреплён на CPU 2 через `taskset`, приоритет повышен через `renice -5`,
> фоновые программы закрыты, кэш **тёплый**: свежие графы, `sync` и один неизмеряемый запуск перед
> серией.
>
> *(ознакомительные измерения)* `graph_traverse` делает **4 системных вызова на вершину** (lseek,
> read, lseek, write) — 174 793 вызова за один проход по 1M. Версия с mmap делает всего 37 вызовов.
> Без кэша запись 10M заняла 90 с вместо 0,37 с, а с `stress-ng` в фоне время выросло на 57 %.
>
> *(план)* Чтобы сравнение было честным, каждый запуск делает **одинаковую работу**: граф 1M
> проходится в 10 раз больше раз, чем 10M, и я сравниваю **наносекунды на вершину**. 62 раунда на
> программу, в каждом раунде 1M и 10M в **случайном порядке**, первые 2 раунда отброшены как прогрев,
> выбросы удалены по правилу 1,5×IQR, N рассчитан по пилотной серии из 10 запусков.
>
> *(результаты)* С read/write 10M медленнее на **7,7 %** на вершину — больше, чем я предполагал (5 %),
> и вся разница в **sys**, то есть в ядре. С mmap 10M медленнее на **19,4 %**, разница в **user**.
> mmap быстрее read/write примерно в **45 раз**. Доверительные интервалы не пересекаются.
>
> *(вывод)* Размер важен даже когда всё в ОЗУ — из-за кэшей процессора и TLB. Дополнительная
> стоимость появляется там, где выполняется код, работающий с данными: в ядре для read/write и в
> самой программе для mmap.»

**Tip:** if he stops you with a question, answer it and say "shall I continue?" («продолжить?»).
Don't read from the screen; point at the table or graph and say the number.

---

## Part 2. Answers to your `(Q: …)` questions in the report

### Q1. How do `lseek()` + `read()` / `write()` work?

A file is a long row of bytes. For every open file the kernel remembers **a position**: a cursor
saying "the next byte I'll read or write is number X".

- `lseek(fd, X, SEEK_SET)` moves the cursor to byte X. Nothing is read; it only moves the cursor.
- `read(fd, buf, 24)` copies 24 bytes **from the file at the cursor into the program's memory**
  `buf`, then moves the cursor forward by 24.
- `write(fd, buf, 8)` copies 8 bytes **from the program's memory into the file at the cursor**.

`fd` (file descriptor) is just a number the kernel gave us at `open()`, like a ticket number.

What `graph_traverse` does for every node:
```
lseek(fd, 40 + i*24)    -> go to node i
read(fd, buf, 24)       -> get value, degree, child
lseek(fd, 40 + i*24)    -> go back to the same place
write(fd, &value+1, 8)  -> save the new value
i = child               -> next node
```
That's **4 syscalls per node**. Each syscall is a trip: user mode → kernel mode → back (≈ 0.2 µs).

With the cache on, `read` does not touch the disk: the kernel finds the page in the **page cache**
(RAM) and copies 24 bytes from it. `write` copies 8 bytes into that page and marks it **dirty**; the
kernel saves it to disk later.

**mmap** is different: `mmap()` makes the whole file look like an array in the program's memory. After
that the program just does `p[offset] = …`, which is an ordinary memory access with no syscall.

### Q2. What is PMU?

**Performance Monitoring Unit**: a set of special counters **inside the CPU** that count hardware
events, such as cycles, instructions, cache misses and TLB misses. `perf stat -e cache-misses` reads
these counters. In our VM, QEMU doesn't give the guest access to the M2's PMU, so perf prints
`<not supported>`. Software counters, which the kernel keeps itself (page faults, context switches),
still work.

### Q3. What are `dirty_ratio`, `dirty_background_ratio`, `dirty_expire_centisecs`, `swappiness`?

They control when the kernel saves **dirty pages** (pages changed in RAM but not yet on disk):

| Setting | Our value | Meaning |
|---|---|---|
| `dirty_background_ratio` | 10 | when dirty pages reach 10 % of memory, a **background** kernel thread starts saving them; the program doesn't wait |
| `dirty_ratio` | 20 | at 20 %, the **program itself is blocked** in `write()` until enough is saved |
| `dirty_expire_centisecs` | 3000 | any page that has been dirty for **30 s** is saved, even if the limits aren't reached |
| `swappiness` | 60 | how willingly the kernel moves program memory to swap instead of dropping file cache |

Why they matter for us: our files are only 1 and 10 MiB, far below 10 % of RAM, so **the program
never waits for the disk**. That's why `--write` with cache is so fast.

### Q4. What are the CPU governor and Turbo?

Modern CPUs **change their speed (frequency)** all the time to save power.
- The **governor** is the Linux policy that chooses the frequency: `performance` (always max),
  `powersave`, `schedutil` (adapts to load). For experiments you want `performance`, so the speed
  doesn't change between runs.
- **Turbo Boost** temporarily raises the frequency above normal while the chip is cool.

Both cause run-to-run variation. **In our VM neither exists** (no `cpufreq` folder), and macOS decides
the real speed and also whether our vCPU runs on a fast (P) or slow (E) core. So it's an uncontrolled
factor, and it's written in the report.

### Q5. What is pinning?

Normally the scheduler can move a process to another CPU at any moment (a **migration**). After a
move, the data the process had in that CPU's L1/L2 cache is lost, so it runs slower for a while.
**Pinning** = `taskset -c 2 ./program` → the process may run **only on CPU 2**. That removes
migrations, so the results are more stable. We chose CPU 2 because CPU 0 handles extra interrupts
(network).

### Q6. What do "wall" and "mmap" mean in the table?

- **wall time** (wall-clock time) is the real time from start to finish, as if measured with a clock
  on the wall or a stopwatch. It includes everything: computing, waiting, being interrupted.
- **mmap** in that table is short for the program `graph_traverse_mmap`, the version that uses `mmap()`.
- Related terms: **user time** is the CPU time spent running the program's own code; **sys time** is
  the CPU time the kernel spent working for it (syscalls, page faults).

### Q7. The perf stat line, and voluntary vs involuntary context switches

A **context switch** happens when the CPU stops running our process and runs something else.
- **Voluntary (vcs):** our process **gives up** the CPU itself, because it has to wait, for example
  for the disk. `--no-cache` had 450,474 of them, one per disk read.
- **Involuntary (ics):** the scheduler **takes** the CPU away (our time slice ended, or someone else
  needed it). They're a sign of competition and noise: 13–17 when quiet, 180–266 with `stress-ng`.

The perf line, piece by piece:
- `task-clock ≈ elapsed`: the process used the CPU almost 100 % of the time it existed, so it never
  waited for anything. "CPU-bound" means the speed is limited by the CPU, not the disk.
- `cpu-migrations 0–1`: how many times the process moved to another CPU. The 1 comes from `taskset`
  itself. It starts on some CPU, moves itself to CPU 2, and only then starts our program. After that
  there are 0 moves.
- `hardware events not supported`: the PMU (Q2) isn't available in the VM.

### Q8. What is H, and why do we need a hypothesis?

H = **Hypothesis**: a prediction written **before** the final measurements. We need it because:
- It forces you to think about the mechanism: what the OS will actually do.
- It protects against "explaining anything afterwards". If the result differs from the prediction,
  you learn something (like our H1).
- The README requires it (step 4.4).

Our three:
- **H1:** for read/write, size barely matters (≤ 5 %), because the 4 syscalls per node cost the same for
  any file size. Result: **7.7 %**, so *not confirmed*, and we explained why.
- **H2:** for mmap, size matters (10–25 %), because there are no syscalls and only memory access is left,
  which depends on caches and the TLB. Result: **19.4 %**, *confirmed*.
- **H3:** mmap is more than 30× faster. Result: **43–48×**, *confirmed*.

### Q9. The whole experiment plan, in simple words

1. **What we measure:** how long one run of the program takes (wall time). We divide it by the number of
   nodes visited, giving **ns per node**, the cost of one step.
2. **Equal work:** 1M has 43,689 nodes and 10M has 436,905 (10× more). If both were walked once, 10M would
   obviously take 10× longer, which tells us nothing. So 1M is walked 10× more often (read/write: 50 vs 5
   passes; mmap: 2000 vs 200). Every run then visits about **2.18 million** (read/write) or **87 million**
   (mmap) nodes and lasts ~1.5–1.9 s.
3. **Cache:** always warm (files in RAM), as the variant says.
4. **Order:** a "round" = one run of 1M + one run of 10M, in **random order**. We did 62 rounds. That way,
   if something slows the computer for a minute, both sizes are hit equally (interleaving).
5. **Warm-up:** the first 2 rounds are thrown away, because the first runs after creating a file are
   slower. We decided this **before** looking at the results.
6. **Outliers:** a run is removed only by a fixed rule (1.5×IQR), and every removed run is listed.
7. **How many runs (N):** we did 10 trial runs (the "pilot") to see how much the results vary, then used
   the formula to see how many runs give ±1 % precision. It said ~24 at most; we chose 60, to be safe.
8. **Light measuring:** in the final runs only `/usr/bin/time` and `date`, because heavy tools (perf,
   strace) slow the program down.

### Q10. The pilot table: mean, s, CV, N

| Word | Meaning | Example (read/write 10M) |
|---|---|---|
| **mean** | the average of the 10 runs | 1.770 s |
| **s** | standard deviation: the typical distance of a run from the average (how "spread out" the runs are) | 0.044 s |
| **CV** | coefficient of variation = s ÷ mean, the spread as a % | 0.044 / 1.770 = 2.5 % |
| **N for E = 1 %** | how many runs we need so that the mean is known to ±1 % | 24 |
| comment for mmap 10M | two very slow early runs inflated s to 0.255; without them N ≈ 24 | |

### Q11. The stage 1 table and the distribution graph

Each row is one configuration after cleaning:
- **N** is how many runs were kept (62 − 2 warm-up − outliers).
- **mean wall** is the average run time. **median** is the middle run: half are faster, half slower.
  The median is less sensitive to rare slow runs.
- **95 % CI** (confidence interval) is the range where the *true* average lies with 95 % certainty.
  **±CI** gives that range as a % of the mean (0.38 % = very precise).
- **ns/node** is the main result: 819.9 vs 883.0.
- **user / sys** shows where the CPU time went: the program vs the kernel.

**The graph (histogram + KDE):**
- The x-axis is ns per node; the y-axis shows how often runs land there.
- The **bars** (histogram) count runs in small bins. The **smooth curve** (KDE) is a smoothed version of
  the bars: every run adds a small bump, and the bumps are summed.
- Blue = 1M, orange = 10M. **The two hills are clearly separated**, so 10M really is slower; it's not luck.
  The long tail to the right is a few slow runs (noise); there are never unusually fast ones.

### Q12. What is the Welch t-test?

A statistical test that answers: "are these two averages **really** different, or could the difference
be random noise?" It compares the difference of the means with how noisy the data is.
- **t** is the difference measured in "noise units". t = 21 means the difference is 21 times bigger than
  its uncertainty, which is huge.
- **p** is the probability of seeing such a difference **if there were no real difference**. p ≈ 0 means
  it's practically impossible by chance.
- "Welch" is the version that doesn't assume both series have the same spread (ours don't).

### Q13. What is the CI half-width?

The CI is written as **mean ± h**. The **half-width h** is that ± part.
Example: read/write 1M is 1.7910 s ± 0.0069 s, so the interval is 1.7841–1.7979, and h / mean = 0.38 %.
Formula: **h = t × s / √N** (t ≈ 2.00 for N ≈ 55).
"The intervals don't overlap" means the 1M interval ends (1.7979) before the 10M interval starts (1.9177).

### Q14. The "Sufficiency" calculation

Formula from the course method: **N = (t × s / E)²**, where E is the precision we want.
We want E = 1 % of the mean.

read/write 10M: s = 0.0415, mean = 1.9289, so E = 0.0193 s and t ≈ 2.00.
N = (2.00 × 0.0415 / 0.0193)² = (4.30)² ≈ **19**. We have 55 > 19 ✔

read/write 1M: s = 0.0256, E = 0.0179 → N = (2.00 × 0.0256 / 0.0179)² = (2.86)² ≈ **9**. We have 56 ✔

Meaning: we did enough runs. More runs would make the interval narrower (it shrinks like 1/√N: 4× more
runs = half as wide), but the conclusion "10M is slower" wouldn't change.

### Q15. The stage 2 table and graph

Read it the same way as Q11, for `graph_traverse_mmap`. Notice the difference from stage 1:
**user** time grows (1.177 → 1.448 s), while **sys** barely changes (0.304 → 0.323 s). The page-fault
table below it shows mmap has about 544 thousand minor page faults per run, the same for 1M and 10M
(by design).

### Q16. The three stage 3 graphs

1. **Mean time per node with 95 % CI** (two panels): each dot is the average ns/node, and the small
   vertical bar ("whisker") is the 95 % CI. Left = read/write (820 → 883 ns), right = mmap (17.1 → 20.4 ns).
   They're separate panels because the scales differ 40×. **The whiskers are short and far apart**, so the
   difference is real.
2. **All four series relative to 1M**: everything is shown as a % of the same program's 1M result.
   1M = 100 % for both; read/write 10M ≈ 108 %; mmap 10M ≈ 119 %. It shows at a glance that **size hurts
   mmap more (in %)**.
3. **Timeline**: every single run in the order it was done (x = round number, y = seconds). Squares are
   the 2 warm-up rounds (thrown away); crosses are outliers. Blue (1M) is always below orange (10M), and
   some slow moments hit both colours at the same time (rounds 52–54). That's VM noise, and it's why we mix
   the order.

### Q17. What is Shapiro–Wilk?

A test that answers: "does this data look like a **normal distribution** (the bell curve)?" Small p
(< 0.05) means **not normal**. We got p < 0.001 for all four series, because of the long right tail of
slow runs. That's why we also report the **median**, and why the course says you can't just assume
"everything is normal".

### Q18. The intrusiveness table

"Intrusiveness" means how much the measuring tool **changes** what it measures.
- **perf stat vs `/usr/bin/time`** (20 pairs of runs): read/write 1.9335 → 1.9418 s (+0.43 %, p = 0.70);
  mmap +5.2 % (p = 0.18). A large p means the difference **could be just noise**: perf's overhead is too
  small to detect with 20 runs.
- **strace vs plain** (3 runs): read/write goes from **0.19 s to 79 s, ~410× slower**! strace stops the
  program at every one of its ~874,000 syscalls. mmap: 0.40 → 0.87 s (only ~2×), because mmap makes very
  few syscalls.
- The lesson: **the same tool can be harmless or terrible, depending on the program**. That's why the
  final measurements used only `/usr/bin/time`.

---

## Part 3. The teacher's known questions (from your friend's defense)

### "Why is read/lseek slower than mmap (in your variant)?" ⭐ most likely

> **Per node, read/write does 4 system calls (lseek, read, lseek, write). Each one switches the CPU from
> user mode to kernel mode and back, checks the arguments, looks up the page in the page cache and copies
> the data: ≈ 200 ns each, ≈ 820 ns per node. mmap maps the file into the address space once; after that
> a node is an ordinary memory read/write with no kernel involved. The kernel only steps in on a page
> fault, once per page per pass (272 faults per pass vs 174,793 syscalls per pass for 1M). Result: 17.1
> vs 819.9 ns per node, ≈ 48× faster. You can see it in the time split: read/write spends 80 % in sys,
> mmap 80 % in user.**

### "What command shows whether the disk is SSD or HDD?"

```bash
lsblk -d -o NAME,ROTA,MODEL          # ROTA: 0 = SSD/NVMe (no rotation), 1 = HDD
cat /sys/block/vda/queue/rotational  # the same flag for one disk
sudo smartctl -i /dev/sda            # model, "Rotation Rate: Solid State Device" or "7200 rpm"
sudo lshw -class disk -short         # model name
```
> **Important for you:** in my VM `rotational = 1` (it looks like an HDD), but that's **wrong**: the
> virtual virtio disk doesn't report the real medium. The real disk is the Mac's SSD. On macOS:
> `diskutil info disk0 | grep -i "solid state"` → `Solid State: Yes`.

*(Run that macOS command once before the defense so you can say you checked.)*

### "Compare the number of calls with strace"

```bash
strace -c ./out/graph_traverse      --write 1 graphs/graph-rand-1M.bin
strace -c ./out/graph_traverse_mmap --write 1 graphs/graph-rand-1M.bin
```
> **read/write: 87,379 lseek + 43,691 read + 43,691 write = 174,793 syscalls, i.e. 4 per node (plus a few
> for the header, loading libc and 2 progress messages). mmap: 37 syscalls in total; the only file-related
> ones are open, fstat, mmap, close and munmap, and there are no syscalls per node.** Also: strace itself
> makes read/write ~410× slower, because it stops the process at each syscall.

### "How do background processes affect the metrics?"

> **With `stress-ng --cpu 4` (all 4 vCPUs busy): wall time +57 % (1.70 → 2.54–2.77 s), involuntary context
> switches 13–17 → 180–266, and the spread of the runs 0.01 → 0.23 s (23×). User + sys also grew ~20 %,
> because the two processes evict each other's data from the CPU caches. So background load hurts both the
> average and the **repeatability**. Pinning, closing apps and interleaving the configurations protect
> against it.**

Possible follow-ups:
- "Which metric shows it best?" → involuntary context switches (`ics`, `%c` in `/usr/bin/time`).
- "Why didn't the time double?" → our process is pinned but the stress workers are not, so the scheduler
  moves them around and CPU 2 is shared only part of the time.

### "Which method is faster if the files are bigger than RAM?" ⭐ think-question

> **Then the page cache can't hold the file, and every access to a page that isn't in RAM needs a disk read
> (~70 µs on my VM's disk), about 100× more than the whole per-node cost now. Both methods become limited
> by the disk, so the 45× difference shrinks a lot: both pay about one disk read per random jump.**
> - **mmap** gets **major page faults**: the process stops until the page is read. With random access,
>   readahead doesn't help. With `--write`, dirty pages must be written back before they can be evicted,
>   so the program can get throttled at `dirty_ratio`.
> - **read/write** also loads pages into the cache, inside the syscall. It can use `O_DIRECT`
>   (`--no-cache`), but then *every* access goes to disk (we measured ≈ 70 µs per read, 3 ops per write).
> - **My expectation:** mmap is still slightly faster (no syscall overhead), but the gap is small compared
>   with the disk time. On an HDD, seek time (~5–10 ms) would dominate everything.
> - This is **not measured** in my experiment. It could be tested by limiting memory:
>   `sudo systemd-run --scope -p MemoryMax=4M ./out/graph_traverse_mmap --write 1 graphs/graph-rand-10M.bin`

### "Questions about caches" (prepare all of these)

| Question | Answer |
|---|---|
| What is the page cache? | RAM where the kernel keeps copies of file pages (4 KiB each). Reading from it means no disk access. In `free -h` it's the `buff/cache` column. |
| What happens on `write()` with the cache? | The data is copied into the cached page, the page is marked **dirty**, and `write()` returns immediately. A kernel thread saves it later (at ≥ 10 % dirty or after 30 s). |
| And with `--no-cache`? | `graph_traverse` opens the file with `O_DIRECT`: it bypasses the page cache and reads/writes whole aligned blocks directly on the disk, so the program waits every time. One write = read the block + write the block. |
| `--no-cache` for mmap? | mmap **can't** bypass the cache, because it maps page-cache pages. The flag only adds `madvise(MADV_RANDOM)` (no readahead), and at the end `msync` + `MADV_DONTNEED` (a hint to drop the pages). That's why it changed almost nothing. |
| How do you clear the cache? | `sync; echo 3 \| sudo tee /proc/sys/vm/drop_caches` (1 = page cache, 2 = dentries/inodes, 3 = both). `sync` comes first, to save the dirty pages. |
| How do you see that a file is cached? | `fincore file` (pages in cache), `free -h` (`buff/cache`), `/proc/meminfo` (`Cached`, `Dirty`). |
| Warm vs cold cache? | Warm = the data is already in RAM (measures memory/CPU speed). Cold = cache cleared before each run (measures the disk). Never mix them inside one series. |
| Why warm in my variant? | The variant is "Cache", and files of 1/10 MiB ≪ 3.3 GiB of RAM always fit. **Proof: 0 major page faults** in all 248 runs. |
| What are CPU caches? | Small, very fast memory inside the CPU (L1 ≈ 1 ns, L2 ≈ 3–5 ns, L3/SLC ≈ 10–20 ns, vs RAM ≈ 100 ns). Recently used data is kept there. |
| What is the TLB? | A cache of address translations (virtual → physical page). On a TLB miss the CPU has to walk the page tables, which is slower; in a VM there are two levels of tables. |
| Why is 10M slower if everything is in RAM? | 2,560 random pages don't fit in the CPU caches/TLB as well as 256 pages do, so there are more misses. We couldn't count the misses (no PMU), but the user/sys split shows **where** the extra time goes. |
| Minor vs major page fault? | Minor: the page is already in RAM and the kernel only maps it (≈ 0.5 µs). Major: the page must be read from disk (≈ ms). |
| Why does mmap have 272 faults per pass for 1M? | The file has 256 pages. The first **write** to each page faults (the kernel marks it dirty): 256. Plus 16 read faults, because on a read fault the kernel maps 16 pages at once ("fault-around"): 256 / 16 = 16. |
| What is readahead? | When the kernel sees sequential reading, it loads the next pages in advance. It's useless for our random jumps (each ≥ 2 pages away). |
| Why did the first runs after generation take longer? | The new file's pages were still dirty and being written to disk, so the first runs waited (vcs = 1248). Fixed with `sync`, the warm-up run and discarding 2 rounds. |

---

## Part 4. Other likely "think" questions about *your* work

| Question | Short answer |
|---|---|
| Why did H1 fail? | We expected ≤ 5 % and got 7.7 %. User time is the same and sys is +9.7 %: the **kernel** copies the data to and from the page and updates its metadata, and with 2,560 pages that is slower (caches/TLB). |
| Why equal work instead of the same number of iterations? | Otherwise 10M simply has 10× more nodes, which is a trivial result. Equal work compares the cost **per node**. |
| Why ns per node? | It's one number that doesn't depend on file size or on the number of passes. |
| Why 62 rounds? | The pilot (N = 10) and the formula said ~24 runs are needed for ±1 %; 60 adds a safety margin for heavy tails; +2 for warm-up. |
| Why K = 2? | We saw it in the baseline: the first runs after creating the file were slower. It was fixed **before** the final run. |
| Why random order (shuf) in each round? | Drift protection: noise or heating over time hits both sizes equally. You can see it in the timeline (rounds 52–54). |
| Why remove outliers? Isn't that cheating? | Only by a fixed rule (1.5×IQR), all of them listed in Appendix B, and the conclusion holds **with** them too (8.3 % and 22.2 %). |
| Why is the distribution not normal? | A run can't be faster than the minimum, but rare interruptions add delay, so there's a tail to the right. Shapiro–Wilk p < 0.001. |
| Why `renice -5`? | So the scheduler prefers our process over normal background tasks (nice 0). Negative values need root. |
| Why `date +%s%N` and not just `/usr/bin/time`? | `/usr/bin/time %e` rounds to 10 ms; `date` gives nanoseconds. |
| Why compile without `-O2`? | Exactly as in the README, so the teacher can reproduce it. `-O2` would speed up the user part (mostly mmap). |
| Why does mmap have more page faults but is still faster? | A fault happens once per page per pass (≈ 0.56 µs each). read/write pays 4 syscalls for **every node**, and there are ~170 nodes per page. |
| What is in a graph node? | 24 bytes: value (8), degree (4), reserved (4), child (8). The header is 40 bytes. Node i is at byte 40 + 24·i. |
| What does `--min-step-pages 2` do? | Every jump goes ≥ 2 pages away (≥ 342 nodes), so consecutive nodes are never on the same page. That gives real random access. |
| Why seed 427? | It's from the README. The same seed gives the same file (same sha256), so the experiment is reproducible. |
| Is the noise in a VM acceptable? | For a lab, yes, as long as it's stated. Our CIs are ±0.4–1 %, far smaller than the effects of 7.7 % and 19.4 %. |
| What if you run without `taskset`? | There's no error, but the process may migrate between CPUs → more noise (lost caches). The result is still valid but more scattered. |

---

## Part 5. The 24 understanding questions (official list)

1. **Why a series of measurements, if the program is deterministic?** The program is deterministic, but the
   environment isn't: interrupts, other processes, migrations, CPU frequency and temperature, cache state,
   the host (in a VM). Runs differ (ours by ±1–3 %), so a single run can be unlucky. A series separates the
   real effect from the noise and lets us compute a CI.
2. **Stages of an experiment and typical mistakes.** Goal → system passport → environment preparation →
   baseline → hypothesis → plan (metric, N, order, warm-up) → measurements → statistics → conclusions.
   Typical mistakes: conclusions from 1–3 runs, no hypothesis, mixing cold and warm cache, running
   configurations in blocks instead of interleaved, heavy tools (perf/strace) during measurement, removing
   "ugly" points without a rule, choosing the warm-up after looking at the data, background load.
3. **Can you conclude from the mean alone? What does the CI say?** No: the mean says nothing about how
   precise it is. The CI shows where the *true* mean lies (with 95 % confidence). If two CIs don't overlap,
   the difference is significant. Ours: 1.7841–1.7979 vs 1.9177–1.9401.
4. **Why the t-distribution and not the normal one?** The true spread (σ) is unknown; we only have s from
   N runs. For finite N the t-distribution is wider, which is more honest. With N ≈ 55, t = 2.00 vs the
   normal 1.96: close, but the course uses t.
5. **What does `time` show? Sys vs user.** real = wall time; user = CPU time in the program's own code;
   sys = CPU time spent in the kernel on its behalf. `/usr/bin/time` is a separate program with `-v` and
   `-f` (faults, context switches, memory); `time` is a bash builtin with only real/user/sys.
6. **Why not measure everything with perf?** It's intrusive (adds overhead), its hardware counters aren't
   available in a VM, and it's meant for *characterization* (explaining why), not for the final timing.
7. **What causes variation? Why interleaving?** Noise: interrupts, other processes, migrations,
   frequency/thermal changes, host activity. Some of it can be reduced (taskset, nice, closing apps), but
   it can't be removed completely. Interleaving: if something changes over time (heat, a background job),
   it affects both configurations equally instead of only the one that happened to be running.
8. **Why prepare the environment instead of measuring in "normal" conditions?** To measure the effect, not
   the background noise. We showed that noise adds +57 % and makes the spread 23× bigger. A clean
   environment needs a smaller N and gives clearer conclusions.
9. **What are read()/seek() and mmap()? Why are they needed?** Two ways to access a file. read/write are
   syscalls that copy data between the file (page cache) and a buffer; mmap maps the file into memory so
   it can be accessed directly. read/write is simple and works with everything (pipes, sockets, files).
   mmap is efficient for random access to large files and for sharing memory between processes.
10. **Why do read and write times differ? With and without cache?** Writing adds syscalls (lseek + write)
    and creates dirty pages. With the cache, both stay in RAM (10M: read 0.30 s vs write 0.37 s). Without
    the cache every read goes to disk (~70 µs), and every write means reading the block + writing the block
    (≈ 3 ops, 208 µs per node): 90 s vs 0.37 s.
11. **Intrusiveness: examples, most and least intrusive tools.** The tool changes what it measures. My
    example: strace makes read/write ~410× slower. A life example: a cold thermometer cools the hot water
    it measures, or measuring your pulse at the doctor's makes you nervous. Least intrusive:
    `/usr/bin/time`, `date`, the program's own timer. Medium: `perf stat`, `vmstat`/`mpstat` running in
    parallel. Most intrusive: `strace`, `ltrace`, high-frequency `perf record`, debuggers.
12. **How does stress-ng change the result? With any options? Why?** CPU load (`--cpu`) means competing for
    CPU time: more involuntary switches and a longer wall time (+57 %). `--vm` puts pressure on memory and
    caches; `--io` calls `sync()`, which affects writeback. Different options load different resources, so
    the effect depends on what our program needs.
13. **Why the system passport? What does lscpu show? UMA or NUMA?** It makes the result reproducible and
    interpretable (a different CPU or disk gives different numbers). lscpu shows the architecture, the
    number of CPUs, threads per core (SMT), sockets, NUMA nodes, caches and flags. **Mine is UMA** (1 NUMA
    node).
14. **How do you drop the file cache?** `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches`. For a single
    file: the program's `--no-cache` (O_DIRECT / F_NOCACHE), or `posix_fadvise(DONTNEED)`.
15. **Why taskset and nice?** taskset pins the process to one CPU (no migrations, stable caches);
    nice/renice changes the priority (−20 = highest … 19 = lowest) so the scheduler prefers our process.
16. **What do context-switches show? What types are there? How do they differ from cpu-migrations?** They
    show how often the process lost the CPU. Voluntary: it waits for I/O or a lock. Involuntary: it was
    preempted. A migration means it moved to *another* CPU, which is worse because the caches are lost. A
    context switch can happen without a migration.
17. **What do cache-misses show?** How often the CPU didn't find data in its cache and had to go to slower
    memory. More misses = slower memory access. That's the mechanism behind our 10M slowdown (we couldn't
    measure it in the VM).
18. **What does %CPU show?** (user + sys) / wall × 100 %. 100 % = busy all the time (CPU-bound, our case);
    low = mostly waiting (I/O-bound; e.g. `--no-cache` used 0.58 s of CPU in 3.02 s of wall time = 19 %).
    It can be above 100 % for multi-threaded programs.
19. **Which tool shows disk I/O?** `iostat -x 1` (%util, await, r/s, w/s), `pidstat -d 1` (per process),
    `vmstat 1` (bi/bo), `iotop`.
20. **What is an OS? Why do we need it? Can we do without it (HAL)?** Software that manages the hardware
    (CPU, memory, devices), gives programs abstractions (files, processes, virtual memory) and protects
    them from each other. Without an OS a program has to drive the hardware itself (bare metal, possibly
    through a HAL, a hardware abstraction layer). That's done on microcontrollers, but there's no
    multitasking or protection.
21. **The two areas of an OS and why they exist.** User space and kernel space, for protection: user
    programs can't touch the hardware or other processes' memory; only the kernel can, and programs reach
    it through system calls.
22. **What is a syscall? Examples? How do you see them?** A request from a program to the kernel (it
    switches the CPU into kernel mode). Mine: `openat`, `lseek`, `read`, `write`, `mmap`, `munmap`,
    `close`, `fstat`, `execve`. You see them with `strace` (`strace -c` gives counts).
23. **Types of interrupts (БЭВМ).** External/hardware (devices, the timer): *asynchronous*. Internal
    (exceptions: division by zero, page fault, invalid instruction): *synchronous*. Software (the program
    asks on purpose: system calls, `int`/`svc`, traps). In БЭВМ, an interrupt from an external device (ВУ)
    is handled after the current instruction finishes, and the context is saved first.
24. **How do you see all running programs?** `ps aux`, `top`, `htop`, `pstree`, `/proc/<pid>/`.

---

## Part 6. The 129 micro-questions (quick answers, with my values)

1. Detailed time statistics: `/usr/bin/time -v`.
2. Seed: **427**.
3. Graph name in the data: column `size` (1M/10M) → file `graphs/graph-rand-<size>.bin`; the `program` column holds the traverser.
4. CI width: narrow, ±0.38 % … ±1.04 % of the mean.
5. Graph generator: `lab/util/graphgen.py`.
6. The two methods: `read()`/`lseek()` and `mmap()`.
7. stress-ng doesn't measure anything; it **creates load** (CPU, memory, I/O) for the noisy test.
8. `--no-cache`: graph_traverse → `O_DIRECT` (bypasses the page cache); mmap → only `madvise` hints, still uses the cache.
9. More memory: mmap (RSS 11.4 MB for 10M vs 1.2 MB).
10. `-O2` is the optimization option itself. I compiled as the README does (no -O → -O0); the course's test uses `-O2`.
11. Time measurement: `/usr/bin/time` (plus `date +%s%N`).
12. Cached pages of the graph: `fincore graphs/graph-rand-10M.bin` (or `vmtouch`).
13. Series: **4** (2 programs × 2 sizes).
14. Run both configurations at once? No: they'd compete for CPU/cache, and we'd measure the interference.
15. `--write`: each node's value is incremented → +2 syscalls per node, more sys time, the file changes, dirty pages.
16. Slower: with `--no-cache` (1M read: 3.02 s vs 0.04 s).
17. Order: hypothesis → plan → measurements → analysis → conclusion.
18. Pin: `taskset -c 2 <cmd>`.
19. Must stage 2 repeat stage 1? **No** (mine differ: sys vs user, 7.7 % vs 19.4 %).
20. Compile: `clang -o out/graph_traverse src/graph_traverse.c`.
21. Max simultaneous graph_traverse: **1** (the runs are sequential).
22. Whiskers = the 95 % confidence interval of the mean.
23. Warm-up runs: discard the first K (mine: 2 rounds), decided in advance.
24. Language of the traversers: **C**.
25. Background load: `stress-ng`.
26. Configurations: 4 in the final series (16 tried in the baseline).
27. Per series: mean, standard deviation, CI (+ median, IQR).
28. Example script core: CPU **2** (CORE=2); mine is also 2.
29. One run isn't enough: noise (interrupts, other processes) can distort it.
30. Fastest: **mmap 1M** (17.1 ns/node).
31. One point = one run (one program launch): its wall time → ns/node.
32. In the CSV besides time: program, size, flags, iterations, nodes, core, round, order, user, sys, faults, context switches, timestamp.
33. First generate the graphs, then collect statistics.
34. Example script: each graph once per round (N = 30 rounds).
35. Source: `lab/intro-exp/src/graph_traverse.c`.
36. CI from raw data: mean ± t(0.975, N−1)·s/√N (scipy).
37. Measurements: 248 runs in the final series (62 × 2 × 2), 221 kept.
38. Cache-off flag: `--no-cache`.
39. A result that contradicts the hypothesis is **allowed**, if you explain the mechanism (my H1).
40. Measured characteristic: running time (wall time).
41. After the series: statistics (mean, s, CI, outliers, tests).
42. What's studied: how the access method (read vs mmap) and the file size affect traversal time, plus the experiment methodology.
43. graph-seq or graph-rand first? Neither: in my variant 1M/10M run in random order every round.
44. Help: `python3 graphgen.py --help`; the traversers print usage when run without arguments.
45. taskset is in `collect.sh` (`CORE=2`, `taskset -c $CORE`), to prevent migrations.
46. Formula: x̄ ± t·s/√N.
47. majflt: 0 for both in the final series (cached). Without the cache, mmap gets more (it loads data through faults).
48. The studied utility walks a graph stored in a file, reading (and updating) its nodes.
49. Recommended N: there's no universal number (≈ 30 is a heuristic); I computed it, and used 60.
50. Compiler: **clang** 21.1.8.
51. Combinations: read/mmap × 1M/10M = 4.
52. Normally distributed? **No** (Shapiro–Wilk p < 0.001, right tail).
53. `time` = bash builtin; `/usr/bin/time` = a separate program with `-v`, `-f`.
54. HDD vs SSD: a bigger difference on an HDD (seek ~ms for random access).
55. Utility for time: `/usr/bin/time` + `date`.
56. Disk: the guest says HDD (rota = 1), but it's virtio; it's really the Mac's SSD (checked on the host).
57. First the environment description, then the measurements.
58. Warm-up discarded: rounds 1–2, because the first runs after creating the file were slower (seen in the baseline).
59. Four series: 2 programs × 2 sizes, `collect.sh` run twice.
60. Language: C.
61. Student's coefficient: makes the CI correct when σ is unknown and N is finite.
62. CPU count: `nproc`, `lscpu`.
63. Page faults: `/usr/bin/time -v`, `perf stat -e page-faults`.
64. The `time` package: it was already installed (apt package `time`).
65. Syscalls: `strace`.
66. CPU info: `lscpu`.
67. Warm-up runs: the first runs, before the system reaches a steady state (caches, writeback).
68. `free -h`: RAM/swap total, used, free, buff/cache; `-h` = human-readable units (Ki/Mi/Gi, base 1024).
69. Write mode: `--write`.
70. Fix the environment: right before the final series (and again after).
71. Two graphs, four series: each graph × 2 programs.
72. Hypothesis: **before** the final measurements.
73. Also compare read vs mmap on: context switches and page faults.
74. Don't adjust the method to get "the same" result: that would be fitting the data. The mechanisms really differ.
75. Graphs to generate: **2**.
76. We measured *characteristics* (time); *parameters* are what we set (size, flags, N).
77. Number of passes: `<iterations>`.
78. N in the script: the second argument (`./collect.sh graph_traverse 62 …` → 62 rounds).
79. User or kernel? Both: its own code runs in user space, the syscalls in the kernel (read/write is ~80 % sys).
80. context-switches and page-faults: `/usr/bin/time -v`, `perf stat`.
81. Why background load: to see what a "noisy" measurement looks like and justify the isolation.
82. Why not perf/strace on every final run: they slow the program down (strace ~410×).
83. Statistics first, then the result.
84. Graph names: `graph-rand-1M.bin`, `graph-rand-10M.bin`.
85. perf not for the final timing: overhead, and it's a characterization tool.
86. RAM: `free -h`.
87. Generator language: Python.
88. CPU load: `stress-ng --cpu 4 --timeout 60s`.
89. Slowest: **read/write 10M** (883 ns/node).
90. OS: Ubuntu 26.04.1 LTS (Linux 7.0) in a VM (UTM/QEMU) on macOS.
91. cache-misses = CPU cache misses; page-faults = the page wasn't mapped yet. They explain *why* the time differs.
92. With stress-ng: more context switches (involuntary 13–17 → 180–266).
93. Warm-up decision: **before** looking at the results.
94. Seed: 427.
95. Before measuring: passport, environment, build, graph generation, hypothesis, plan.
96. Example script: ITER = 5.
97. perf stat default events: task-clock, context-switches, cpu-migrations, page-faults, cycles, instructions, branches, branch-misses.
98. Order: graphgen first, then graph_traverse.
99. Total series: 4 final (+ pilot, intrusiveness).
100. read → mmap: syscalls 174,793 → 37, ~80 % sys → ~80 % user, faults 137 → 544 k, 45× faster, size effect +7.7 % → +19.4 %.
101. Files per run: 1.
102. Wall time: `/usr/bin/time` (%e) or `date`.
103. Mixed order: drift protection (time-dependent noise hits both).
104. graph_traverse writes 8 bytes per node through `write()` (349 KB per pass for 1M) into the page cache; the kernel later writes the dirty pages (at most the file size) to disk.
105. Clear the cache manually: `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches`.
106. CPU model/cores: `lscpu` (`nproc`).
107. Traversers: `graph_traverse`, `graph_traverse_mmap`.
108. Metric of one run: wall time (→ ns/node).
109. Stages of the task: 3 (read/lseek, mmap, comparison) + preparation; README sections 0–9.
110. CI: shows how precisely the mean is known.
111. Order: `shuf` gives a random order in every round.
112. Generator language: Python.
113. Raw data: to recompute anything, check outliers and the distribution, and reproduce.
114. Generate the graphs or build first? Either, as long as both happen before measuring (I built first).
115. Graphs: 2.
116. What changes between runs: the time (noise).
117. Environment setup: removes noise sources, so the result reflects the effect.
118. Passport before the final series: yes (snapshot before and after).
119. Common to both traversers: the same graph format, the same traversal logic, the same CLI.
120. Topologies in the README: sequential and chain (random); my variant: chain, 2 sizes.
121. Goal: compare traversal times and learn the experiment methodology.
122. Passport before the final series: yes.
123. Did you do it yourself: yes.
124. Without taskset: no error, but migrations → more noise.
125. Bigger N → narrower CI (∝ 1/√N).
126. More major faults with mmap when the data isn't cached: the first touch of an uncached page is a major fault; read() loads data inside the syscall, not through a fault.
127. The two access methods: `read()`/`lseek()` vs `mmap()`.
128. One run: ≈ 1.5–1.9 s.
129. graph_traverse at the API level: `open`, then for each node `lseek`+`read` (24 B) and `lseek`+`write` (8 B), go to the child; `close`; repeated `<iterations>` times.

---

## Part 7. Key numbers to remember (read this before you walk in)

| What | Number |
|---|---|
| Nodes | 1M: **43,689** (256 pages); 10M: **436,905** (2,560 pages) |
| Node / header | 24 B / 40 B; every jump ≥ 2 pages (≥ 342 nodes) |
| Seed | **427** |
| Iterations | read/write 50 & 5; mmap 2000 & 200 |
| Rounds | 62 per program (2 warm-up); kept 56/55/57/53 |
| **read/write ns/node** | **819.9 → 883.0 (+7.7 %)**, user the same, sys +9.7 % |
| **mmap ns/node** | **17.10 → 20.43 (+19.4 %)**, user +23 % |
| mmap vs read | **48× (1M), 43× (10M)** |
| CI | ±0.38 % … ±1.04 % |
| Syscalls per pass (1M) | **174,793** read/write vs **37** mmap in total |
| Page faults per run | read/write ~137; mmap ~544,000 (272 per pass for 1M) |
| No cache | read 10M 30.5 s; write 10M **90.5 s** vs 0.37 s with the cache |
| Disk access in the VM | ≈ 70 µs |
| stress-ng | +57 % time, ics 15 → 180–266 |
| strace | read/write ~**410×** slower, mmap ~2× |
| perf stat | +0.4 % (not significant) |
| Machine | MacBook Air M2 (4P+4E), 16 GB; VM with 4 vCPU, 4 GiB, Ubuntu 26.04.1, kernel 7.0, clang 21.1.8 |

## Part 8. Commands you should be able to type from memory

```bash
lscpu; nproc; free -h; uname -a                    # passport
lsblk -d -o NAME,ROTA,MODEL                        # SSD or HDD
taskset -c 2 ./out/graph_traverse --write 5 graphs/graph-rand-10M.bin
/usr/bin/time -v ./out/graph_traverse --write 5 graphs/graph-rand-10M.bin
strace -c ./out/graph_traverse --write 1 graphs/graph-rand-1M.bin
perf stat -e task-clock,context-switches,cpu-migrations,page-faults ./out/graph_traverse_mmap --write 200 graphs/graph-rand-10M.bin
stress-ng --cpu 4 --timeout 30s &
sync; echo 3 | sudo tee /proc/sys/vm/drop_caches  # clear the page cache
fincore graphs/*.bin                              # what is in the cache
./collect.sh graph_traverse 62 data/final_read.csv  # rerun the measurement
python3 analyze.py data/final_read.csv data/final_mmap.csv
```

If he asks you to rerun something, **don't start the full 62 rounds** (≈ 4 minutes). Say "the full
series takes about 4 minutes, I can show 5 rounds" and run `./collect.sh graph_traverse 5 /tmp/demo.csv`.
