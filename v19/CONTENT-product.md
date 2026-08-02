# /product — Augur One — content draft v2

Two tabs: **Overview** (this narrative) and **Specification** (the table).
Grounded in `hardware/oracova-tscircuit/DESIGN-INVARIANTS.md` + `DUT-SIGNAL-PIN-BUDGET.md`.
Status discipline: the base board is **in layout**; the capabilities below are proven on
development hardware (two-MCU rig + Colorlight i9 ECP5). Every claim on this page is tagged.

---

## Header

**Kicker:** Augur One
**Product name:** Oracova Augur One (formal first use) / Augur One (everywhere else)
**H1:** One board between your firmware and the world it thinks it lives in.
**Sub:** The DUT board carries your microcontroller. Augur One is everything your
firmware expects to find around it: sensors that answer, loads that push back, buses that
respond, and faults that arrive when the agent decides they should.

CTA row: `Request a quote` · `Specification ↓`

---

## Section 1 — Three layers of computation, two of them on the board

Intro: Emulating a world has three different jobs and they run at three different speeds.
Putting them on one processor is why bench rigs end up either slow or unfaithful. Oracova
splits them across three layers. **Two live on Augur One. The third is the bench computer,
a separate machine on the network.**

(The DUT is not one of the layers. It is the thing being tested: your chip, running your
unmodified firmware, on the DUT board.)

### Layer 1 (on Augur One) — FPGA fabric: the part that has to be exact
**Lattice ECP5 LFE5U-85F**

Protocol timing is not a place for software. Sensor register files, bus slaves, PWM and
encoder decode, fault injection, and the in-fabric logic analyzer all live in gateware, so
the DUT's bus sees answers at the DUT's own clock, not when a scheduler gets to it. This is
the layer that makes an MPU6000 look like an MPU6000 to a driver that reads it at 8 kHz.

Runs here: sensor models, protocol slaves, edge-accurate capture, fault injection,
DUT debug relay.

### Layer 2 (on Augur One) — Real-time compute: the part that has to be fast
**STM32N657 (Cortex-M55 + NPU)**

Physics is arithmetic, not timing. Motor and plant models, thermal and pack integration,
control-rate math, and anything that needs to update state between the DUT's samples run
on the N6. It is close enough to the fabric to feed it and far enough from the host that a
laptop hiccup cannot stall the plant.

Runs here: plant models, physics integration, closed-loop state, model coefficients.

The part also carries an NPU. We are not using it yet, and we are not going to pretend
otherwise: it is there because plants whose physics are expensive to integrate directly
(saturating magnetics, flux maps, thermal networks) are a good fit for a learned
approximation running at rate. That is a road we have, not a road we have walked.

### Layer 3 (off the board) — Bench computer: the part that has to think
**A separate machine, reached over Ethernet**

The agent, the test authoring, the run orchestration, the verdict scoring and the evidence
store are not real-time work. They sit on the bench computer, where they can be slow, be
restarted, and be reasoned about. The checker that scores runs lives here too, deliberately
outside the loop it is judging.

Keeping this layer off the board is the point: it upgrades without touching hardware, and
nothing it does can stall the plant running on the other two layers.

**You supply the bench computer.** A Linux machine with gigabit Ethernet is the whole
requirement. No GPU, no special hardware, nothing to source: a lab that already has machines
does not buy another one, and you are not locked to hardware we picked.

Runs here: the agent, test authoring, CI triggers, verdicts, evidence and hashes.

Closing line: Each layer only does the work that belongs at its speed, which is why the loop
closes at rate instead of approximately.

Summary line for the page: **Augur One is layers one and two. Your bench computer is layer
three. Your board is the thing they are all there to test.**

---

## Section 2 — One cable

**Power over Ethernet is standard.** Power and network arrive on the same cable, so a bench
is one run of Cat-6 from a PoE switch and nothing else. Put it in a rack, in a lab across
the building, or in a customer's facility, and it is still reachable and still recoverable.

**USB-C 5 V is the other option** when there is no PoE switch to hand, on a bench sitting
next to a laptop. Both inputs go through an ideal-diode ORing stage, so both can be
connected at once without either back-feeding the other.

Why it matters: benches multiply. One per pull request, one per agent, as many as the team
runs in parallel. A rack of one-cable benches is a thing a lab can actually operate; a rack
of benches each needing a power brick, a hub, and a hand on a button is not.

---

## Section 3 — It always comes back

Heading: **The supervisor is the part that never goes down**
**STM32H563**, its own MCU, on its own rail, with its own network path.

The rule the board is designed around: **the Ethernet fabric must never drop during a
recovery.** So the FPGA and the N6 are always powered. Recovery is by reset, not by power.

- **N6 wedged** → supervisor asserts its reset line.
- **FPGA misconfigured** → supervisor pulses PROGRAMN, which reconfigures from NOR with
  I/O tristated.
- **FPGA bitstream corrupt** → the supervisor owns the ECP5's JTAG. It can SRAM-load a
  known-good image directly, and reprogram the config NOR through the FPGA's own
  JTAG-to-SPI bridge.
- **Switch itself hangs** → the one case where the supervisor resets the switch.

Because the FPGA and N6 have no power switches at all, there are no half-powered or
back-driven states to get stuck in. That is by construction, not by firmware discipline.

The supervisor also owns DUT power: rail setpoint, enable, current sensing, and the
Kelvin sense return.

Closing line: A bench you cannot recover remotely is a bench somebody has to walk to.

---

## Section 4 — The DUT interface

The DUT board carries the chip under test and the parts that belong to it: crystal, straps,
whatever that part needs to boot. Everything else is Augur One's job.

We keep DUT boards for the most commonly used chips. For anything else, the DUT board is
designed for your part, and that is what the bring-up service covers.

Four mezzanine connectors carry **400 pins, 287 distinct nets**, allocated as:

- **148** digital I/O across 4 banks, each 1.19-3.29 V
- **40** analog channels (10 module slots x 4)
- **40** pins of adjustable DUT supply, plus Kelvin sense
- **3** gigabit Ethernet ports, 4-pair MDI to the DUT
- **2** USB 2.0 OTG links to the DUT
- **18** debug pins (SWD/JTAG, relayed through the FPGA)
- straps that let a DUT board identify its own revision and capabilities

The DUT rail is adjustable **1.8 V to 5 V** with current sensing on the DUT rail, so the
firmware's own power behavior is observable, not assumed.

Callout: **We meet your board at the controller boundary.** Your power stage stays off the
bench. Your firmware still sees the signals it would see in the product.

---

## Section 5 — Status (honesty block, keep it visible)

| Thing | State |
|---|---|
| Closed loop on real silicon (DC servo, pump, thermal, BLDC) | Proven, 2026-06-17 |
| Scored fault library with FAIL then guarded PASS | Proven, run 20260618-080733 |
| Full control loop in FPGA fabric at 8 kHz (unmodified Betaflight) | Proven on ECP5 development hardware, 2026-07-07 |
| Augur One (the board on this page) | In layout, first article pending |
| DUT boards | Stocked for common chips, designed per part otherwise |

Line under the table: The capabilities above run today on development hardware. Augur One
consolidates them onto one board; it has not been fabricated yet, and we will not
claim otherwise.

---

# Tab 2 — Specification table

## Compute
| | |
|---|---|
| Layer 1, on board | Lattice ECP5 LFE5U-85F (gateware: protocol, capture, fault injection) |
| Layer 2, on board | STM32N657, Cortex-M55 (real-time physics and plant state) |
| NPU | Present on the N6, not used today. Intended for learned approximations of expensive physics. |
| Layer 3, off board | Bench computer over Ethernet (agent, tests, verdicts, evidence). Customer-supplied. |
| Bench computer requirement | Linux, gigabit Ethernet. Nothing else special. |
| Supervisor | STM32H563 (recovery, DUT power, not a compute layer) |

## DUT interface
| | |
|---|---|
| Digital I/O | 148, across 4 banks, each on its own 1.19-3.29 V rail |
| Analog injection channels | 40 |
| Ethernet | 3 gigabit ports; 4-pair MDI to the DUT, 24 pins |
| USB | 2 x USB 2.0 OTG to the DUT, software-controlled attach |
| Debug | SWD/JTAG, 18 pins, relayed via FPGA |
| DUT supply | 1.8-5 V adjustable, Kelvin-sensed; current on two ranges: 8.19 A FS active, 16.4 mA FS asleep |
| DUT self-ID | Revision + capability straps |

## I/O logic levels
| | |
|---|---|
| Adjustable rails | 4 independent VCCIO domains, one per DUT bank |
| Range | 1.19 V to 3.29 V, set per bank |
| Regulation | Closed-loop LDO per rail, each behind its own load switch |
| Scope | Bank I/O reference only, independent of the DUT supply |
| Use | Mixed-level DUTs: one bank at 1.8 V, another at 3.3 V, same board |

## Analog
| | |
|---|---|
| Channels | 40, across 10 module slots (4 per slot) |
| Per-slot choice | High-speed module, medium-speed module, or pass-through jumper |
| High-speed module | 2 x AD3542R per slot, on dedicated +7 V / -1.5 V rails |
| Medium-speed module | DAC80504 per slot |
| Mix | Any combination; slots are independent |
| Isolation | Every analog column flanked by analog-ground columns, 1.2 AGND per channel |

## Network
| | |
|---|---|
| Switch | RTL8367S |
| Host link | Ethernet |
| DUT link | 4-pair MDI to the DUT board |
| PoE | Stuffing option, approximately 1.5 A board limit |

## Power input
| | |
|---|---|
| Standard | Power over Ethernet, power and network on one cable |
| Alternate | USB-C 5 V, 15 W budget |
| ORing | Ideal-diode; both sources may be connected at once |

## Physical (Augur One)
| | |
|---|---|
| Augur One | 210 x 130 mm |
| DUT board | 130 x 80 mm |

## Recovery
| | |
|---|---|
| N6 | Supervisor reset line |
| FPGA | PROGRAMN reconfigure, plus supervisor-owned JTAG (SRAM load and NOR reprogram) |
| Switch | Supervisor reset (only if the switch hangs) |
| Power switching on FPGA/N6 | None by design, no half-powered states |

---

## RESOLVED
- ECP5: **LFE5U-85F**
- Analog: **40 channels, 10 slots x 4**, each slot high-speed or medium-speed
- Board sizes: base **210 x 130 mm**, DUT **130 x 80 mm**
- Part numbers: fine to publish, but do not lead with them
- DUT boards: common chips stocked; others are a designed board + bring-up service

## RESOLVED (round 2)
- Layers: FPGA + N6 on Augur One; **bench computer is layer 3 and is customer-supplied**
  (not shipped, at least for now). DUT is not a layer.
- NPU: present, **not used yet**; stated as a direction, not a feature.
- Vocabulary locked: "bench computer" (never "host") for layer 3; "chip under test" / DUT
  for the target; one name for the "checker".

## RESOLVED (round 3)
- **PoE is standard**; USB-C 5 V is the alternate. Both ORed.
- **Bench computer: Linux + gigabit Ethernet.** Nothing else special, customer-supplied.

## STILL OPEN
1. PoE class/wattage to publish once measured on the first article (the design note says
   approximately 1.5 A board limit; that is a design figure, not a measured one).
2. Whether the run-report page's "the oracle" gets renamed to "checker" for vocabulary
   consistency (one-word edit, affects the live site).


---

## NAMING (decided 2026-08-01)

- **Base board: Oracova Augur One.** Short form "Augur One". "Oracova Augur One" on first
  use in formal copy, invoices, and the spec sheet.
- Clearance note: "Augur" is held by Augur Systems Inc (software, network management) and is
  also a crypto project; both software, neither test hardware. House-mark prefixing is the
  mitigation. Run a proper USPTO clearance before silkscreen/packaging spend.
- Naming grammar for the rest of the line:
  - DUT boards: `DUT-<part>` e.g. DUT-G474, DUT-F411
  - Analog modules: fast module / medium module / jumper
  - Future base boards: Augur Two, etc.
