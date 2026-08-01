# Homepage movie — "implement and test the gyro driver"

**Length:** ~125 s (full) · 95 s cut ends after Scene 6 · **Sound:** none required (autoplay-muted); optional low synth pad + soft key clicks
**Look:** the site's own design language — `#0a0e12` background, amber `#ffb454` accent, JetBrains Mono,
PASS green `#2ee06f`, FAIL red `#ff5252`. The movie should feel like the website came alive, not like a
marketing render dropped into it.
**Honesty rule (site ethos):** every recreated or sped-up shot carries a small mono caption, same style as
"replay · not live video". Never imply live footage that isn't.

**Logline:** a DUT board clicks onto the base board, one prompt goes in, and the agent grinds through
implement → flash → test → probe → fix cycles on real silicon until the checker says PASS.

---

## Scene 1 — The hardware exists (0:00–0:10)

3D board assembly. Dark void, subtle grid floor (the site's hero grid).

- 0:00 The **base board** floats in, three-quarter view, slow rotation. Callouts fade in mono type:
  `plant emulator` · `fault injector` · `internal logic analyzer`.
- 0:04 The **DUT board** (small carrier, one MCU) descends above it, exploded-view style — pin headers
  aligned, a thin amber guide line per pin.
- 0:07 It **seats onto the base board** with a single satisfying settle (no bounce). On contact, a ring of
  amber traces lights up outward from the connector.
- Caption (bottom-left, mono, dim): `DUT board: your microcontroller. Base board: its world.`

Production: render from the KiCad/STEP exports of the real boards (`hardware/oracova-tscircuit/kicad-export-*`);
Blender or KiCad raytrace + camera move. If board CAD isn't final, use the current rev and caption it
`engineering rev` — do not render an idealized fantasy board.

## Scene 2 — The prompt (0:10–0:16)

Hard cut to a full-frame terminal, identical styling to the site's hero replay panel
(`oracova bench` title bar, dim metadata line).

Typed live, cursor blinking:

```
$ oracova task "implement and test the gyro driver"
```

- 0:13 Response lines appear, machine-fast (no fake human typing for output):

```
plan     MPU6000 gyro/accel · SPI1 · DUT STM32F411, real silicon
world    pulling mpu6000 model from the marketplace (validated verilog)
         synth → bench FPGA .......................... ok
bench    DUT board seated · internal logic analyzer armed on SPI1
```

- Title-bar metadata reads: `replay · task 20260731-… · sped up · not live video`

## Scene 3 — The bench wires itself (0:16–0:28)

Same terminal. Before any driver code, the agent establishes hardware ground truth.

- 0:16 Netlist extraction — the SPI pins come from the customer's own board files, not a guess:

```
netlist  parse DUT board PCBA: SPI1 → PA5 SCK · PA6 MISO · PA7 MOSI · PA4 nCS
map      DUT pins → base connector → FPGA balls ............ 4 nets routed
```

- 0:19 **Visual beat:** brief cutaway to the Scene-1 3D model, top-down. The four nets light up one by
  one as amber traces running DUT pin → connector → FPGA, each labeled (`PA5 → SCK`, …). 3 seconds,
  then back to the terminal. (This is the payoff of the assembly shot — the mapping is *physical*.)
- 0:22 Wire test — dumb on purpose, and labeled as such:

```
wiretest gpio loopback, no protocol: fabric drives each net, edge counters at the far end
  PA5 ✓   PA6 ✓   PA7 ✓   PA4 ✓          4/4 nets toggle · 0 shorts · 0 opens
bench    wiring is ground truth — every failure after this line is firmware
```

- Caption (bottom-left, dim): `a wire test before any driver code — so a bus bug can never be blamed on a cable`

## Scene 4 — Iteration 1: it fails (0:28–0:42)

Same terminal. The agent's loop begins. Lines stream in:

```
iter 1   write driver: spi init, mode 0 · burst read WHO_AM_I
build    ok    flash    ok    test    running
  who_am_i ................................. FAIL   read 0xFF, expected 0x68
```

- 0:34 **Split screen** — right half slides open to the **logic analyzer capture** (rendered waveform,
  site palette: amber SCLK, blue MOSI, violet MISO, red annotation). CS drops, clock ticks, MISO stays
  high. Annotation appears exactly like a colleague pointing at a scope:

  `SCLK idles low → mode 0. This part talks mode 3 (CPOL=1, CPHA=1).`

- Caption under the waveform: `internal logic analyzer · captured on the bench FPGA`
- 0:39 Back on the terminal:

```
la       SPI mode mismatch: bus mode 0, device expects mode 3
fix      CPOL=1 CPHA=1 → rebuild
```

## Scene 5 — Iterations 2–3: closer (0:42–0:56)

Faster pacing now — the audience has the pattern. Montage rhythm, ~2 s per beat:

```
iter 2   flash ok · test running
  who_am_i ................................. PASS   0x68
  gyro_x .................................... FAIL   reads 0x0000, always
```

- 0:47 LA panel snaps back in: MOSI byte annotated `0x43` with a red underline on bit 7:

  `read flag (0x80) missing — that's a write, not a read.`

```
la       addr 0x43 sent without the 0x80 read bit
fix      set MSB on register reads → rebuild
```

- 0:52

```
iter 3   flash ok · test running
  gyro_x .................................... data flows
  rate check: world spins the table 90 °/s · driver reports 5.5
fix      FS_SEL=3 → 16.4 LSB/(°/s) scale
```

(Beat lands because the *world* catches this one, not the bus — the plant spun a known rate and the
driver's number was wrong. One line of caption: `the emulated world knows the true rate`.)

## Scene 6 — PASS (0:56–1:08)

```
iter 4   flash ok · full suite
  who_am_i .................................. PASS
  self test ................................. PASS
  rate step 90 °/s .......................... PASS
  burst read @ 8 kHz sustained .............. PASS

result   gyro driver implemented and tested · 4 iterations · 23 min unattended
checker  deterministic, fixed thresholds — the agent never grades its own work
```

- The `result` line gets the green treatment — the deliverable, not the grade — everything else stays quiet.
- 1:04 Terminal shrinks back into the hero panel of the actual homepage (seamless match-cut — the movie
  literally becomes the website).

## Scene 6b — Act II: make it fast (0:56 extension, ~+30 s)

The suite is green — now the agent improves its own work. Same terminal, same rhythm:

```
iter 5   improve: burst reads over DMA — free the CPU for the control loop
build    ok · flash ok · test running
  burst read @ 8 kHz ........................ FAIL   transfer never starts
regs     NDTR frozen — driver armed DMA1; SPI1 requests route to DMA2 only
fix      SPI1 RX/TX → DMA2 streams 0/3 → rebuild

iter 6   flash ok · test running
  burst read @ 8 kHz ........................ FAIL   stream armed, zero requests
regs     stream 0 CHSEL=0 — SPI1_RX is channel 3 on this stream
fix      CHSEL → 3 · CR2 RXDMAEN set → rebuild

iter 7   flash ok · test running
  gyro_x .................................... data flows, shifted by one byte
la       15 clocks per 14-byte frame — NDTR off by one, stream parks mid-frame
fix      exact transfer count: NDTR = 14 → rebuild

iter 8   flash ok · full suite
  ... all PASS · cpu cycles in the read path: 0
```

Beats: iters 5-6 are register-diagnosed (the debug probe reads NDTR/CHSEL — no LA needed);
iter 7 comes back to the LA for the off-by-one clock count, the visual rhyme with iter 1.
Every bug is real F411 mechanism: SPI1 only requests on DMA2 (RM0383 stream/channel table),
CHSEL=3 for SPI1_RX on stream 0, and the exact-count park is the bench's own documented
DMA war story. The arc: works → improve → breaks → fixed → faster. That's the product.

## Scene 7 — End card (1:08–1:17 … cuttable to 1:08)

- Amber logo `oracova_` on dark. Two lines, the site's own copy:

  `AI agents test your firmware on real hardware.`
  `A hundred iterations, unattended. You review the one that passed.`

- Small mono CTA: `oracova.com · book 15 minutes`

---

## Production notes

- **Every terminal frame above is the deliverable spec** — build the terminal as an HTML/CSS animation
  (same components as the site hero) and screen-capture it at 60 fps, or render with asciinema + custom
  theme. No stock "hacker" footage, ever.
- **The LA captures should be real.** Run the actual gyro-driver bring-up against the bench once with the
  three bugs deliberately staged, capture `logic_analyzer.v` output via `la_host.py`, and render the real
  waveforms in the site palette. Then the caption `captured on the bench FPGA` is true, and the movie
  doubles as evidence. (Register truth used above is real: WHO_AM_I = reg `0x75` → `0x68`, read flag
  `0x80`, MPU6000 is SPI mode 3, FS_SEL=3 → 16.4 LSB/°/s.)
- **The 3D scene** is the only "produced" segment; keep it under 10 s so the film spends its time where
  the product lives — the loop.
- **Where this fits the site:** replaces/augments the hero replay panel; also cut a 25 s version
  (Scenes 2, 4, 6 compressed — prompt, first fail, PASS) for social/OG.
- **The wire test is a real bench pattern**, not movie fiction: fabric-side edge counters + level
  bits on every candidate net give a full wiring truth table in one pass (the same pin-mapper trick
  used to bring up the FPGA rig). Stage it for real and the `4/4 nets toggle` line is a capture, not a prop.
- **The bug sequence is deliberately junior-proof:** mode mismatch → missing read flag → wrong scale is
  the exact trilogy every firmware engineer has personally lived through with this part. Recognition is
  the sell; the viewer should mutter "yep" three times.
- **What NOT to add:** voiceover, whooshes on the board assembly, fake typing sounds during output,
  progress bars that don't exist in the real CLI.
