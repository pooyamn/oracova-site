# oracova-site

Marketing site for Oracova. `v19/` is staging, the repo root is production
(oracova.com / oracova-site.pages.dev). `tools/header.py` owns the nav, hamburger menu and
footer sitemap on every page: edit it, never the per-page chrome, then run
`python3 tools/header.py` (and `--check` to verify no drift). Its `roots` list is
deliberately `['v19']` so production is only touched when promoting.

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

### At promote time
Production still serves `/runs/bldc-hall-fault-demo`. When v19 goes to root, that URL dies:
add a `/runs/*` -> `/#evidence` redirect so bookmarks and shared links do not 404.

## House style

- No em-dashes in human-facing copy, including mailto subjects. `&middot;` separators are fine.
- Every number that appears twice must agree everywhere, and must survive the reader's
  mental arithmetic. This audience divides specs in their head.
- Anything recreated, simulated or sped up carries a visible label, and no adjacent copy may
  contradict that label.
- Tap targets 44px minimum, including generated chrome. Text floor ~11px.
