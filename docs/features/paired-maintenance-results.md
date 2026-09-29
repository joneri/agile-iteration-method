# Underhållsprov: båda korrekta, högre tidskostnad med AIM

Två nya GPT-6 Astra High-sessioner fick den 29 september 2026 samma ändring:
lägg till portabla JSON-presets i apparna från det andra Enigma-paret. A arbetade
utan AIM; B använde samma frysta AIM-paket som i det paret. Varje session hade
15 minuter och tillgång till samma Chromium. Krav och oberoende fall låstes
innan någon underhållssession började. Förbättring och bedömning gjordes utan AIM.

## Resultat

| Mått | A: utan AIM | B: AIM |
| --- | ---: | ---: |
| Rapporterad utvecklings- och verifieringstid | **3:49** | 6:56 |
| Oberoende presetfall | 26/26 | 26/26 |
| Giltiga browserimporter mot separat Enigma-orakel | 3/3 | 3/3 |
| Felaktiga browserimporter som bevarar hela tidigare tillståndet | 23/23 | 23/23 |
| Tidigare oberoende simulatorfall, återkörda | 123/123 | 123/123 |
| Egna tester, återkörda av bedömaren | 26 godkända | 16 godkända |
| Produktionsbygge | Godkänt | Godkänt |
| Verklig nedladdning och export efter kandidatöverföring | Godkänt | Godkänt |
| Avbryt, omstart och mobilbredd 390 px | Godkänt | Godkänt |

AIM tog 187 sekunder längre, cirka 82 procent, i denna enda ändring. Detta är
ett negativt resultat för utvecklingstiden och inget belagt underhållsövertag.
Båda utvecklarna hittade en avgränsad modul för presetformatet. Domänalgoritm och
sökmotor förblev byte-identiska med tidigare versioner; tidigare prestanda- och
mutationsprov upprepades därför inte och räknas inte som nya mätningar.

## Vad provet avslöjade

B:s logg visar cirka 145 sekunder före första produktfilen, mätt från rapporterad
start till filens skapandetid. Det är en indikator på startarbete, inte en exakt
uppdelning av tänketid. Startverktyget avvisade en befintlig UTC-tid med decimaler
och `+00:00`, vilket krävde en manuell formatändring. Det felet rättades efter
inlämningen i AIM:s gemensamma tidsvalidering. Historiska bytes bevaras nu och
ändringar i kontrollpunkten ogiltigförklarar fortfarande tidigare startförhandsvisning.
Det frysta provpaketet och de uppmätta tiderna har inte ändrats i efterhand.

B:s review upptäckte också en verklig gränsdefekt: JavaScripts `$` kunde acceptera
en avslutande radbrytning i ett strikt trebokstavsfält. Explicit längdkontroll
och regressionsfall lades till före inlämning. Det visar ett användbart
reviewresultat, men bevisar inte att just AIM var nödvändigt för upptäckten.

De två historiska kunskapspåståendena från B:s första Epic är inaktuella mot den
ändrade appen. Hashverktyget upptäcker detta korrekt. Den nya reviewn innehåller
manuell evidens, men ersätter inte dessa med nya maskinkontrollerbara påståenden.
En äldre formulering om att ingen data laddas upp är dessutom otydlig efter
lokal filimport; ingen nätverksöverföring observerades. AIM-instruktionen har
förtydligats: granska tidigare frånvaropåståenden när funktioner tillkommer,
behåll historisk evidens som historik och ange vad som granskats på nytt.

## Evidens och begränsningar

Det beständiga arkivet är
`/Users/jonaseriksson/Documents/Codex/2026-09-29/aim-maintenance-pilot`.
Det innehåller frysta produkter, låsta fall, råa resultat, verkliga JSON-nedladdningar,
bilder och kontrollsummor. Bedömaren granskade båda mobilbilderna visuellt.
De 86 oföränderliga protokoll-, paket- och PRD-filerna samt samtliga 113 frysta
inlämningsfiler var oförändrade efter bedömningen.

Ett par, olika ursprungsappar och en enda webbläsarmotor begränsar slutsatsen.
Testantal jämför inte assertionsstyrka. Ingen generellt högre säkerhetsnivå,
lägre resursförbrukning eller framtida underhållsfördel följer av detta prov.
