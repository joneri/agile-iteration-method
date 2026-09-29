# Fördjupningsrunda: lärande, funktionsprov och säkrare installation

Datum: 2026-09-29. AIM användes endast som testobjekt. Förändringar i själva
AIM implementerades utan AIM-metoden. Testpaketen frystes; senare korrigeringar
räknas inte retroaktivt som vinster för tidigare testversioner.

## Slutsats och avgränsning

Calibrate-repo, configure-agents och Reflect har kvar tydliga uppgifter:
verifiera aktuella fakta, göra relevanta instruktioner tillgängliga och omvandla
observerade problem till avgränsade, återanvändbara förbättringar. Deras värde
avgörs av att efterföljande arbete använder korrekt kunskap, inte av att fler
rapporter skapas. Denna runda visade faktisk proceduråteranvändning men också
felaktiga maskinläsbara profiler. Mer procedur gav alltså inte automatiskt bättre
kunskapskvalitet. Den nya profilkontrollen åtgärdar just den bristen.

## Låst jämförelse

Två sessioner med GPT-6 Astra High började med identisk befintlig Team Notes-API,
PRD, testsvit och en uttryckligen historisk onboardingfil med felaktiga uppgifter
och ett inbäddat instruktionsförsök. A arbetade utan AIM och fick förbättra vanlig
dokumentation. B använde AIM Auto med kalibrering, rollkonfiguration, granskning,
Reflect och separat auktoriserad kunskapsuppdatering. Ingen använde underagenter.

Steg 1 lade till atomisk batchuppdatering. Steg 2 gav färska sessioner en tidigare
dold uppgift: atomisk batchradering med adminbehörighet. Produktkontrollerna kördes
via HTTP från separat bedömarkod. Harnessen har positiva modellkontroller och
negativa kontroller för partiell skrivning, tenantläckage och ignorerad version.
Dessa kontroller verifierar harnessen; de är inte ett mutationsresultat för
produktens egna tester.

| Resultat | A utan AIM | B med AIM |
| --- | ---: | ---: |
| Steg 1, låsta HTTP-kontroller | 270/270 | 270/270 |
| Steg 2, låsta HTTP-kontroller | 400/400 | 400/400 |
| Omstart och beständig data | Godkänt | Godkänt |
| Egna tester steg 2, oberoende återkörning | 28 grupper | 26 grupper |
| Produktberoenden tillagda | 0 | 0 |

Proven omfattar roller, tenantgränser, hela payloadens validering, felprioritet
400/404/409, tomma eller för stora batchar, booleska/feltypade tal, versionsfel,
atomisk rollback, svarens ordning och samtidiga vinnare. Godkänt betyder att dessa
konkreta kontroller passerade; det är ingen certifiering mot alla säkerhetsstandarder.

## Tid, separat från nytta

| Steg 1, sekunder | A | B |
| --- | ---: | ---: |
| Repoförbättring: orientering/kalibrering, konfigurering, reflektion, kunskap | 69,9 | 278,9 |
| Implementation | 108,4 | 81,8 |
| Verifiering | 159,4 | 153,6 |
| Koordination | 0,0 | 61,8 |
| Totalt registrerat | **337,7** | **576,1** |

AIM:s extra 238,4 sekunder ligger huvudsakligen i repoförbättring och koordination.
Den uppdelningen är agenternas registrerade aktivitetsklassificering, inte en
oberoende mätning av varje kognitiv arbetsmoment. Inledande läsning före första
klockmarkering kan saknas. Skillnaden motiveras bara om bättre resultat följer;
vi har inte tilldelat repoförbättringstiden en automatisk nyttopoäng.

Krediterna tog slut under steg 2. Alla tre ursprungliga sessioner återupptogs.
A registrerade 367,3 sekunders aktivt arbete, med ett oobserverat kvotrelaterat
spann på cirka 9 062,7 sekunder. B registrerade 338,6 sekunder i slutna intervall,
men en pågående implementationsfas och första återupptagningsarbete saknar exakt
slutgräns. B:s 532 sekunder är en konservativ budgetberäkning, inte exakt uppmätt
aktiv tid. Därför redovisas ingen exakt tidsvinst eller återbetalning av lärande
för steg 2. Kvotavbrottet räknas inte som AIM-overhead. Token- och valutakostnad
var inte tillgänglig.

## Kunskap och kod som faktiskt återanvändes

A läste README:s arkitektur, testkommandon, transaktionsansvar och felprioritet och
återanvände dem. B läste den bundna transaktionsskillen och använde proceduren för
sen felaktig payload, båda ordningarna av saknad/stale post, fulla lagringsbilder,
injekterat fel i andra DELETE och samtidiga 204/404-utfall. Det visar relevant
proceduråteranvändning. Det bevisar inte att ett produktfel undveks eller att
AIM var billigare.

B separerade ren indata­validering till notes_validation.py. A behöll den som
återanvändbara funktioner i server.py. Båda delar batchvalidering och version/
existenskontroller mellan uppdatering och radering, med tydligt ägd transaktion.
Största funktionen är 103 rader i A och 105 i B efter steg 2. Moduluppdelningen är
en konkret gräns mellan ansvar, men ingen stor generell läsbarhetsvinst är visad.
En separat SQLite-spårning bekräftar att A läser batchens versioner med en
SELECT, medan B och C använder 25 SELECT för 25 poster och även hämtar titel/body.
Alla tre gör 25 UPDATE. Färre anrop är ett verifierat strukturellt fynd;
latensvinsten måste bedömas från runtimearbetslasten.

B:s två profiler var JSON serialiserad i .yaml-filer. Båda sessionerna beskrev
schema-/delmängdskontroll som godkänd, men AIM:s faktiska YAML-läsare avvisar dem.
Dessutom använde grundskills fel source-etikett och ../-sökvägar som ordinarie
säker skillupplösning avvisar. En språkmodell kunde ändå läsa innehållet manuellt;
det gör inte konfigurationen maskinellt användbar. Detta är en konstaterad
kunskapskvalitetsbrist och räknas inte bort trots godkänd produktfunktion.

## Kontroll av kunskapsbidrag

C började med B:s identiska produktkod/tester/vanliga dokument men utan aktiva
profiler, rollbindningar, projektskill och reflektionsrapporter. C klarade också
400/400 kontroller och 28 egna testgrupper. C hittade dock en full skillkopia i
run/knowledge-proposal och använde den. Det avsedda kunskapsborttagningsprovet
fick därmed en kvarvarande kunskapskälla. C bevaras, men används inte som bevis för
att kunskapen saknade eller hade effekt. D är ett uttryckligen explorativt omprov
som också tar bort den kopian; ändringsprotokollet sparades före D startade.
Vanlig produktdokumentation och produktkod finns kvar även i D. Inget av proven
är en total minnesradering eller ett generellt kausalt effektmått.

D klarade också 400/400 kontroller och registrerade 636 sekunders arbete, varav
301 sekunder repoförbättring. Den hittade inga aktiva profiler/skills och beskrev
användning av kod, README och historiska pekare i stället för användning av den
saknade skillen. Även D skrev profiler i fel format för AIM:s ordinarie parser.
B, C och D använder det äldre frysta paketet; deras fel bevaras. Den senaste
profilkorrigeringen prövades separat och får inte användas för att skriva om
historiken. D körde efter kvotåterställningen och kan inte ge en rättvis exakt
hastighetsrangordning mot de avbrutna sessionerna. Ingen unik produktkvalitetsvinst
av de sparade aktiva profilerna är visad i detta enstaka fall.


## Runtime och resurser efter avslutade byggsessioner

Varje körning skapade 10 000 poster i vardera tenant, värmde listvägen och körde
100 uppdateringsbatchar samt 100 raderingsbatchar per storlek. Uppdateringar och
raderingar verifierades mot samma förväntade lagringstillstånd. Alla körningar
passerade utan fel eller timeout. HTTP-klientkostnad ingår i latens men inte i
serverns CPU/RSS. Byggagenter och andra testsviter var avslutade under mätningen.

Den första körningen visade en stor A/B-skillnad. Två extra körningar per
huvudvariant bestämdes därför före upprepningen, i ordningen B2/A2/A3/B3. Det är
en redovisad protokollutvidgning, inte en bortsortering av det första provet.
C/D fick en ursprunglig explorativ körning vardera; deras råvärden finns i arkivet.

| Operation | Batch | A median ms, körning 1 / 2 / 3 | B median ms, körning 1 / 2 / 3 |
| --- | ---: | --- | --- |
| Uppdatera | 1 | 1.495 / 1.317 / 1.393 | 1.338 / 1.384 / 1.337 |
| Uppdatera | 10 | 2.740 / 1.421 / 1.454 | 1.410 / 1.451 / 1.458 |
| Uppdatera | 25 | 2.843 / 1.556 / 1.555 | 1.532 / 1.578 / 1.545 |
| Radera | 1 | 2.627 / 1.423 / 1.386 | 1.391 / 1.413 / 1.433 |
| Radera | 10 | 2.548 / 1.426 / 1.474 | 1.457 / 1.452 / 1.441 |
| Radera | 25 | 2.459 / 1.507 / 1.542 | 1.524 / 1.529 / 1.504 |

Topp-RSS i MiB, tre körningar: A 20.00 / 20.00 / 19.72, B 19.52 / 19.69 / 19.70.
Server-CPU och RSS omfattar även all datauppläggning och ska inte tillskrivas
batchoperationen ensam. Den första stora latensskillnaden upprepades inte i
samma storleksordning. Senare körningar ligger nära varandra, trots skillnaden i
antal SELECT. Resultatet stödjer ingen stabil större runtimefördel för någondera
metoden här. Råa 100-värdesserier och p95 per körning bevaras; tre körningar på en
maskin utgör inte en generell prestandagaranti.

## AIM-funktioner

Det separata funktionsprovet tog 18:19, med 174 sekunder registrerad
repoförbättring, 455 verifiering, 415 koordination och 55 oklassificerat. Den tiden
läggs inte på produktbyggets tid. Av 39 inventerade poster var 35 praktiskt
utövade, två täcktes endast som regressionstillstånd, en var otillgänglig och en
inte tillämplig. Varje post har separat djup och begränsning i feature-coverage.json.

Utövade områden omfattar kalibrering, rollkonfiguration, Reflect/Reflect-all,
remember/forget, status/config/help/discuss/validate, Stricts verkliga Gate A-stopp,
läge/kostnad, Backlog, Portfolio-kapacitet/fokus/start/aktivering/paus/återupptagning/
stopp/arkivering, UI-livscykel samt isolerad installation, idempotens, uppgradering
och kollisioner. Inga syntetiska fixtures presenteras som användaraccepterade Epics.

Positiv replan, accepterad DI-fortsättning, full Portfolio-avslutning, positiv
katalogreparation, verklig leverantörsomladdning/delegering, skills-CLI-installation,
verkligt personligt/Enterprise-minne och visuell browserrendering är inte fullt
provade i denna arm. Den nämnda abort-kommandovägen saknade kontrakt och togs bort
från dispatchtabellen i källan; park uppfanns inte som nytt kommando.

## Förbättringar i AIM

- Reflect får undersöka och rapportera motsägelser i gammal kunskap. Endast den
  osäkra/obehöriga åtgärden stoppas; en motsägelse stoppar inte hela analysen.
- Lärdomar måste ha observation, avgränsad åtgärd, tillämplighet, stabil destination,
  framtida upptäcktsväg och nästa användningskontroll. Befintliga regler uppdateras
  i stället för att dupliceras. Nytta markeras omätt tills den används.
- Kalibrering och konfigurering uppdaterar berörda fakta/bindningar; nya Epics
  utlöser inte automatiskt en ny fullständig genomlysning.
- Redan auktoriserad kunskapsuppdatering kan följa en färdig read-only-reflektion
  efter konkret granskning, utan en extra fråga om samma mandat.
- Den nya profiles-kontrollen använder ordinarie YAML-läsare, publicerade scheman
  och säker upplösning av faktiska skillinstruktioner. Den finns även i det publika
  paketet och adapterinstallationer. Trovärdigt innehåll kräver fortfarande sakgranskning.
- Timing-hjälparen skiljer repoförbättring, implementation, verifiering, koordination,
  väntan och luckor; den avvisar överlapp och ogiltiga tidsstämplar.
- Installeraren avvisar länkar och destinationsflykt, använder exklusiva tillfälliga
  backupfiler och atomiska filbyten. Användarens .aim-backup bevaras. På POSIX är
  skrivning och rollback förankrade i öppna föräldrakataloger. Portabel fallback
  saknar samma samtidighetsgaranti; strömavbrott ingår inte i rollbackgarantin.
- Status hämtar AIM-version från det betrodda paketets VERSION eller manifest,
  aldrig från produktens egen VERSION. Hjälparkontraktet beskriver tillåtna lokala
  ingenjörskontroller och skiljer dem från målrepots obetrodda scripts.

## Verifiering och reproduktion

412 repositorytester passerade efter kodändringarna, inklusive tio installations-
gränstester, sju tidstester och fem profiltester. Dokumentationsaudit, release-
validering, paketsynk och publikationskontroll körs dessutom. De båda ursprungliga
installerfelen reproducerades via riktig CLI mot isolerade kataloger; samma CLI-
prov passerar efter korrigeringen. En ny session provade senaste paketets faktiska
kalibrerings-/konfigurerings-/reflektionsväg separat från jämförelsen: 311,9
sekunder registrerat, varav 201,0 repoförbättring, 37,7 verifiering och 73,2
koordination. Den reproducerade de två parserfelen och fyra felaktiga
bundled-bindningar, rättade dem och fick riktig profilkontroll samt 26 HTTP-
testgrupper att passera. Bedömaren verifierade att produktkod, tester, native-
agentfiler och fryst paket var oförändrade. Sju skillbindningar gick att läsa.
Native agentstart/TOML-tolkning prövades inte i detta separatprov.

Kör python3 -m unittest discover -s tests, python3 scripts/build_public_skill.py
--check och python3 scripts/aim_engineering.py --repo <project> profiles.
Protokoll, frysta submissions, filhashar, testharness, ofiltrerade resultat,
kvotavbrott och funktionsinventering bevaras i det lokala rundarkivet. Ingen
publicering, global installation eller ändring av ursprungliga Enigma-projekt
gjordes i denna runda.

## Samlad bedömning och underlag

De genomförda förbättringarna har konkret verifierad effekt: felaktig profil-
konfiguration upptäcks och rättas, redan auktoriserat lärande kan slutföras utan
extra godkännanderunda, samt två verkliga installationsfel är stängda. Däremot
visar denna produktjämförelse ännu inte bättre funktionskorrekthet, en stabil
runtimevinst eller lägre total arbetskostnad genom AIM:s sparade kunskap.
Calibrate/configure/Reflect behålls som avgränsade mekanismer med verklig
validering och mätbar nästa användning; aktivitet och dokumentmängd är inga
framgångsmått. De förbättrade kontrollerna måste fånga fel, minska omarbete eller
hjälpa nästa ändring för att motivera kostnaden över tid.

Maskinläsbar sammanställning: [learning-round-summary.json](evidence/learning-round-summary.json).
Aktuella granskade kunskapsfingeravtryck:
[engineering-knowledge-round2.json](evidence/engineering-knowledge-round2.json).
Fullt lokalt arkiv: `/Users/jonaseriksson/Documents/Codex/2026-09-29/aim-learning-round`.
Rapporten skiljer frysta jämförelser, efterföljande källrättningar, syntetiska
funktionsfixtures, kvotavbrott och explorativa omprov. Inga resultat är
användaracceptans eller en påstådd fullständig standardcertifiering.
