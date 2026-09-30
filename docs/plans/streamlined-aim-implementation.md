# Samlade AIM-beslut: implementation och verifiering

Datum: 2026-09-30.

Den godkända [planen](streamlined-aim-approvals.md) är implementerad i repositoryt för chatt, CLI och AIM UI. Arbetet utfördes utan AIM som arbetsflöde. Rapporten beskriver implementation och verifiering inför AIM 3.2.0; releaseinformationen finns i [CHANGELOG](../../CHANGELOG.md). Repositoryts verkliga `.aim`-tillstånd och den lokalt installerade skillen har inte uppdaterats av detta utvecklingsarbete.

## Levererad funktion

- Epicens riktning och första Inkrementets plan kan godkännas tillsammans.
- PO bedömer hela Epicen före leveransbeslutet. Användaren kan acceptera Inkrementet tillsammans med redovisat avslut eller fortsättning, eller acceptera enbart Inkrementet.
- Vid accepterad fortsättning är nästa handling att planera nästa Inkrement. Strict kräver fortfarande godkännande av nästa plan före implementation.
- Chatt, CLI och UI använder samma versionerade förslag och härledning av nästa steg. Continue ger inte i sig nytt mandat.
- Avslutsberedskap kan kontrolleras utan att skriva acceptans eller fabricera auktoritet. Verkligt avslut återanvänder befintliga kvalitetskontroller.
- Ett gemensamt verktyg registrerar beslut. Ett processlås serialiserar övergångar; oföränderliga beslutsfiler förbereds före en atomisk tillståndsuppdatering. Orefererade filer från avbrutna försök räknas inte som beslut.
- Återförsök är idempotenta. Ändringsbegäran gör det gamla förslaget ogiltigt. Administrativ förnyelse tillåts endast när erbjudandet och dess bundna leveransunderlag är oförändrade.
- Äldre godkännanden får ingen större innebörd. Auto och Portfolio Auto behåller befintliga mandatgränser.

Det fullständiga kontraktet och CLI-användningen finns i [samlade beslut](../workflow/streamlined-decisions.md). Portabel skill och adaptrar har uppdaterats från sina kanoniska källor. Paketrevisionen är 17; produktversionen för releasen är 3.2.0. Tabellen nedan redovisar kontrollkörningen efter Continue-rättningarna, före versions- och releaseuppdateringen. Releaseprocessen återkör kontrollerna mot versionssatta källor.

## Verifiering

| Kontroll | Resultat |
| --- | --- |
| `python3 -m unittest discover -s tests` | 497 tester passerade, 40,036 sekunder efter Continue-rättningarna |
| `python3 scripts/validate_aim_runtime.py . --release` | Healthy; release readiness PASS |
| `python3 scripts/build_public_skill.py --check` | Godkänd |
| `node --check aim-ui/app.js` | Godkänd |
| `git diff --check` | Godkänd |

De 25 beslutstesterna täcker bland annat samlad start och avslut, partiell acceptans, fortsättning, inaktuellt underlag, saknade Epic-kriterier, samtidiga operationer, avbrott vid skrivgränser, förlorad kvittens, administrativ förnyelse, manipulerade kvitton, äldre åtgärder och CLI utan UI. Befintliga regressionssviter verifierar bland annat runtime, Portfolio, adaptrar och paketering. Samtliga kontroller i tabellen har återkörts efter Continue-rättningarna.

AIM UI kontrollerades dessutom i webbläsare mot en isolerad testfixture: beslutsunderlag, samlad knapp, acceptera-enbart-knapp och ändringsdialog granskades. En missvisande dialogrubrik korrigerades. Inget beslut skickades till någon verklig AIM-körning. UI:s läsmodell och bryggans kvittoverifiering testas automatiskt; en fullständig leverans genom en levande kodagent har inte genomförts här.

## Registreringstid och begränsningar

100 isolerade körningar av samlad acceptans och avslut mot giltiga syntetiska testunderlag gav följande före Continue-rättningarna nedan. Mätningen är historisk och har inte körts om efter rättningarna:

| Mått | Tid |
| --- | --- |
| Median | 6,20 ms |
| 95:e percentilen | 7,42 ms |
| Längsta körningen | 10,17 ms |

Varje mätning använde en separat `DecisionTests`-fixture, förberedde och publicerade ett giltigt förslag, mätte anropet till `apply` i samma Python-process och kontrollerade att resultatet var `epic_complete`. Förberedelse, publicering, processuppstart, modellarbete och användarväntan ingår inte. [Rådata och källfilernas SHA-256](streamlined-aim-registration-timing.json) anger miljö och samtliga observationer. Siffrorna gäller denna lokala syntetiska körning och är ingen garanti för andra miljöer.

Mätningen visar att själva registreringen ligger under planens femsekundersmål i den testade miljön. Den visar inte att aktiv administration halverats eller att total utvecklingstid minskat med en viss andel. Planens acceptanskriterium 10, jämförelse av hela gamla och nya agentflöden med samma resurser, återstår. Även mänsklig utvärdering av hur väl Continue-beskeden förstås återstår. Grundimplementationen verifierades med automatiska kontroller och egen granskning; därefter tillhandahöll användaren en extern granskning med två reproducerade fel, hanterade nedan.

## Rättningar efter extern granskning

Granskarens reproduktionsskript återkördes och båda Continue-felen har rättats:

- `blocked` och `epic_paused` kontrolleras före väntande förslag och ändringsbegäran, även i Auto. Status visar det sparade hindret och `canExecute: false`. Ändringsbegäran finns kvar efter giltig återupptagning.
- Accepterat `split_scope` ger nästa handling `split_scope` med den redan godkända beskrivningen i `nextWork`. Beskedet skiljer själva uppdelningen från senare beslut om ursprungliga Epicen och från mandat att implementera avskild omfattning. Enbart Inkrementacceptans ger inget split-mandat.

Fem regressionstester har tillkommit, varav två sammanhängande CLI-scenarier utan UI:

1. Samlad start, rollernas kontrollpunkter och samlat avslut med två syntetiska användargodkännanden.
2. Två Inkrement med ändringsbegäran, paus, uttrycklig återupptagning, reviderat förslag, godkänd fortsättning, separat godkännande av nästa plan och avslut. Acceptansen för båda Inkrementen bevaras.

Varje CLI-anrop startar en ny Python-process och återläser sparat tillstånd. Testvärdena för användarsvar, produktunderlag och rollernas framsteg kommer från isolerade fixtures. Detta verifierar verktygskedjan och återläsning efter processbyte; det är **inte** en verklig kodagentsession, verklig implementation av ett produktuppdrag eller en mänsklig begriplighetsutvärdering. De två praktiska agentförsök som granskaren rekommenderar återstår därför.

Dokumentation: CC BY 4.0. Attribution: Jonas Eriksson, Agile Iteration Method.
