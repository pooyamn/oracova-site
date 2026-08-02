# /product — content draft v1

Two tabs: **Overview** (this narrative) and **Specification** (the table).
Grounded in `hardware/oracova-tscircuit/DESIGN-INVARIANTS.md` + `DUT-SIGNAL-PIN-BUDGET.md`.
Status discipline: the base board is **in layout**; the capabilities below are proven on
development hardware (two-MCU rig + Colorlight i9 ECP5). Every claim on this page is tagged.

---

## Header

**Kicker:** The bench
**H1:** One board between your firmware and the world it thinks it lives in.
**Sub:** The DUT board carries your microcontroller. The base board is everything your
firmware expects to find around it: sensors that answer, loads that push back, buses that
respond, and faults that arrive when the agent decides they should.

CTA row: `Request a quote` · `Specification ↓`

---

## Section 1 — Three layers of computation

Intro line: Emulating a world has three different jobs, and they run at three different
speeds. Putting them on one processor is why bench rigs get slow or unfaithful. Oracova
splits them.

### Layer 1 — FPGA fabric: the part that has to be exact
**Lattice ECP5 (LFE5U-85F)**

Protocol timing is not a place for software. Sensor register files, bus slaves, PWM and
encoder decode, fault injection, and the in-fabric logic analyzer all live in gateware, so
the DUT's bus sees answers at the DUT's own clock, not when a scheduler gets to it. This is
the layer that makes an MPU6000 look like an MPU6000 to a driver that reads it at 8 kHz.

Runs here: sensor models, protocol slaves, edge-accurate capture, fault injection,
per-bank DUT debug relay.

### Layer 2 — Real-time compute: the part that has to be fast
**STM32N657 (Cortex-M55 + NPU)**

Physics is arithmetic, not timing. Motor and plant models, thermal and pack integration,
control-rate math, and anything that needs to update state between the DUT's samples run
on the N6. It is close enough to the fabric to feed it and far enough from the host that a
laptop hiccup cannot stall the plant.

Runs here: plant models, physics integration, closed-loop state, model coefficients.

### Layer 3 — Host computer: the part that has to think
**Bench host over Ethernet**

The agent, the test authoring, the run orchestration, the verdict scoring and the evidence
store are not real-time work. They sit on the host, where they can be slow, be restarted,
and be reasoned about. The deterministic checker that scores runs lives here too, deliberately
outside the loop it is judging.

Runs here: the agent, test authoring, CI triggers, verdicts, evidence and hashes.

Closing line: Each layer only does the work that belongs at its speed, which is why the
loop closes at rate instead of approximately.

---

## Section 2 — Power: USB-C or PoE, one cable either way

The bench takes **5 V over USB-C** (15 W budget), or **Power over Ethernet** as a stuffing
option so a bench in a rack needs one cable for power and network together. Input goes
through an ideal-diode ORing stage, so both sources can be present without back-feeding.

Why it matters: a bench you can put anywhere is a bench you can put in a rack, in a lab
across the building, or in a customer's facility, and still reach over the network.

**Status tag:** PoE is a stuffing option on the current design (board limit approximately 1.5 A).

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

The DUT board is per-part: your microcontroller, its crystal, its straps, routed out to
the base board. Everything else is the base board's job.

Four mezzanine connectors carry **400 pins, 287 distinct nets**, allocated as:

- **148** general-purpose digital I/O
- **40** analog injection channels
- **40** QSPI lines from the DAC/mimic plane
- **40** pins of adjustable DUT supply, plus Kelvin sense
- **24** pins of 4-pair Ethernet MDI to the DUT
- **18** debug pins (SWD/JTAG relayed through the FPGA, per bank)
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
| The base board described on this page | In layout, first article pending |
| DUT boards | Built per part |

Line under the table: The capabilities above run today on development hardware. The base
board consolidates them onto one board; it has not been fabricated yet, and we will not
claim otherwise.

---

# Tab 2 — Specification table

## Compute
| | |
|---|---|
| FPGA | Lattice ECP5 LFE5U-85F |
| Real-time MCU | STM32N657, Cortex-M55 with NPU |
| Supervisor MCU | STM32H563 |
| Host | External, over Ethernet |

## DUT interface
| | |
|---|---|
| Connectors | 4 x DF40HC(3.0)-100DS-0.4V mezzanine |
| Total pins | 400 (287 distinct nets) |
| Digital I/O | 148 |
| Analog injection channels | 40 |
| Mimic/DAC QSPI lines | 40 |
| DUT Ethernet | 4-pair MDI, 24 pins |
| Debug | SWD/JTAG per bank, 18 pins, relayed via FPGA |
| DUT self-ID | Revision + capability straps |

## DUT power
| | |
|---|---|
| Rail | 1.8 V to 5 V adjustable |
| Sensing | Current sense on the DUT rail, Kelvin sense return |
| Control | Supervisor-owned setpoint and enable |

## Analog
| | |
|---|---|
| Module options | Jumper (pass-through), DAC80504, AD3552R |
| Fast path | AD3552R modules for high-rate injection |
| Reference | REF5025 2.5 V |

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
| Primary | USB-C 5 V, 15 W budget |
| Alternate | PoE (option) |
| ORing | Ideal-diode, both sources may be present |

## Recovery
| | |
|---|---|
| N6 | Supervisor reset line |
| FPGA | PROGRAMN reconfigure, plus supervisor-owned JTAG (SRAM load and NOR reprogram) |
| Switch | Supervisor reset (only if the switch hangs) |
| Power switching on FPGA/N6 | None by design, no half-powered states |

---

## OPEN QUESTIONS FOR POUYA

1. **ECP5 size**: BOM lists LFE5U-25F / -45F / -85F. Which is the shipping configuration?
2. **PoE**: option only, or standard on the product? Wattage/class to publish?
3. **Analog channel count**: 40 connector pins, but how many *independent* channels does that
   map to, and at what update rate per module type? (Want a real number, not a pin count.)
4. **Host**: do you ship the host, or is it customer-supplied? Spec to publish if you ship it.
5. **N6 role**: is the NPU actually used, or is it incidental to the part choice? (Only claim it
   if it does something.)
6. **Confidential**: any part number above you do not want public? Easiest to cut are the
   exact regulator/switch/reference parts.
7. **Bench dimensions / rack unit / weight** once the layout closes: worth a physical row.
