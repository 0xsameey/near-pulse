# Submission readiness - November 13, 2026

## Release assessment

**Local demonstration: ready.** The five-page dashboard runs from verified
public exports without credentials. Offline replay and the production build pass.
**Static hosting package: prepared for review.** No deployment is authorized or
performed. **Hackathon entry: local release prepared; human publication and
submission steps remain outstanding.** The thesis is explicitly unresolved.
An unresolved result is a research limitation, not a claim that the app is broken.

## Evidence and verification

- Transactions/signers: November 3-9, seven UTC days. Calls: November 9 only.
- Successful 1Click swaps: 134,156, deduplicated by deposit address plus memo.
- Input volume: $263,033,264.614200753422, exact Decimal aggregation.
- Original November 9 datasets and provenance are preserved. All 137 raw HTTP
  response-page hashes validate; no BigQuery or Explorer acquisition was repeated.
- Seven levels yield six paired daily changes. The threshold is 30 pairs.
  Including calls leaves one common date; including public price leaves none.
- CoinGecko: user reports private authenticated success, 168 samples covering
  November 3-9, no missing dates, no persistence. Public display/redistribution
  rights remain unestablished. No price exports or observations were added.
- Offline replay of network,intents completed successfully; price unavailable
  and Insufficient data verdict retained. Complete rebuild true concerns the
  requested public sources only.
- 111 Python tests and 17 subtests passed; Python compileall passed; 20 frontend
  tests passed; TypeScript typecheck and production build passed. Release tests
  render all five pages with published data and check missing price downloads.
- Desktop Chrome inspection visited Overview, Network, Intents, Thesis and
  Methodology. The chart Method dialog opened and its full-methodology link
  navigated correctly. Source labels and observed coverage were reviewed.
- Actual desktop captures: [Overview](screenshots/overview.png),
  [Intents](screenshots/intents.png), [Thesis](screenshots/thesis.png),
  [Methodology](screenshots/methodology.png). Browser chrome is excluded.
- A 375 CSS-pixel responsive Methodology viewport was inspected: navigation
  collapsed, heading wrapped, no visible horizontal clipping in the inspected
  region. The viewport height was limited by docked developer tools. A complete
  mobile flow and all requested device sizes were not exhaustively checked.
- The console at inspection showed wallet-extension content-script warnings
  (ObjectMultiplex/MaxListenersExceeded and Backpack window.ethereum) and the
  React development-tools notice. No application error was visible in that
  inspected state; this is not a clean-console certification of every flow.

## Remaining handoff blockers

1. Publish the reviewed repository only after explicit authorization, including
   the verified raw replay inputs, hashes, source SQL and original response
   pages already bundled in the source archive. Keep all secrets excluded.
2. Record and have the human publish the actual demo video/X post. The prepared
   60-90-second script is docs/demo-script.md. A local-only demo requires video,
   not screenshots alone. Include @NEARProtocol and #NEARHackathon and state it
   was built at NEAR HACKATHON. Public repository and demo-post URLs are pending.
3. Owner must verify reciprocal independent-project disclosure in Sentinel's
   README. NEAR Pulse names Sentinel. Sentinel was not accessed or modified.
4. Human must supply/confirm lead name, email, team size, payout NEAR account,
   track, public URLs, description and contact consent, then approve the exact
   payload before the one-time submission. No payload was invented or sent.
5. Recommended final human visual check: complete mobile navigation, downloads,
   theme switching and console inspection in a browser without wallet extensions.

## Research limits (not silently filled)

No bullish or bearish relative-price conclusion is defensible. Price comparisons
remain untested until appropriate rights permit the intended public delivery.
More overlap is needed for 30 valid paired changes and lagged tests; earlier
contract calls are missing. Do not relax thresholds, substitute a price source,
sample counts, or raise query caps to improve the verdict. The current release
can be submitted as an honest descriptive research platform if the human accepts
these stated limitations; it cannot be described as a validated investment edge.

## Artifacts and rules

artifacts/near-pulse-source.zip includes reviewed replay sources and documents;
artifacts/near-pulse-static.zip contains the production dist contents.
artifacts/manifest.json records SHA-256, sizes and ZIP CRC checks. The packager
scans for actual local secret values and excludes .env, ADC and dependencies.

Official instructions were re-read at https://nearhackathon.com/HACKATHON.md on
November 13, 2026: public repository due November 14, 23:59 UTC; human demo post;
exact-payload confirmation before submission; reciprocal independent-project
disclosure. Nothing was deployed, pushed, purchased or submitted.

## Large replay-input delivery

The merged raw Intents JSON is 241,138,717 bytes; the reviewed source ZIP is
about 143 MB. These must not be treated as ordinary small repository files.
Before publishing, choose and verify Git LFS delivery or a public release asset
containing the reviewed source archive, then add its actual URL and checksum to
the public README. A release asset should be downloaded/extracted before running
the existing replay commands. Do not put a guessed download URL in the README.
The local source ZIP already contains all verified inputs and passed isolated
replay; eventual public delivery remains a handoff blocker. See GitHub's limits:
https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github.
