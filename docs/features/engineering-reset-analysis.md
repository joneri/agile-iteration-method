# AIM: analys och grundförbättringar efter Enigma-jämförelsen

Analysdatum: 2026-09-28, uppdaterad 2026-09-29. Detta är en oberoende teknisk analys och implementation,
genomförd utan AIM:s leveransmetod. Dokumentet är jämförelseunderlag; aktuellt
beteendekontrakt finns i [Engineering delivery](../workflow/engineering-delivery.md).

## Slutsats

Det ursprungliga granskade försöket visar inget mervärde i viktad produktkvalitet eller
leveranstid för AIM framför Astra utan metod. AIM:s rollnamn, godkännanden och
rapporter garanterade varken aktuell dokumentation eller effektiv kod.
Förbättringen måste ligga i vad arbetet upptäcker och levererar per tidsenhet.
Mer procedur är inte i sig en lösning.

Ändringarna i detta arbete förbättrar konkreta mekanismer och har återkörbara
tester och prestandamätningar. De bevisar **inte** att nästa AIM-genererade produkt
slår Astra utan AIM. En sådan slutsats kräver nya, jämförbara produktförsök.
Den ursprungliga jämförelsens poäng och originalprojekt har inte ändrats.

Det första nya [parade produktprovet](paired-pilot-results.md) är nu genomfört.
Båda fick 99/100 i produktbedömningen. AIM-produkten avslutade representativa
sökningar cirka 2,2 gånger snabbare med lägre minne, men tog längre tid att bygga
och missade en felinjektion som den nakna produktens tester fångade. Utfallet
motiverar nästa förbättring, inte ett påstående om generell överlägsenhet.

I [det andra paret](paired-pilot2-results.md) blev AIM-leveransen cirka 21 procent
snabbare och fulla sökningar cirka 11 procent snabbare med något lägre toppminne.
Båda klarade 123 oberoende fall och tre felinjektioner. Första kandidaten vid
automatisk placering kom däremot senare med AIM. [Underhållsprovet](paired-maintenance-results.md)
gav korrekt funktion i båda apparna, men AIM tog 6:56 mot 3:49. Alla dessa
utfall bevaras; vinsterna upphäver inte de observerade nackdelarna.

Det separata [API-provet](paired-api-results.md) gav 129/129 oberoende HTTP-kontroller
och 3/3 upptäckta felinjektioner i båda versionerna. AIM tog 13:49 mot 8:54,
hade tydligare modulgränser och extra verifierade Host/Origin-skydd. Körtiden
var ungefär lika och toppminnet cirka 5,5 procent lägre i denna enda körning.
Tre byggpar och ett underhållspar visar därmed konkreta vinster och kvarstående
kostnader, inte generell dominans över samma modell utan metod.

Den följande [fördjupningsrundan](learning-round-results.md) prövar kalibrering,
rollkonfiguration och Reflect över två leveranser, samt AIM:s bredare funktioner.
Den visar återanvända procedurer men också profiler som inte gick att läsa med
AIM:s egen parser. En paketerad profilkontroll och ett separat agentprov rättar
den bristen. Installerarens länk- och backupfel är också reproducerade och
korrigerade. Det äldre kunskapsfingeravtrycket bevaras som historik; den aktuella
sakgranskade uppsättningen är `engineering-knowledge-round2.json`.

### Bedömning enligt användarens förtydligade mål

Användaren förtydligade efter proven att AIM får ta längre tid när bättre kod,
komponentgränser, prestanda eller säkerhet motiverar merkostnaden. Målet är
därför större samlad nytta av den levererade produkten över dess användning och
fortsatta utveckling. Kortast byggtid är inte ett separat godkännandekrav.
Tiden ska fortfarande redovisas, både absolut och relativt; extra dokument,
rollbyten eller testantal räknas inte i sig som en kvalitetsvinst.

Följande är en ny nyttobedömning enligt det förtydligandet, inte en omräkning av
de låsta produktpoängen eller en ändring av historiska testresultat:

| Prov | Skillnad i bygg-/ändringstid med AIM | Nyttobedömning |
| --- | ---: | --- |
| Första Enigma-paret | +6:47 | Den stora vinsten i full sökning och minne kan motivera tiden för återkommande användning. Den missade felinjektionen är dock en kvarstående svaghet i testskyddet. |
| Andra Enigma-paret | −4:50 | Tydlig samlad fördel i detta par: snabbare leverans och full sökning, lägre minne och samma oberoende korrekthets-/mutationsutfall. Längre tid till första automatiska träffen är en redovisad kompromiss. |
| Separat API | +4:54,7 | Jag bedömer merkostnaden som rimlig för en tjänst som ska förvaltas vidare: tydligare ansvarsgränser och verifierade extra HTTP-skydd, med samma kontrollerade funktion. Framtida underhållsbesparing är ännu inte uppmätt. |
| Presetunderhåll | +3:07 | Ingen motsvarande kvalitetsfördel är ännu belagd. Korrekt funktion i båda och en nyttig AIM-reviewupptäckt räcker inte för att fastställa att merkostnaden betalade sig. |

Med detta mål visar AIM redan motiverade fördelar i konkreta leveranser trots
att det ibland tar längre tid. Nästa förbättring ska bevara dessa vinster och
minska arbete som inte påverkar produkten, särskilt vid små underhållsändringar.
Faktiska korrekthets- eller säkerhetsfel får inte döljas av en totalpoäng.
Ekonomisk återbetalningstid och generell överlägsenhet är inte beräknade eller
bevisade av detta material.

### Läget efter verifiering den 29 september

| Önskat utfall | Implementerat och observerat | Kvar att belägga |
| --- | --- | --- |
| Korrekt intern dokumentation | Tunna rollinstruktioner, källbundna faktaposter och kontroll av inaktuell evidens | Underhållsprovet upptäckte gamla inaktuella faktaposter; hashkontroll hittar drift men bevisar inte semantisk sanning |
| Snabbare utveckling | Starttext minskad från cirka 55 till 23 kB, behovsläsning och enklare auktoriserad Auto-start | Andra paret var cirka 21 procent snabbare med AIM; första paret och den lilla underhållsändringen var långsammare |
| Snabbare kod och färre resurser | Första pilotens fulla sökningar cirka 2,2 gånger snabbare; andra paret cirka 11 procent snabbare; lägre toppminne i båda | Första resultatet kan vara långsammare; fler uppgifter och upprepningar behövs |
| Läsbar och utbyggbar kod | Rollskills kräver tydliga domän-, UI- och jobbgränser; båda pilotapparna separerade domän och worker | Inget uppmätt underhållsövertag; första paret missade en variantdefekt, andra paret fångade samtliga tre |
| Säker kod | Skyddad lokal HTTP/evidensläsning i AIM; API-provet verifierade tenantisolering, atomisk samtidighet och extra Host/Origin-skydd | Ingen generell standardcertifiering; tillämpliga krav och angreppsytor måste bedömas per produkt |
| Skills för alla roller och tomma projekt | Fyra bundna basfärdigheter, validerade projektbindningar och spårbara preliminära förslag från krav/PRD | Ett förslag är inte en installerad färdighet eller verifierad specialistkompetens |

Den senaste arbetskopian passerar **389 tester**, dokumentationsaudit,
evidensaktualitet, deterministisk paketkontroll, releasevalidering och byggd
publiceringsartefakt. Den är ännu inte utgiven eller globalt installerad.

Efter att det andra produktparet frysts upptäcktes och rättades dessutom en
felaktig sökrot för medföljande rollskills. Kontroll av ett nyskapat externt
projekt gav tidigare fyra falska fel om saknade instruktioner. Kontrollen läser
nu medföljande instruktioner från det körande AIM-paketet och projektspecifika
skills från projektet. Tester täcker båda rötterna och att projektfiler inte kan
maskera saknade paketfiler. [Evidens](evidence/2026-09-29-bundled-skill-location.json).
Denna rättning påverkar inte det andra parets frysta paket eller dess resultat.

Underhållsprovet avslöjade också att två startkontroller avvisade historiska
UTC-tider med bråkdelar och explicit `+00:00`. De använder nu gemensam validering
av verkliga UTC-tider utan att ändra gamla kontrollpunkter. Nya tester täcker
godkända format, felaktiga datum, bibehållen historik och att även en ekvivalent
tidsomskrivning ogiltigförklarar en tidigare förhandsvisning.
[Regressionsevidens](evidence/2026-09-29-maintenance-startup.json).

## Vad de fyra projekten faktiskt visade

Underlag: Codex-tråden `01a0e2fc-29d9-76e2-a67f-32930de91aa9`, dess låsta
ABCD-produktrapport, underhållsanalys, effektivitetsrapport och D:s separata
prestandamätningar. Senare delar av tråden exponerades inte genom läsverktyget;
de sparade rapporterna användes därför som underlag för D.

| Projekt | Produktpoäng | Utveckling och uppsättning | Viktig observation |
| --- | ---: | --- | --- |
| A, Luna + AIM | 85/100 | 104–105 min, användaruppgift | Föredragen visuell utformning; fel vid kandidatöverföring och svagare felupptäckt |
| B, Astra utan metod | 99/100 | 23 min 15 s, användaruppgift | Snabbast sökning och lättöverskådlig domänkärna |
| C, AIM | 97/100 | 33 min, användaruppgift | God funktionell kvalitet, men långsammare sökning och tät källkod |
| D, Astra + AIM Strict | 97/100 | 2 h 14 min 46 s utvecklaragent + 19 min 58 s separat testagent | Tydligast UI-komponentgränser, men långsam sökning och inaktuell profil |

C:s exakta modell/version och reasoning var inte uttryckligen fastställda i
rapporten. D:s modell bekräftades som Astra; katalogens namn är missvisande.
D:s agenttid och A–C:s användarrapporterade tider har olika precision och
omfattning. Kalenderpauser är inte agentarbete. Tokenkostnad och fullständig
mänsklig arbetstid saknas. Dra därför ingen exakt generell produktivitetskvot.

C tog cirka 42 % längre rapporterad total tid än B utan högre viktad poäng.
Vid automatisk cribplacering mättes C till 9,312 s och B till 0,719 s i samma
kontrollomgång. D:s senare kontroll gav 17,782 s för D och 0,744 s för B.
Det är färdiga appars söktider, inte modellernas utvecklingstid. Begränsningar
och antal returnerade kandidater måste hållas lika vid nya prestandajämförelser.

## Orsaker och vad som fortfarande är en hypotes

### 1. Flera dokument lagrade samma föränderliga verklighet

A:s Dev-instruktion påstod att sökning saknades. C:s instruktion beskrev en
redan implementerad worker som planerad. D:s profil påstod att automatisk
cribplacering saknades. Alla tre riskerade att vilseleda nästa session.

Det observerade felet är dokumentdrift. En trolig mekanism är kopierad status
som inte uppdaterades vid leverans. En mer detaljerad kalibrering vid start
löser inte att fakta åldras efter första implementationen.

**Ändring:** native agentfiler läser aktuella profiler och skills utan kopierad
status. Viktiga påståenden kan bindas till dokument och stödfiler med hash.
Den nya kontrollen detekterar förändring, borttagning, tomma/ogiltiga poster och
osäkra sökvägar. Den certifierar inte påståendets betydelse. Två faktiska
repo-påståenden har sådana evidensposter, som kontrolleras i release-CI.

### 2. Granskningens aktivitet förväxlades med dess felupptäckt

A:s tester missade två av tre gemensamma felinjektioner. Kandidatöverföringen
kombinerade ett gammalt resultat med nya formulärinställningar. C och D hade
bättre regressionsskydd, vilket visar att AIM kan användas med god kvalitet,
men inte att metoden automatiskt åstadkommer den.

**Ändring:** rollskills betonar oberoende testorakel, kravbaserade motexempel,
resultatens indataidentitet och testning genom riktiga integrationsgränser.
Rapporter och antal tester räknas inte som kvalitetsbevis.

### 3. Prestanda var en förhoppning, inte ett tidigt verifierat konstruktionsval

Källkoden ger en konkret förklaring att undersöka: B bygger `buildCoreTable`
en gång per sökning och återanvänder tabeller och tidslinjer. D:s
`searchPlacement` beräknar rotorvägen för 26 signaler för varje cribtecken,
start och placering. Det innebär återkommande beräkningar och allokeringar.
Skillnaden är förenlig med mätningarna, men ingen profilerad kausal attribution
av hela tidsskillnaden har gjorts här. D:s sökschemaläggning har också andra
egenskaper; en optimering får inte ta bort dess korrekta beteende.

De lästa algoritmfilerna i B och D matchade SHA-256-värdena i jämförelsens
versionsmanifest; analysen gäller därmed samma filversioner.

**Ändring:** TDO och Dev ska tidigt välja representativ arbetslast och orakel,
mäta relevant körtid och resursåtgång, profilera den dyra delen och jämföra samma
arbete efter ändring. Kort kod, Web Workers eller fler komponenter innebär inte
i sig effektivare beräkning.

### 4. Komponentifiering saknade tillräckligt konkreta kontrollfrågor

D visade att bättre gränser går att åstadkomma: separata vyansvar, gemensam kärna,
typat workerprotokoll och callback med sparade kandidatinställningar. A:s React-val
skapade däremot inte automatiskt sådana gränser; C blandade separation med direkt
DOM-koppling och mycket långa rader.

**Ändring:** kontrollera ansvar, ägarskap över tillstånd, meddelandekontrakt,
formatering och en konkret framtida ändringspunkt. Undvik både jättemoduler och
godtycklig uppdelning för filantalets skull. Underhållbarhet behöver också mätas
genom en efterföljande ändring av en ny session, inte bara bedömas visuellt.

### 5. Uppstarten hade verklig overhead utan visat nettovärde

A och C behövde extra kalibrering. D hade många turer och väntetillfällen.
Skillnaden kan inte ensam tillskrivas Strict: modeller, mänsklig styrning och
separat testning påverkar också. Men tiden ska räknas som kostnad tills ett
konkret kvalitetsvärde demonstrerats.

**Ändring:** tomma projekt får basförmågor direkt och preliminära förslag från
krav/PRD. Keywordmatchning är en lågkonfidenssignal, inte en automatisk
stackbeställning. Rollövergångar behöver inte innebära nya modellkörningar.
Oförändrad evidens återanvänds; större dokument läses när de behövs.

## Vad som implementerats

| Område | Konkret mekanism | Begränsning |
| --- | --- | --- |
| Rollskills | Fyra bundlade rollskills, explicita bindningar, kontroll av läsbara instruktioner och fallback | Tillgänglig text innebär inte bevisad modellkompetens |
| Tomma projekt | Avgränsad PRD-läsning, källrader och preliminära förmågeförslag | Nyckelord kan ge både missar och falska träffar; semantisk bedömning krävs |
| Dokumentation | Hashbunden proveniens, färskhetskontroll och CI-kontroll på egna fakta | Hashar bevisar inte att texten är sann; negativa påståenden behöver också inventering |
| Kontext | Mänsklig onboarding flyttad till behovsläst referens; full metod inte ovillkorlig läsning | Textminskning är inte uppmätt token- eller tidsbesparing hos modellen |
| Körtid/minne | Evidens läses och hashberäknas en gång per kontroll; inget cacheläge mellan kontroller | Vinsten beror på hur mycket evidens som delas |
| Säkerhet | Host kontrolleras mot lokal lyssnare, Origin kontrolleras separat, publika bindningar nekas | Detta är verifierade kontroller, inte en fullständig säkerhetscertifiering |
| Filhantering | Begränsad läsning av vanliga filer, länkar/FIFO/traversal nekas | De säkra descriptorbaserade läsningarna är verifierade på macOS; Linux täcks av CI |
| Distribution | Samma kanoniska källor till portabelt paket och native adaptrar | Ändringarna är lokala och inte en publicerad release |

Den portabla instruktionen var 54 825 byte före ändringen. I det första
produktprovet var den 41 355 byte. Efter provet har kommandodetaljer och
avslutningsregler också flyttats till behovslästa referenser, med tidigare
regeltext bevarad. Den senaste versionen är cirka 23 kB, omkring 58 % mindre
än utgångsläget. Ingen godkännandesemantik har tagits bort för att uppnå
textminskningen; användarens befintliga arbete i repot har bevarats. De nya
byggagenternas tidsvinst är ännu inte uppmätt. Se
[textkontrollen](evidence/2026-09-28-command-routing.json).

## Verifiering och mätdata

Utgångsläget hade 365 godkända tester. Nya beteendetester provar bland annat tomt
projekt, PRD utan kod, felaktig package.json, uteblivna skills, fakta som ändras,
dubbla och tomma påståenden, symlänkar, FIFO, traversal, cacheåteranvändning och
cacheinvalidering. HTTP-testet går genom riktiga anslutningar och provar fientlig
Host/Origin, dubbla headers, fel port, saknad Host samt normal lokal trafik.
Installationstester verifierar att referenser går att läsa i rena installationer.

Slutkörningen gav **382 godkända tester**. Dokumentationsaudit, genererat
skillpaket, produkt-/releasevalidering, publiceringsartefakt och officiella
skills-CLI:s rena installationer för Codex, Claude Code och GitHub Copilot
passerade. Paketen provades lokalt; ingen publicering eller global uppgradering
av användarens installation gjordes.

Säkerhetsändringen verifierades dessutom mot den gamla serverns faktiska HTTP-
beteende i isolerade testmappar: samma fientliga Host/Origin fick tidigare HTTP
200 med repo-information och får nu HTTP 403 utan informationen.
[Reproduktionsresultat](evidence/2026-09-28-http-boundary.json).

Efter att paketet för jämförelseprovet frysts upptäcktes även en separat brist i
evidensvyn: en `.aim`-mapp som länkar utanför projektet kunde exponera den länkade
katalogens filer. Den nya läsningen nekar länkar i hela sökvägen, begränsar filer
till 1 MB och kontrollerar den öppnade filen även om sökvägen byts efter förkontroll.
Ett isolerat HTTP-prov gick från 200 med testinnehållet till 404 utan innehållet.
Regressionstestet provar också det samtidiga sökvägsbytet och vanlig tillåten
läsning. [Reproduktionsresultat](evidence/2026-09-28-evidence-read-boundary.json).
Denna senare UI-korrigering ingår inte i byggagentens frysta AIM-paket.
Efter korrigeringen passerar **383 tester**, dokumentationsaudit, kontroll av det
genererade paketet, produkt-/releasevalidering och byggd publiceringsartefakt.

Fortsatt granskning den 29 september fann att kanbanvyn löste upp `.aim`-länken
innan den kontrollerades. En länk utanför projektet orsakade ett obehandlat
`ValueError`. Vyn avvisar nu länkade och trasiga kataloglänkar innan
workspace-upptäckt och svarar med ett kontrollerat HTTP 503. Samma server kan
läsa vyn igen efter att en vanlig katalog återställts. Ett nytt HTTP-test
verifierar båda avvisningarna och återhämtningen.
[Reproduktionsresultat](evidence/2026-09-29-board-root-boundary.json).
Detta är en förkontroll av rotkatalogen, inte ett löfte om en atomär ögonblicksbild
av alla kanbanfiler vid samtidiga lokala filbyten. Evidensändpunktens separata
läsare har det starkare skyddet mot sökvägsbyten som beskrivs ovan.

Råa prestandatal, miljö, arbetslast och källhashar finns i
[mätprotokollet](evidence/2026-09-28-engineering-benchmark.json). Sju körningar per
fall efter en uppvärmning; mediansiffror nedan. Minnet är separat mätt topp för
Python-allokeringar med `tracemalloc`, inte processens RSS eller systemets minne.

| Evidenskontroll | Före | Efter | Toppminne före → efter |
| --- | ---: | ---: | ---: |
| 1 referens, 1 fil | 0,154 ms | 0,133 ms | 542 888 → 277 068 byte |
| 64 referenser, 1 delad fil | 9,729 ms | 0,269 ms | 603 134 → 277 068 byte |
| 64 referenser, 64 filer | 9,891 ms | 8,587 ms | 602 029 → 345 440 byte |

Detta är en mikromätning av AIM:s verktyg, **inte** bevis på 35 gånger snabbare
utveckling eller bättre genererade appar. Syntetisk arbetslast, varm filcache,
en maskin och korta körtider begränsar generaliserbarheten. Inga prestandatrösklar
för väggtid läggs i CI. Regressionstesterna kontrollerar i stället bibehållen
korrekthet, filgränser och antal läsningar.

Återkörning från den granskade baskoden:

```bash
git show 2f9043110b926aba47aabf772cde1c342b39d348:scripts/aim_runtime_contract.py > /tmp/aim-runtime-baseline.py
python3 scripts/measure_engineering.py --baseline /tmp/aim-runtime-baseline.py
python3 -m unittest discover -s tests
python3 scripts/aim_engineering.py check docs/features/evidence/engineering-knowledge-round2.json
python3 scripts/build_public_skill.py --check
python3 scripts/audit_documentation.py .
python3 scripts/validate_aim_runtime.py . --release
```

Baslinjen i det sparade mätprotokollet är arbetskopian före denna optimering,
inklusive redan pågående ändringar. Dess kontrollfunktion för evidensreferenser
var identisk med ovanstående commits funktion; andra funktioner skiljer sig.
Benchmarkverktyget importerar Python från baslinjefilen: använd endast en granskad
kopia av AIM:s egen kod. Det kör inte inlästa kommandon ur produktdokument.

## Vad som behövs för att faktiskt slå Astra utan AIM

Lås kriterierna innan nästa försök. Använd samma modell/version/reasoning,
verktyg, startfiler, resurser och tidsbudget. Kör rena, isolerade sessioner med
samma uppgift; låt inte lösningar eller bedömarens tester läcka mellan varianterna.
Variera ordningen och kör minst tre upprepningar per variant på flera uppgifter:
algoritmisk webapp, applikation med behörighetsgränser och en ändring i befintlig
kod. Använd ett fjärde, tidigare osedd fall för att motverka anpassning till Enigma.

Bedöm produkten blindat med samma funktionella kontrakt, oberoende orakel,
säkerhetsprov, runtimearbetslaster och uppföljande underhållsändring. Registrera
agenttid, mänsklig tid, tokenanvändning när tillgänglig, kvalitet, latens och
minne separat. Behåll misslyckade körningar och timeouter i materialet.

Förslag till **förhandsbestämd beslutsregel**, inte ett uppnått resultat:

- Inga nya centrala funktions- eller säkerhetsfel jämfört med den nakna modellen.
- Minst likvärdig uppmätt kravuppfyllelse och inget dolt byte av sökomfång.
- Förbättring i total leveranstid eller verifierad kvalitet som överväger
  eventuell merkostnad; redovisa avvägningen i stället för att välja ett
  fördelaktigt sammanvägt poängtal i efterhand.
- Samma eller bättre runtimeprestanda/resursåtgång för relevanta arbetslaster.
- En ny session löser den gemensamma följdändringen utan mer dokumentationsdrift
  eller fler regressionsfel; tidsmät även orienteringen.

Om AIM förlorar ska utfallet styra nästa ändring. Ta bort eller förenkla moment
utan visad nytta. Dessa åtgärder förbättrar AIM:s förutsättningar; först nya
produktförsök kan avgöra om förutsättningarna ger önskat resultat.

## Proveniens för den ursprungliga jämförelsen

Filhashar från rapporterna som lästes, för att skilja historiskt underlag från
framtida uppdateringar:

| Rapport | SHA-256 |
| --- | --- |
| jamforelserapport-ABCD-produktlast.md | `fcb1ab4f4dfda81d57e13994caef2884692a309a12fe6f8cefbb52a1e343d6b5` |
| aterupptagning-och-underhall.md | `6aca5ed35ad6ab3da98339082d66399795d76e2d866b4f28ab9ec26820a7723b` |
| utvecklingseffektivitet.md | `d89e6bbcdd707eb764a741630d1c392a4d14289204ee9d540c3175c2db865c02` |
| D-performance-summary.json | `d03d5dd9575d7112cd3a3a864e94ccfc7f92d81d02e90269daadee0fdf8fe743` |
