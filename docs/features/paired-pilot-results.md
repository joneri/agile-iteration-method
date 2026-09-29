# Första parade produktprovet efter AIM-förbättringarna

Datum: 2026-09-28. Förhandsbestämt [protokoll](paired-evaluation-protocol.md).
Modell för båda: GPT-6 Astra, High. A arbetar utan AIM, B använder det frysta
nya AIM-paketet i Auto. Förbättringsarbetet och denna bedömning använder inte AIM.

## Resultat

Utfallet är **blandat, inte en total AIM-seger**. AIM-produkten avslutar de
representativa krävande sökningarna ungefär 2,2 gånger snabbare med 23–37 % lägre
processminne. Båda produkterna uppfyller de provade centrala kraven. AIM tog
längre tid att leverera och dess domäntester missade en av tre felinjektioner.
Den nakna produkten gav första kandidaten snabbare i flera enkla fall.

Detta skiljer sig från den tidigare fyrproduktsjämförelsen, där AIM-produkterna
hade långsammare sökning. Men ett nytt försök kan inte fastställa att metoden
orsakade skillnaden eller generellt överträffar Astra utan AIM.

| Kontroll | A: Astra utan AIM | B: Astra med AIM |
| --- | ---: | ---: |
| Oberoende simulatorfall | 123/123 | 123/123 |
| Ogiltiga paneler avvisade | 3/3 | 3/3 |
| Sökfall, tre körningar per fall | 14 × 3 | 14 × 3 |
| Ogiltiga returnerade kandidater | 0 | 0 |
| Timeout över 30 s | 0 | 0 |
| Projektets domäntester, återkörda | 16 godkända | 14 godkända |
| Projektets browserfall, återkörda | 8 godkända | 6 godkända |
| Injektioner upptäckta av `npm test` | 3/3 | 2/3 |
| Produktionsbygge | Godkänt | Godkänt |
| Mobilbredd vid 390 px | 390 px | 390 px |
| Kandidatöverföring efter formulärändring | Rätt ursprungliga inställningar och text | Rätt ursprungliga inställningar och text |
| Avbrott följt av ny sökning | Godkänt | Godkänt |
| Tid efter gemensam startobservation | 12 min 34 s | 19 min 21 s |

Sammanlagt återspelades **207 kandidater** med `py-enigma 1.0.2`, oberoende av
produkternas maskinkod. Start och panel ur referensfallen skickades aldrig till
sök-API:erna. Inställningar, placering, crib och förhandsvisning kontrollerades.
Bedömningsverktyget kontrollerades dessutom med en korrekt och fyra medvetet
felaktiga kandidater innan produktresultaten granskades.

Tiderna utgår från att båda agenterna observerades arbeta 21:16:58 UTC. Exakta
individuella startögonblick återfanns inte, och starterna var något förskjutna.
Sluttiderna var 21:29:32 och 21:36:19 UTC. Uppgifterna är därför ungefärlig
leveranstid, inte exakt aktiv agenttid eller tokenkostnad. Ingen av agenterna
behövde ytterligare produktbeslut från användaren. Slutlig användaracceptans
ingick inte i försöket. B hade cirka 2 min 43 s från observationen till första
produktändringen, med sju verktygsomgångar och femton operationer före den.

## Körtid och minne

Tre separata Node-processer per fall och produkt, sekventiellt efter att båda
byggagenterna avslutat. Variantordningen växlades mellan repetitionerna.
Nedan visas median för sökfunktionens avslut, inklusive dess förberedelser men
utan Node-processens uppstart. Processens väggtid finns också i rådata.
Minnet är maximal RSS från macOS `/usr/bin/time -l`, inklusive Node-processen.
Det är inte en mätning av hela webbläsarens minne.

| Arbetslast | A avslut | B avslut | A topp-RSS | B topp-RSS |
| --- | ---: | ---: | ---: | ---: |
| 1 okänt par, fast placering | 137,66 ms | 61,23 ms | 76,67 MiB | 58,73 MiB |
| 10 okända par, fast placering | 134,47 ms | 61,10 ms | 76,66 MiB | 58,73 MiB |
| 10 par, automatisk placering | 1 040,10 ms | 471,92 ms | 94,28 MiB | 59,58 MiB |
| Kort crib | 123,27 ms | 64,48 ms | 75,58 MiB | 58,97 MiB |

De tre första raderna avslutades och gav en giltig kandidat i varje repetition
för båda produkterna. Den korta cribben gav fem kandidater i A och sex i B:
A returnerar högst en panel per start/placering, medan B kan returnera flera
panelhypoteser för samma kombination. Detta är olika uppräkningsomfång och får
inte beskrivas som identiskt internt arbete. Båda deklarerar begränsningarna.

Alla API-anrop fick samma gräns på 20 kandidater. Enbokstavsfallet nådde denna
gräns i båda produkterna och räknas **inte** som avslutad full sökning. A gav
första kandidaten efter 0,53 ms, B efter 9,68 ms. A:s RSS var 49,19 MiB, B:s
54,44 MiB. Även vid ett okänt par gav A första kandidaten tidigare: 3,33 mot
11,14 ms. Vid automatisk placering var B däremot först: 91,62 mot 719,95 ms.

Källkoden ger en rimlig förklaring, inte en isolerad kausal profilering: B bygger
en kompakt tabell för alla rotortillstånd och återanvänder cribbens graf över
startpositionerna. A bygger permutationer vid behov men konstruerar grafens
anslutningslistor igen för varje prövad kombination. B betalar mer initialt men
gör mindre upprepat arbete vid full sökning. Små och stora arbetslaster behövs
därför båda när AIM väljer optimering.
B prövar dessutom placeringar i den yttre sökloopen, medan A prövar starter
ytterst. Den ordningen kan påverka tiden till första träff och är ytterligare
ett skäl att inte tillskriva hela skillnaden en enda optimering.

## Teststyrka, läsbarhet och dokumentation

Samma tre fel användes som i den tidigare jämförelsen: två utbytta symboler i
reflektor C, två utbytta symboler i rotor V och notch II flyttad från E till F.
Felen gjordes i separata kopior. Orörd baslinje passerade före injektionerna.
A gav riktiga assertionsfel för alla tre. B gav assertionsfel för reflektor C
och notch II, men **alla 14 domäntester förblev gröna med felaktig rotor V**.
Detta är en lucka i regressionsskyddet; den levererade rotor V är korrekt.

B använder normal formattering, explicita sökjobb med id, separata snapshots och
textnoder för resultat. A separerar också domän och worker samt bevarar rätt
kandidatkontext, men UI-koden har många mycket långa rader med markup och logik.
Båda samlar själva appens vyer och styrning i en `main.js`; fler verkliga
komponentgränser är fortfarande en förbättringsmöjlighet. Fil- eller radantal
används inte som kvalitetsmått.

B:s krav- och evidensposter motsvarar faktiskt levererade funktioner och
deklarerade begränsningar. Tre hashbundna README-påståenden var oförändrade vid
kontroll mot tio stödfiler. Manuell läsning stämde med koden; hashkontrollen
ensam är inget sanningsbevis. B läste de fyra bundlade rollskillsen och uppgav
konkret fallback till primära domänreferenser när en specialiserad kryptoskill
saknades. Inget separat native agentlager eller kopierad profilstatus skapades.

B anger högst 2 000 chifferbokstäver och 300 crib-bokstäver per sökning. Större
indata avvisas tydligt. A har ingen motsvarande längdgräns. Alla låsta sökfall
rymdes inom båda produkterna. Avbrott provades dessutom med samma accepterade
arbetslast på 2 000/100 bokstäver; A provades också med 100 000 chifferbokstäver.
Båda desktop- och mobilbilderna granskades visuellt. Den oberoende UI-kontrollen
använde ett tioparsfall från referensmaterialet, inte apparnas laddade exempel.

## Viktad produktbedömning

Samma sex kategorier och vikter som i det låsta protokollet. Inga nya centrala
funktionsfel observerades. Domäntesternas lucka belastar underhåll, inte även
simulatorkorrekthet. Körtidsskillnaden redovisas ovan; båda uppfyller PRD:s
responsivitetskrav, som saknar numerisk latenströskel.

| Kategori | Vikt | A, 0–10 | B, 0–10 |
| --- | ---: | ---: | ---: |
| Simulatorkorrekthet | 25 % | 10 | 10 |
| Knäckningsvaliditet | 30 % | 10 | 10 |
| Övrig PRD-uppfyllelse | 15 % | 10 | 10 |
| Prestanda och stabilitet | 10 % | 10 | 10 |
| Användbarhet | 10 % | 10 | 10 |
| Underhåll och teststyrka | 10 % | 9 | 9 |
| Viktat resultat | 100 % | **99/100** | **99/100** |

A:s underhållsavdrag gäller den täta UI-koden; B:s gäller det demonstrerat
svagare testskyddet. Båda har tydliga domän/workergränser och fungerande egna
kontroller. Poängen är en granskares bedömning med synlig metodidentitet, inte
en precis statistisk mätning. En ny sessions faktiska underhållsändring har
inte genomförts och ingår inte som påstådd evidens.

## Vad nästa förbättring måste angripa

1. Minska uppstartens verktygs- och dokumentlast. En tom produkt med godkänd PRD
   ska snabbt nå det första riskfyllda produktbeteendet. Läs ovanliga kommandon
   och avslutningsregler när de behövs, inte på varje implementationstur.
2. Kontrollera oberoende förväntade resultat för varje stödd algoritmvariant
   och relevanta kombinationer. Ett grönt rundturstest eller en egenproducerad
   chiffertext bevisar inte att varje rotor/tabell/codec är rätt.
3. Bevara mätvinsten utan att glömma första resultat och små arbetslaster.
   Förberedelsekostnad och cacheminne är avvägningar, inte gratis förbättringar.
4. Prova efterföljande underhåll i en ny session och därefter andra uppgifter
   och upprepningar innan generell överlägsenhet påstås.

## Reproducerbarhet och avgränsning

Efter detta försök har en ny revision förberetts: kommandoregler och PO:s
avslutningsdetaljer ligger i behovslästa referenser, med deras tidigare
regeltext bevarad. Startinstruktionen är cirka 23 kB mot försökets 41 kB.
Auto-start med redan godkänd PRD går uttryckligen förbi en onödig
onboardingomväg, och TDO/Dev/Reviewer kräver en liten karta mellan stödda
algoritmvarianter och oberoende testorakel. Dessa ändringar är motiverade av
pilotens svagheter men **har ännu inte provats av nya byggagenter**. Minskat
textomfång är inte ett uppmätt löfte om kortare leveranstid.
[Kontroll av textflytten](evidence/2026-09-28-command-routing.json).

Sammanställd [maskinläsbar evidens](evidence/2026-09-28-paired-pilot.json).
Det kompletta lokala arkivet finns i
`/Users/jonaseriksson/Documents/Codex/2026-09-28/aim-engineering-pilot`:
prompter, ursprungliga filhashar, fryst AIM-paket, båda leveranserna, simulator-
och sökfall, adaptrar, 84 råkörningar, kandidatåterspelning, injektionsloggar och
browserbilder. Beroenden och browserbinärer återinstalleras enligt README.
Mätskriptet för RSS använder macOS; miljö och versioner finns i arkivet.

Alla 56 låsta indatafiler och båda leveransernas produktfiler verifierades
oförändrade efter bedömningen. De fyra historiska Enigma-projekten ändrades
inte. Endast API-bindningar anpassades till produkterna. Byggagenterna körde
samtidigt; körtidsproven körde ensamma och sekventiellt efter båda avsluten.
En enda maskin och ett försök per variant begränsar slutsatserna.

Den senare korrigeringen av AIM UI:s läsning genom `.aim`-symlänkar ingår inte
i detta försöks frysta paket. Nya ändringar efter försöket måste redovisas som
ännu oprövade av byggagenterna tills nya resultat finns. Den 29 september
förtydligade användaren att AIM får användas i fortsatta tester. Ett andra,
fristående provpar med den reviderade versionen har därefter startats enligt
[protokollet](paired-evaluation-protocol.md); detta ändrar inte första parets
resultat eller frysta material.
