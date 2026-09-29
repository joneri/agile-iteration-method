# Andra jämförelseparet: kortare leveranstid med bibehållen verifierad funktion

Genomfört 29 september 2026 svensk tid. A är GPT-6 Astra High utan AIM;
B är samma modell och reasoning med den reviderade, frysta AIM-versionen.
Förbättringsarbetet och bedömningen genomfördes utan AIM som arbetsmetod.

## Resultat

I detta par levererade AIM-agenten cirka **21 procent snabbare**. Båda klarade
samma oberoende funktionsprov och samtliga tre felinjektioner. AIM-appen
avslutade representativa sökningar cirka 11 procent snabbare med något lägre
toppminne. Vid automatisk placering tog den däremot längre tid till första
kandidaten. Resultatet är en konkret fördel i detta par, inte generell
överlägsenhet eller ett isolerat kausalbevis för de nya instruktionerna.

| Mått | A: utan AIM | B: AIM |
| --- | ---: | ---: |
| Byggtid, rapporterade UTC-klockslag | 23:31 | **18:41** |
| Oberoende simulatorfall | 123/123 | 123/123 |
| Avvisade ogiltiga kopplingspaneler | 3/3 | 3/3 |
| Upptäckta felinjektioner | 3/3 | 3/3 |
| Full sökning, tio par | 88,22 ms | **78,49 ms** |
| Topp-RSS, samma tioparsfall | 65,64 MiB | **60,28 MiB** |
| Full sökning, automatisk placering | 711,78 ms | **630,19 ms** |
| Första kandidat, automatisk placering | **132,65 ms** | 440,20 ms |
| Topp-RSS, automatisk placering | 74,44 MiB | **73,30 MiB** |
| Produktbedömning med tidigare vikter | 99/100 | 99/100 |

Totalt 84 sekventiella körningar: 14 fall, två produkter och tre repetitioner.
204 kandidater återspelades med Py-Enigma, med **noll ogiltiga kandidater** och
**noll timeouter**. Varje körning startade en ny Node-process. Rapporten skiljer
avslutad sökning från kandidatgräns; båda nådde gränsen 20 i det tvetydiga fallet.
I det korta cribfallet returnerade båda fem kandidater. Tids- och minnessiffrorna
är medianer, inte en garanterad vinst på andra maskiner eller indata.

Båda returnerar ett panelvittne per start/placering. B har dessutom en redovisad
gräns på 25 000 söknoder per start/placering; den nåddes inte i de fall som
redovisas som avslutade. A har ingen sådan nodgräns. A söker placeringar först,
B startpositioner först, vilket bidrar till olika ordning på tidiga kandidater.
Det är en observerad algoritmskillnad, inte ett kontrollerat profileringsexperiment.

## Teststyrka och verkligt användarflöde

Båda sviterna fångade ändrad C-reflektor, ändrad V-rotor och flyttad omslagsbokstav
på II-rotorn. Ändringarna gjordes var för sig i isolerade kopior. Alla sex
resultat var assertionsfel i körbara tester, inte syntax- eller installationsfel.
Det åtgärdar den observerade testluckan i första AIM-provet på just dessa fel.

Apparnas egna domäntester och produktionsbyggen kördes om: A 20/20 och B 11/11.
A:s samlade browserskript och B:s nio browserfall passerade också vid återkörning.
Testantal används inte som kvalitetspoäng.

Den separata, gemensamma browserkontrollen använde ett oberoende tioparsfall,
inte apparnas laddade exempel. Den verifierade att gamla kandidater behåller
chiffertext och maskininställningar efter formulärändring, dekrypterar rätt vid
överföring, och att avbrott och omstart fungerar. Båda ryms vid 390 px utan
horisontellt sidöverflöd. Desktop- och mobilbilder granskades visuellt. Inga
okontrollerade JavaScript-fel eller externa runtimeanrop observerades i dessa
flöden. Den statiska testserverns saknade favicon gav ett ofarligt 404 i båda.

Den gemensamma browsern var Chromium 153.0.8010.12. A:s inlämnade testskript har
en hårdkodad etikett `WebKit` från agentens ursprungliga körning; den etiketten
har uttryckligen korrigerats i bedömarens metadata för Chromium-återkörningen.
B:s egna browserfall kördes dessutom med dess deklarerade Playwright-browser.

## Läsbarhet, dokumentation och bedömning

Båda separerar domän, sökning och worker från UI. A använder inga npm-beroenden
för drift eller bygge, men har tät JavaScript och nästan all CSS på sju långa
rader. B har formaterad domänkod och CSS men ett samlat UI-modul med markup,
händelser och jobbhantering. Underhållskategorin sätts till 9/10 för båda;
övriga kategorier till 10/10 med tidigare vikter. Poängen är en granskares
bedömning med synlig metodidentitet, inte statistisk precision.

README-beskrivningarna stämmer med de observerade sökgränserna och modulernas
ansvar. B:s två källbundna dokumentationspåståenden hade oförändrade hashvärden
för samtliga tio refererade filer; innehållet granskades också manuellt.
Hashkontrollen ensam skulle inte räcka som sanningsbevis.

Ett separat underhållsprov i nya sessioner har startats på kopior av dessa
leveranser. Dess resultat ingår ännu inte i tabellen ovan.

## Jämförbarhet och begränsningar

Samma låsta PRD, fall och bedömningsvikter som första paret. Båda fick 30 minuter
och nya sessioner utan tidigare lösningar. A startade 23:31:49 UTC och lämnade
in 23:55:20; B startade 23:31:58 och lämnade in 23:50:39. Modellkvot per agent
har inte kunnat fastställas; byggtid är inte ett mått på tokenkostnad.

De första apparna frystes före respektive bedömning. Samtliga 61 initiala
indatafiler samt 37 respektive 44 arkiverade produkt-/evidensfiler kontrollerades
oförändrade efter provet, bortsett från browsercache som inte ingick i återkontrollen.
Runtimeproven kördes sekventiellt när båda byggagenterna hade avslutat.

Det första parets råa agent byggde betydligt snabbare än det andra parets råa
agent. Browserinstallation, implementation och modellvariation skiljer sig.
Man kan därför inte tillskriva hela den nya relativa tidsvinsten en kortare
AIM-starttext. Två Enigma-par räcker inte för generell överlägsenhet; därför
redovisas också ett [underhållsprov](paired-maintenance-results.md) och ett
[API-prov med tidigare oanvända krav](paired-api-results.md).

Den senare rättningen av sökvägen till medföljande rollskills ingår inte i
detta frysta AIM-paket. Den är separat regressionstestad i AIM-repot.

[Maskinläsbar evidens](evidence/2026-09-29-paired-pilot2.json).
Komplett lokalt arkiv:
`/Users/jonaseriksson/Documents/Codex/2026-09-29/aim-engineering-pilot2`.
Arkivet innehåller prompter, paket, leveranser, adaptrar, råmätningar, mutationer
och bilder. Installerade beroenden och browserbinärer är utelämnade; deras
miljöuppgifter och relevanta ursprungliga hashvärden finns kvar.
