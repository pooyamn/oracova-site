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

### Open questions blocking copy fixes (raised by review 2026-08-03)
Each of these is a claim on the live site that cannot be verified from the repo:

1. **Is the test-agent split real?** The homepage says "A separate agent writes the tests,
   working from the spec rather than the code", but the replay above it shows a single
   `oracova task "implement and test the gyro driver"`. Either the replay shows the split
   or the claim comes off.
2. **Can the bench read analog out of the DUT?** Onboarding promises "everything your MCU
   senses and drives"; the spec lists only DACs plus the Kelvin-sensed supply current.
3. **The internal logic analyzer has no specification.** It is the replay's hero feature
   and appears nowhere in the spec tab: channels, depth, sample rate, trigger model.
4. **How does a run reach the bench from CI?** No GitHub / GitLab / webhook / pipeline
   mention exists anywhere, yet "every firmware PR gets its own bench" is the core pitch.
5. **Where does firmware source go and where does the agent run?** No mention of cloud,
   on-prem or self-hosted. Reviewers rate this the silent deal-killer above the engineer.
6. **"A hundred iterations, unattended"** in the hero against `8 iterations, 1 h 12 min`
   in the artifact below it. 100 implies a 15 hour run.
7. **Sensorless FOC.** Every motor claim on the site is hall-sensored. No latency, analog
   update rate or bandwidth figure is published anywhere.
8. **DUT power budget in watts.** "up to 8.19 A" reads as a supply rating next to
   "1.8-5 V DUT supply"; 5 V x 8.19 A = 41 W against a 71.3 W PoE budget shared with
   everything else on the board.
9. **"DUT designs are open source"** was removed from onboarding on 2026-08-03 for having
   no link, same rule as the marketplace. Restore it with a repository URL.

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
