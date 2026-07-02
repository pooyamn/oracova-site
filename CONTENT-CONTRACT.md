# Oracova site — content contract

_Every item below must remain FINDABLE on the deployed site after any redesign round.
Text may move into boxes, rows, captions, diagrams, or expandable elements. It may be
lightly reworded only if the claim stays identical. Nothing may be deleted. Voice rules
(COPY.md v5/v6) bind all rewording: plain claims, no em-dashes, no marketing aphorisms,
"hardware" not "wire" as metaphor._

## Homepage

1. Hero line: "AI agents test your firmware on real hardware."
2. Hero second: "A hundred iterations, unattended. You review the one that passed."
3. Hero sub: "Flashing, testing, re-testing on the bench needed a human. Not anymore."
4. Betaflight video slot + caption (gyro/accel over I2C, 4x motor decode, 8 kHz closed loop).
5. What-is paragraph, all four claims: automated test bench for firmware / unmodified binary
   on your real microcontroller / world emulated with real-time physics, faults injected,
   PASS-FAIL with captured evidence / AI agents drive the bench so the loop runs unattended.
6. How-it-works header: "Every firmware PR gets its own bench and its own agent."
7. Step: change arrives with its own tests; your engineers or agents write the change,
   Oracova writes tests separately, on the bench not a mock, "you manage outcomes, not benches."
8. Step: loop runs until PASS, flash-run-read-fix-repeat, unattended.
9. Step: every test stays in the suite, runs on every future PR, catches integration
   regressions.
10. Scale note: add benches, cheap to replicate, one per PR.
11. World header: "Close your control loop on real-time physics emulation."
12. Live physics claim: motors spin, packs heat up, pressure builds.
13. No-forcing claim: firmware reaches every test point on its own, no test hooks, no forced
    states, no special builds + over-temperature illustration + unmodified binary.
14. Marketplace: validated models (gyro, LCD, hall encoder) from Oracova's open-source
    marketplace, contribute back.
15. Application cards: motor control (stuck hall, swapped sectors, skipped sector, proven on
    bench) / BMS (over-temp, sensor dropout, thresholds, reached not faked) / power & thermal.
16. Link to onboarding page.
17. Verdict header: "You review the one that passed." + Run = PASS/FAIL + traces, event
    trails, firmware hashes, repeatable, diffable, in CI.
18. Run card, exact data: RUN 20260618-080733, bldc_hall_a_stuck_low, STM32F411 real silicon,
    BLDC plant + hall encoder on RP2350, HALL_A forced low at t+200 ms, unguarded
    mismatch=8 unsafe=4 FAIL, guard patch unsafe=0 PASS + caption (wrong phase 8 times, 4
    unsafe, verdicts from real hardware not a simulator).
19. Evidence: unmodified Betaflight closed loop (I2C clock-stretch, 4 motors decoded, physics,
    ANGLE mode, 8 kHz, hardest case).
20. Evidence: DShot zero-edges story (DMA failure on F411, build green, DShot600 configured,
    static checks passed, only the closed loop caught it).
21. Evidence: BLDC fault library numbers (swapped sectors FAIL mismatch=8 unsafe=8; hall stuck
    low FAIL unsafe=4; skipped sector FAIL seq_fault=7; invalid hall bus PASS safe shutdown;
    guard flips stuck-hall to PASS unsafe=0; stored evidence + firmware hashes).
22. Evidence: Tesla ECU over CAN one-liner.
23. Objection: AI can't judge → deterministic AI-free checker, verdict from real hardware not
    the model.
24. Objection: simulation exists → sims pass builds that fail on the chip, loop closes on real
    silicon.
25. Objection: HIL vendors → $9,900 floor to six figures, hand-configured, below it nothing;
    agent-drivable, self-serve, per-PR.
26. Outcome header: "Firmware finally develops like software."
27. Founder para: hardware+firmware engineer, shipped motor controllers and battery systems,
    been the human at the bench, wants 15 minutes.
28. CTA: Book 15 minutes (both hero and end).
29. Footer: "AI agents test your firmware on real hardware."

## Onboarding page

30. Header: "From your PCB to verdicts." + two-paths framing.
31. Step 1: custom DUT board for your microcontroller, goes onto the Oracova base board, DUT
    designs are open source.
32. Box: base board plays sensors/loads protocol-exact + physics models, real time.
33. Box: analog front-ends, DAC/ADC modules in resolutions and speeds you pick, custom module
    possible; voltages and currents first-class.
34. Box: custom DUT + debug probe, every pin routed, real silicon not substitute, probe
    flashes/resets/inspects.
35. Benches cheap to replicate note (one per PR, one per agent).
36. Step 2: collecting information: actual PCB, schematics, datasheets, pin assignments,
    product description; what the bench stands in for.
37. Step 3 intro: AI agent does the work with your confirmation; expect questions about
    hardware and physics or docs that answer them; the agent asks, it does not guess.
38. Path A (working firmware): read source (peripherals, protocols, drives/senses) → write
    I/O + physics → run unmodified binary on DUT, probe watching, compare against field →
    iterate to golden, suite builds on it.
39. Path B (no firmware): peripheral by peripheral, both sides together, proven before next,
    suite is the record, never an untested part.
40. Marketplace strip: open-source marketplace, validated models proven against real firmware,
    AI builds what is unique and pulls the rest, contribute back.
41. Boundary strip: emulated (everything MCU senses/drives, digital buses direct, analog via
    modules) / not emulated (power stage, high voltage/current off bench, same signals) /
    proven today (motor commutation, servo, pump, thermal, Betaflight).
42. CTA: bring your schematic to the call, 15 minutes, no deck.

## Known placeholders (allowed to remain, not judged)
- Betaflight video pending capture; Book buttons unlinked until Calendly exists; no founder
  name until Pouya adds it.
