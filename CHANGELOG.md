# Changelog

## 2026-01-30 – Autopost v3 stabilisering
- Bankade drafts kan raderas utan fel i delete‑route.
- Autopost använder senaste trading‑day close för effectiveDate och close‑vs‑close‑beräkning.
- Daily snapshot‑grafen visar alltid dagens värde (senaste punkt) i callout.
- Förslag renderas även vid `partial` data (preview‑only), medan `invalid` fortsatt suppressar.

## 2026-01-26 – Buyplan 2.0
- Köpkapital stöder både likvida medel och simulerat belopp, tydligt markerat i flödet.
- Köpplanen är regelmedveten med auto‑regel som hanterar restbelopp utan att bryta hårda tak.
- Yield‑skydd använder samma yield som portföljen och flaggar endast när total yield sänks.
- Pris och buy‑beräkningar använder marknadskurs; snittpris visas enbart som kontext.
- Timing‑rekommendationer visas när data finns, med tydlig fallback när timing saknas.
- Köpplanen kan skapa köptransaktioner med ursprungstext och uppdatera portfölj/ledger.
- Quote‑transparens: varningar för gamla/saknade kurser, refresh‑knapp och per‑rad status.
