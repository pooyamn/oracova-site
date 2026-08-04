# oracova-site

Marketing site for Oracova. `v19/` is staging, the repo root mirrors production
(oracova.com / oracova-site.pages.dev).

`tools/header.py` owns two things: the shared stylesheet and the chrome. Running it
generates `site.css` (palette, light theme, type scale, kicker, button, the `.instrument`
scope for terminals, and the nav/menu/footer chrome) into every root, injects one
`<link rel="stylesheet" href="/site.css">` ahead of each page's own `<style>`, and rewrites
the nav, menu and footer markup. Never edit `site.css` or per-page chrome by hand: edit
`header.py` and re-run it. Page stylesheets load after the shared sheet and may extend it;
they must not restate it.

`--check` verifies no drift and runs two lints, both of which caught real bugs the day they
were written:

- **unbalanced braces**, which is what an edit that removes the first line of a two-line
  rule leaves behind. The orphan `}` closes the enclosing `@media` early and silently
  corrupts every rule after it.
- **shadowed selectors**: a selector declared inside any `@media` block and redeclared
  unguarded later in the same file. The later rule wins at every width and in every theme,
  so the guarded intent never ships. This shape accounted for the phone evidence grid, the
  hero h1 floor, the /demo terminal footer, /demo's reduced-motion suppression, and
  onboarding's light-mode hero.

An override must come after the rule it overrides. Put page-level `@media` blocks at the
end of the page's `<style>`. Its `roots` is `['.', 'v19']`
so the chrome can never drift between the two trees. Page bodies are copied root-ward only
at promote time, so between promotions the root carries staged chrome and shipped bodies.

Promote (production is the `main` branch, deployed from the `v19` directory):

```
for f in index product demo onboarding 404; do cp v19/$f.html $f.html; done
cp v19/board-augur-one-*.webp v19/robots.txt v19/sitemap.xml v19/_redirects .
python3 tools/header.py && python3 tools/header.py --check
set -a; . ~/.openclaw/secrets/cloudflare.env; set +a
npx wrangler pages deploy v19 --project-name=oracova-site --branch=main
```

Do not deploy the repo root itself: it carries the `v1`..`v18` archives, which
production has never served.

The board render is generated, not photographed. `ai-hil/hardware/render2.py` with
`--rgba` (alpha, so one asset works in both themes) and `--fit=<pad>` (solves scale and
offset from the projected vertex extents, so the board cannot leave the frame). The
approved desktop camera is `240 24 34 3 1.5 0 0 0.98 1600 660`; the phone crop is the same
camera at elevation 46 into `900 620`. Source: `oracova-assembly.step` via `step_tess.py`.

Deploy staging:

```
set -a; . ~/.openclaw/secrets/cloudflare.env; set +a
npx wrangler pages deploy v19 --project-name=oracova-site --branch=v19-preview --commit-dirty=true
```

The branch alias `v19-preview.oracova-site.pages.dev` can serve stale edge copies for a
minute or two after a deploy. Verify against the immutable `<hash>.oracova-site.pages.dev`
URL wrangler prints, not the alias.

Screenshot caveat: plain headless Chrome clamps layout width to a 500px minimum, so a
`--window-size=390` capture renders at 500 and crops, which fakes "content cut off on
mobile". For real phone layout, drive CDP `Emulation.setDeviceMetricsOverride`, or shoot at
500 and read it as the sub-560px layout.

## Product facts (checked with Pouya 2026-08-02)

- **Augur One is in fabrication**, first article pending. Everything the site says runs
  today runs on **Oracova development hardware**, not on Augur One. Any copy that says
  "proven on the bench" without that distinction is an overclaim: keep the attribution
  explicit. `/product` carries a "What runs today" block that states this.
- **Current sense is dual-range**: one range for normal draw (250 uA/LSB up to 8.19 A), one
  for low sleep currents (31 nA/LSB). The old copy also claimed a 16.4 mA full scale at
  15-bit, which does not close (31 nA x 32768 = 1.02 mA), so the full-scale figure is off
  the site until the low-range full scale is confirmed. Do not re-add it unverified.
- **AD3542R is correct** for the high-speed analog module on the product page. Do not
  "correct" it to AD3552R.
- A **lite base board** is planned shortly after Augur One. Until it exists the site says
  one base board; onboarding's "choose the base board by how much power your system needs"
  comes back when lite ships.

## Backlog

### Pre-order page
Three separate reviewers (buyer persona, UX, copy) independently bailed at the same place:
the comparison table prices the competition (`$9,900+` for a HIL rig) and leaves Oracova's
own entry cost as "a DUT board + bring-up". No price, availability or lead time appears
anywhere on the site. Build a pre-order page with a price band, a ship window, and a typical
bring-up range, and link it from the product page and the comparison row. Until it exists,
every "Request a quote" is asking for an email before answering the buyer's first question.

### Marketplace
The open-source model marketplace does not exist yet. Its claims were pulled from the site
on 2026-08-02 (onboarding "The open-source marketplace" block, and the "from the
marketplace" line in both terminal replays). Build the marketplace, then restore the claim
**with a link** - an unlinked open-source claim reads as vapor to this audience.

### A real captured run for the evidence section
The scored run report was deleted on 2026-08-02 at Pouya's request. What remains as
"evidence" is two prose anecdotes plus two replays that are correctly labelled *recreated*,
so a visitor can now scroll the whole site without seeing one artifact produced by the
machine rather than written about it. Do not fix this by drawing another synthetic trace -
that is more of the same problem. Capture a real one.

**Attempted 2026-08-02 - no artifact yet.** Full write-up on the `evidence-capture`
branch (`evidence-capture/FINDINGS.md`): the BLDC rig is unplugged, so the attempt used
the Betaflight + i9 flight-sim rig instead. Two adapters were built so the BF HIL suite
runs on today's city gateware at all (38-byte telemetry framing, and a CRSF bench adapter
because RC reaches BF from the fabric, not over MSP). It then measured 8/12, 5/12, and
PASS/FAIL/FAIL on repeats of the same scenario, so nothing was published. One mechanism is
named (no scenario clears the fault it injects) and the remaining unexplained pattern plus
ordered next steps are in that file. Start there, not from scratch.

Plan:

1. **Pick the run.** The BLDC hall-fault suite is the strongest: it already produces a real
   FAIL on the unguarded build and PASS with the guard patch, which is the whole argument in
   one artifact. The DShot600 zero-edges bug is the second choice.
2. **Book the bench.** Needs an uninterrupted window on the dev rig with the STM32F411 DUT
   seated. Confirm nothing else is mid-run before starting.
3. **Capture, do not reconstruct.** Keep the raw outputs: the internal logic analyzer
   samples (VCD or CSV), the checker's verdict JSON with its fixed thresholds, the firmware
   SHA for each build, the run ID, and wall-clock timestamps. The published trace must be
   rendered from the captured samples, not hand-drawn to look like them.
4. **Publish it** at `/runs/<id>` with the verdict table, the thresholds, the firmware
   hashes, and the raw log downloadable. Restore the links from the homepage evidence
   section and the onboarding "RESULT / Verdicts" card (currently pointed at `/demo`).
5. **Label it accurately.** A real capture needs no "recreated" label - instead state the
   date, the firmware commit, and that it ran on development hardware.

### Open questions: answered 2026-08-03 (review round 3 Q&A with Pouya)

All 15 were put to Pouya one by one; the copy now reflects the answers. Record:

1. **Test-agent split**: planned, not built. Claim softened to "tests come from the spec,
   not the code". Restore the separate-agent claim when it ships.
2. **Analog capture**: on-board ADC channels exist; spec row added, counts and rates
   "confirmed at first article". Publish figures when known.
3. **Logic analyzer**: in fabric, sim-proven (n=0 on silicon, `bench/fpga/cores/la/`).
   Spec row states edge/level/pattern triggers with channels/depth as gateware parameters,
   per Pouya: flexible by need, no fixed caps published.
4. **CI integration**: intentionally silent until built. BUILD ITEM: a CI hook (webhook or
   repo watcher) is the missing operational mechanism both personas rated top-3.
5. **Data handling**: agent runs on-prem on the customer's bench computer; source never
   leaves; iteration records (verdicts, captures, commit hash) are uploaded. Published as
   "Where your source goes" on /product.
6. **"A hundred iterations"**: real capacity claim, stays. The 8-iteration artifact is one
   example run, not a contradiction.
7. **Analog figures**: high-speed module 8 MSPS/channel, 0-5 V incl. true 0 V (from
   `SHEET-EDITS-ad3542r-rework.md`). Sensorless FOC itself remains unclaimed until run.
8. **DUT supply**: the old "up to 8.19 A" was sense full scale, NOT deliverable; real cap
   is ~3 A. Site now says "up to 3 A" and publishes sense resolutions without full scales.
9. **Open-source DUT designs**: repo coming soon; future-tense sentence restored on
   onboarding. Add the link when public.
10. **World model library**: no finished models exist; they will be built per first
    customers. Copy reframed to the proven machinery (buses/capture/fault injection) with
    built-for-your-product as the pitch. Do not reintroduce a model list.
11. **BMS boundary**: AFE modeled digitally at its interface (like the MPU6000), MCU on
    the bench, pack physics behind the model. Published on the BMS card. "Pack voltages"
    removed from the DAC row.
12. **Determinism**: DESIGN REQUIREMENT, not yet claimable. Design the world to be
    cycle-deterministic (seeded scenarios, same stimuli per run); measure, then publish.
13. **Tests are files in a test repo**, versioned and reviewed like code. Published.
14. **CAN**: no transceivers; DUT TX/RX land in fabric, then route to the N6's real CAN
    controller. The fabric owns the wire, so bus faults are physical. Published in spec.
15. **Temperatures**: legitimate (DAC modules drive analog temps; digital sensors emulated
    in fabric). Sleep-range/ship-mode-drain line added to the BMS card.

### Cloudflare zone setting
Scrape Shield "Email Address Obfuscation" is ON for oracova.com. It rewrites every
`mailto:` into `/cdn-cgi/l/email-protection#<hex>`, which 404s without JavaScript, and
replaces the footer address with a visible `[email protected]` placeholder until the
decoder script runs. The API token in `~/.openclaw/secrets/cloudflare.env` cannot read or
write zone settings, so this needs the dashboard: oracova.com -> Scrape Shield -> off.

## House style

- No em-dashes in human-facing copy, including mailto subjects. `&middot;` separators are fine.
- Every number that appears twice must agree everywhere, and must survive the reader's
  mental arithmetic. This audience divides specs in their head.
- Anything recreated, simulated or sped up carries a visible label, and no adjacent copy may
  contradict that label.
- Tap targets 44px minimum, including generated chrome. Text floor ~11px.
