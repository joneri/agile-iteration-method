# Månvaktens växthus: kvalitetskriterier och mätmetod

- Version: 1.2, 2026-10-13. Omfattningen i avsnitt7 korrigerad till ett före/efter-par enligt användarens order; bedömningsankare och tekniska budgetar oförändrade. Ursprunglig revision1.1: Utökad med kodbegriplighet, modularitet, underhållbarhet, produktprestanda och säkerhet före första baslinjemätningen.
- Tillhör: [testprotokollet](moonkeeper-greenhouse-evaluation-protocol.md) och [förbättringskravet](aim-product-quality-requirements.md).
- Status: Mätmetoden fryst före baslinjen; resultat sparas separat under `output/aim-quality-evaluation/`. Kvalitetsankare och budgetar ändras inte utifrån resultaten.
- Gränsvärdena nedan är val för detta test, inte vetenskapligt etablerade universella kvalitetsgränser. Ändringar efter första körningen kräver en ny protokollrevision och ommätning av berörda jämförelser.

## 1. Huvudregel

En produkt är kvalitetsgodkänd när samtliga elva dimensioner har minst **3 av 4**, inga bindande produktkrav är ouppfyllda eller overifierade och inga kritiska fel kvarstår. En godkänd produktbedömning ersätter inte användarens AIM-acceptans.

Visa alltid delbetyg, kravavvikelser och kritiska fel. Tid får inte vägas in i kvalitetsbetyget.

Byggaren får veta kvalitetsdimensionerna och vad nivå 3 kräver, utöver sin produktbrief. Byggaren får inte testledarens dolda preferenser, jämförelseprodukter eller bedömningsanteckningar. I den öppna varianten gäller produktbeslut bara när de faktiskt kommunicerats; utebliven discovery bedöms separat.

## 2. Elva kvalitetsdimensioner med konkreta ankare

För varje dimension: välj det högsta heltalsbetyg vars villkor är uppfyllda. Nivå 4 kräver även nivå 3. Stöd varje betyg med minst en observation och en länk till bild, inspelning, testresultat eller tidsstämplad anteckning. Utebliven kontroll är **overifierad**, inte 0. Känd brist får däremot inte döljas som overifierad.

| Dimension | 0 — Saknas/blockerad | 1 — Betydande brist | 2 — Grundnivå | 3 — Godkänd kvalitet | 4 — Särskilt väl utfört |
| --- | --- | --- | --- | --- | --- |
| **Avsikt och känsla** | Produkten saknar den beställda spelupplevelsen eller kan inte spelas alls. | Spelaren måste huvudsakligen stressa, reagera snabbt eller utföra handlingar utan begriplig koppling till växthuset. | Temat och lugnet finns, men återställning eller utforskande har liten betydelse för upplevelsen. | Spelet är lugnt, handlingarna återställer växthuset synligt och miljön ger anledning att undersöka och tänka. Kommunicerade val om perspektiv och rörelse följs. | Miljö, återkoppling och progression förstärker tillsammans nyfikenhet och återställning; bedömaren kan visa minst två konkreta exempel på hur de gör det. |
| **Spelidé och bandesign** | Ingen fungerande spelregel eller lösningsväg. | Spelaren kan vinna genom slumpmässigt tryckande eller en uppenbar serie oberoende aktiveringar utan resonemang. | Regeln fungerar, men banorna upprepar samma val eller kräver oförklarad gissning. | Banorna introducerar och kombinerar regler; minst en senare bana kräver ett verkligt beroende eller en ordning som spelaren kan resonera fram. Lösningar följer synliga regler. | En senare bana får spelaren att ompröva en tidigare använd strategi och ger en begriplig insikt utan dold regel eller precisionskrav. |
| **Visuell kvalitet** | Centrala objekt eller tillstånd går inte att urskilja. | Layout, kontrast, överlappning eller blandat uttryck försvårar spelet tydligt. | Läsbart men generiskt eller inkonsekvent; återställning och viktiga tillstånd framgår svagt. | Figur, miljö, objekt och UI har en sammanhängande stil och tydlig visuell hierarki. Aktivt/inaktivt och återställt tillstånd kan avläsas. Inga blockerande överlappningar på testytorna. | Medveten komposition, ljus, rörelse eller miljödetaljer gör platsen särpräglad och stöder orientering och stämning; minst två exempel visas. Fler effekter ensamt räcker inte. |
| **Interaktion** | Centrala kontroller fungerar inte. | Återkommande felaktiga handlingar, fastnande rörelse eller otydligt interaktionsmål hindrar normal användning. | Kontrollerna fungerar men har återkommande friktion eller svag återkoppling. | Spelaren kan röra sig, välja mål och interagera förutsägbart. Handlingar ger tydlig respons. Upprepad indata och fokusbyte skapar inte fastnat tillstånd. Ingen precisionshandling krävs för lösning. | Kontextuell återkoppling gör även ogiltiga försök och alternativa handlingar begripliga utan att avbryta spelrytmen; inga återkommande kontrollmissförstånd observeras. |
| **Introduktion och omförsök** | Spelet kan inte läras från leveransen eller aktuell bana kan inte återställas. | Ny spelare behöver upprepade externa instruktioner för grundregeln eller måste börja om hela spelet efter vanliga misstag. | Grundregeln kan läras, men en viktig övergång behöver hjälp eller omförsök ger onödig friktion. | En ny spelare hittar kontrollerna, löser första banan och kan förklara grundregeln utan extern hjälp. En senare regel kan upptäckas i spelet. Omstart återställer aktuell bana via högst två tydliga UI-handlingar. | Ny spelare kan även förutse varför ett tidigare försök misslyckades och själv använda lärd regel i en ny situation utan hjälp. |
| **Funktionell robusthet** | Spelet startar inte eller central progression är blockerad. | Återkommande tillstånds- eller återställningsfel kräver omladdning eller gör utfallet opålitligt. | Normalvägen fungerar men minst ett relevant gränsfall ger ett reproducerbart, icke-kritiskt funktionsfel. | Samtliga obligatoriska funktionella kontroller nedan passerar. Startinstruktionerna fungerar och verifierade begränsningar stämmer med produkten. | Även extra relevanta motexempel härledda av granskaren passerar, inklusive upprepade banbyten, ogiltiga handlingar och återställning från olika delvis lösta lägen. |
| **Kodbegriplighet för människa och AI** | Underhållen källkod saknas eller går inte att följa. | Kryptiska namn, dold styrning eller felaktiga beskrivningar gör centralt beteende svårt att spåra. | Koden går att förstå, men en ny läsare behöver författarens förklaring eller gör ett centralt fel i förståelseprovet. | Både ny mänsklig läsare och ny AI-session kan korrekt lokalisera och förklara banbeskrivning, tillstånd, handling till resultat och återställning med källhänvisningar. Namngivning, formatering och kommentarer stöder förståelsen. | Båda kan dessutom korrekt förutsäga effekten av ett relevant gränsfall och ange ändringsställe och berörda tester utan författarhjälp. |
| **Modularitet och komponentindelning** | Centrala ansvar går inte att skilja åt och förändringar saknar avgränsbara ingångar. | Banor, spelregler, indata och rendering är så sammanflätade eller duplicerade att samma regel måste ändras på flera ställen. | Viss indelning finns, men dolda beroenden eller delat muterbart tillstånd försvårar isolerade ändringar. | Bana/data, spelregler/tillstånd, indata och presentation har tydliga ansvar och begripliga gränssnitt. Delade regler har en ansvarig plats. Domänregler kan verifieras utan att hela UI:t måste spelas manuellt. | Underhållsprovet visar att beteende kan utökas vid avsedd gräns utan att orelaterade ansvar ändras; inga onödiga abstraktionslager behövs för den prövade ändringen. |
| **Underhållbarhet och verifierbarhet** | En avgränsad ändring går inte att genomföra utan en omfattande omskrivning. | Ändringen ger regressioner, duplicerar regler eller kräver ingrepp som en efterträdare inte kan motivera. | Ändringen fungerar efter onödigt breda ingrepp, eller relevanta tester saknar förmåga att upptäcka ett återinfört fel. | En ny utförare klarar det standardiserade underhållsprovet med avgränsat, motiverat diff. Gamla flöden fungerar och relevanta tester upptäcker ett kontrollerat återinfört fel. | Ändringen görs via den etablerade utökningspunkten, testerna täcker både normal- och gränsfall och samma princip fungerar i det faktiska fortsättningsincrementet utan parallell regelimplementation. |
| **Laddning, körprestanda och resursbruk** | Start eller normal spelbelastning hänger eller kraschar. | Återkommande långa stopp eller växande resursbruk gör spelet svårt att använda. | Spelet är användbart men minst en fastställd prestandabudget överskrids eller en verifierad resursläcka återstår. | Mätningarna i avsnitt 3C klarar budgetarna för laddning, respons, bildintervall, tillgångar och stabilitet vid omstarter, med bibehållen funktion och grafik. | Nivå 3 samt profilerad evidens visar motiverat arbete och resursbruk i de dyraste vägarna; en representativ större belastning klaras utan onödig upprepad beräkning eller dold kvalitetsminskning. |
| **Säkerhet** | Ett exploaterbart kritiskt fel exponeras, exempelvis läsning utanför tillåten filyta eller oavsiktlig kodkörning. | Ett exploaterbart allvarligt fel finns i indata, lokal server, hemligheter eller beroenden. | Inga kritiska/allvarliga fel är bekräftade, men en tillämplig säkerhetskontroll har en känd kvarvarande brist. | Faktiska angreppsytor är inventerade; tillämpliga positiva och negativa kontroller i avsnitt 3D passerar och inga kända exploaterbara brister kvarstår. Ej tillämpligt motiveras. | Nivå 3 samt oberoende härledda angreppsfall passerar och en liten regressionskontroll upptäcker en avsiktligt införd brist i en relevant säkerhetsgräns. |

Nivå 4 är inte ett krav för acceptabel kvalitet. Innan fortsättningsändringen finns kan underhållbarhetens nivå 4 vara overifierad; en styrkt nivå 3 gäller då. Välj inte en konststil i efterhand som facit. Abstrakt grafik kan få högt betyg om uttryck, läsbarhet och känsla är väl genomförda.

Fler filer, komponenter, abstraktioner, kommentarer eller tester ger inte automatiskt högre betyg. Bedöm tydliga ansvar, korrekt förståelse och verifierad förändringsförmåga. Ramverk eller ett visst komponentantal är inte krav. Underhållen källkod bedöms separat från minifierade distributionsfiler.

## 3. Kravkontroll och obligatoriska tekniska kontroller

Skapa före bedömningen en kort kravlista från den aktuella briefen och faktiskt lämnade svar. Markera varje krav **pass/fail/overifierat** med belägg. Kravlista och produktpoäng är separata: exempelvis kan snygg grafik inte kompensera för en saknad uttryckligen beställd bana.

Utför samma relevanta kontroller för båda spåren genom ordinarie UI. Dokumentera produktspecifika lösningssekvenser så att kontrollerna går att upprepa.

1. Starta från ren projektkopia enligt levererade instruktioner. Kontrollera att inga odokumenterade tjänster eller tillgångar behövs.
2. Spela varje beställd bana från start till mål. Bekräfta att felaktiga eller ofullständiga lösningar inte ger vinst och att rätt lösning gör det.
3. Starta om varje bana dels efter delvis löst pussel, dels efter en ogiltig handling. Jämför position, objekt, resurser, UI och vinstvillkor med banans ursprungsläge.
4. Utför samma relevanta interaktion fem gånger i följd. Håll inne och släpp rörelseknappen och växla sedan fönsterfokus under rörelse. Kontrollera att inget fastnar eller skapar oavsiktlig progression.
5. Kontrollera banövergång och slutläge. Omladdning ska ge ett begripligt giltigt läge; sparad progression krävs bara om det beställts eller utlovats.
6. Kontrollera 1440 × 900 och 1024 × 768 CSS-pixlar i samma browser, med 100 procent zoom. Kritiska kontroller och spelobjekt ska vara åtkomliga. Mobilstöd bedöms inte om det inte beställts.
7. Stäng av ljud. Viktiga tillstånd ska fortfarande gå att förstå och får inte skiljas åt enbart med färg.
8. Kontrollera browserkonsolen och observerade fel. Rapportera konsekvensen av eventuella fel; räkna inte en orelaterad miljövarning som ett produktfel.
9. Efter nästa increment: upprepa lösning och återställning för samtliga gamla banor och hela kontrolluppsättningen för den nya banan. Granska även ändrade gemensamma funktioner.

**Kritiskt fel:** spelet startar inte, en nödvändig bana kan inte slutföras, centralt speltillstånd förloras eller blockeras utan avsedd återhämtning, eller en vanlig handling hindrar fortsatt spel. Övriga avvikelser får dokumenterad konsekvens och dimension. Ett kritiskt fel blockerar kvalitetsgodkännande oavsett totalpoäng.

### 3A. Begriplighet och ansvarsfördelning

En människa med relevant utvecklarvana och en separat AI-session får varsin identisk ren källkodskopia, normal projektdokumentation och samma fyra frågor. Ingen får författarens chatthistorik eller den andra läsarens svar. AI-sessionen använder samma modell, resonemangsnivå och läsverktyg i alla spår. Ingen kod skrivs i detta läsprov.

1. Var definieras en bana och hur skulle en ny bana registreras?
2. Vem äger det aktuella speltillståndet och vilka vägar får ändra det?
3. Följ en vanlig spelarhandling från indata till ändrad regelstatus och synlig återkoppling. Var avgörs att banan är klar?
4. Vad återställs vid omstart och vad bevaras? Visa källställen och ett relevant test eller en evidenslucka.

Ge läsarna högst 15 minuter för ett första svar. Registrera faktisk tid, lästa filer, begärd hjälp och sakfel. En oberoende granskare kontrollerar svaren mot kod och observerat beteende. Nivå 3 kräver korrekta svar på alla fyra från båda läsarna utan författarhjälp. Ett uteblivet svar vid tidsgränsen är en evidenslucka, inte bevis för dålig kod; en uttryckligt felaktig förklaring är däremot ett observerat missförstånd.

Människans och AI:ns tider och korrekthet redovisas separat. Tokenåtgång kan redovisas om faktiskt uppmätt, men kallas inte kodbegriplighet. Om mänsklig kodläsare saknas ska den delen redovisas som overifierad.

Rita därefter en liten ansvarskarta från faktisk kod: banbeskrivning, spelregler, tillstånd, indata, rendering/UI och eventuell lagring/server. Kontrollera verkliga beroenden, duplicerade regler, delat muterbart tillstånd, onödiga lager och hur tester når spelreglerna. En fil kan innehålla väl avgränsade ansvar; många filer kan fortfarande vara hårt kopplade.

### 3B. Standardiserat underhållsprov

En ny utförarsession gör följande ändring på en separat kopia av varje bedömd snapshot:

> Lägg till en synlig räknare ”Omstarter: N” för aktuell bana. Den börjar på 0, ökar exakt en gång per genomförd omstart, fungerar likadant för alla befintliga omstartskontroller och nollställs vid byte av bana. Räknaren ska inte påverka spelregler eller vinstvillkor. Lägg till relevant verifiering.

Ge samma modell, verktyg och högst 20 minuters aktiv tid till alla utförare. Ingen hjälp från produktförfattaren. Provet behöver inte bli en del av den levererade produkten; kopian används bara för mätning och återförs aldrig till huvudkörningen. Ett underhållsprov får inte i smyg rätta ursprungsprodukten.

Kontrollera 0 vid start, 1 respektive 2 efter två omstarter, alla befintliga omstartsätt, nollställning vid banbyte och oförändrade gamla lösningsvägar. Granskaren ska i en disponibel testkopia återinföra ett fel, exempelvis dubbel ökning eller utebliven nollställning, och kontrollera att relevant test fallerar. Återställ kopian efteråt. Enbart gröna tester före felinjektion räcker inte för påståendet att de upptäcker regressionen.

Mät tid till korrekt ändring, antal försök, ändrade ansvar och oavsiktliga regressioner. Dokumentera varför varje ändrad modul behövde ändras. Filantal och radantal är beskrivande; ett gränssnitts- och tillståndsarbete kan legitimt beröra flera filer. Bred omskrivning, kopierad spellogik och orelaterade ingrepp sänker bedömningen.

Läsprovet och underhållsprovet redovisas separat från byggartiden. Lägg inte deras ändringar eller lärdomar i nästa increments startunderlag. Det ordinarie fortsättningsincrementet ger dessutom evidens om underhållbarhet vid en större, verklig produktändring.

### 3C. Laddning, körhastighet och resurser

Mät den avsedda körbara leveransen; använd produktionsbygget om ett sådant finns. Samma maskin, browserversion, effektläge, viewport 1440 × 900 och samma skärmuppdateringsläge ska användas. Kör i synlig aktiv flik, utan parallella byggjobb eller andra prestandamätningar. Registrera miljön. Vid ett annat skärmuppdateringsläge än 60 Hz ska en gemensam miljö ordnas före jämförelsen; ändra inte gränsen efter att resultaten är kända.

Mät minst tre oberoende körningar av varje arbetslast. Spara råvärden och median; redovisa även sämsta körning. P95 beräknas på många händelser/bildintervall inom varje körning, inte på bara tre sammanfattningsvärden.

| Mått | Arbetslast och instrumentering | Budget för nivå 3 |
| --- | --- | --- |
| Tid till spelbar produkt | Tre kalla browserstarter med tom cache och oförändrat startläge. Från navigationsstart till första banan är synlig och en ordinarie indata ger rätt respons. Verifiera spelbarhet oberoende av en eventuell appmarkering. | Median högst 3 s och ingen körning över 5 s på referensmiljön. |
| Varm omladdning | Tre omladdningar med cache kvar; redovisas separat från kallstart. | Median högst 1,5 s. |
| Laddningsmängd | Logga dokument, kod, stilar, fonter, bilder och ljud som överförs fram till spelbar första bana. Redovisa transfererade och okomprimerade byte, serverns komprimering och antal anrop. | Högst 5 MiB transfererat vid kallstart; inga onödiga återkommande hämtningar av samma oförändrade tillgång under spel. |
| Respons på handling | Minst 30 förutbestämda giltiga och ogiltiga handlingar i representativa speltillstånd. Browsertrace mäter från mottagen indata till första renderade bild med korrekt konsekvens. | P95 högst 100 ms och ingen produktorsakad respons över 250 ms. |
| Bildflyt | Tre 60-sekunders genomspelningar av den mest krävande normala banan med rörelse och interaktion. Mät bildintervall i browsertrace och märk laddning/banbyte separat. | P95 högst 20 ms vid 60 Hz; inga produktorsakade avbrott över 100 ms under vanlig rörelse. |
| Resursstabilitet | Värm upp med fem omstarter/banbyten, gör sedan 20 till. Mät JS-heap efter likvärdig garbage collection, kvarvarande DOM-noder, lyssnare och timers; jämför motsvarande speltillstånd. | Slutlig retained JS-heap får inte öka mer än det större av 5 MiB och 10 procent från uppvärmd bas. Inga upprepade kontroller får ackumulera läckta objekt, lyssnare eller timers per cykel. |

Budgetarna är ingen universell definition av snabb kod; de är förhandsbestämda tekniska mål för detta lilla lokala spel. Ge dem till alla byggare före start. Bekräfta före baslinjen att referensmiljön kan mäta dem. En saknad mätförmåga får inte ersättas med ett påhittat pass; besluta om en likvärdig metod och frys den före mätning.

`PerformanceNavigationTiming` ger navigationstider, men dokumentets load-händelse bevisar inte att spelet är spelbart. `requestAnimationFrame`-intervall är ett kompletterande mått på schemaläggningen, inte bevis för när en fysisk bild visades; browsertrace eller motsvarande renderingsobservation ska styrka respons och flyt. Instrumentering ska vara likvärdig och dess overhead redovisas. Se [MDN: navigationstider](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceNavigationTiming) och [MDN: requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame).

Profilera de dyraste stegen: regeluppdatering, rendering, tillgångsladdning och eventuell sökning/beräkning. Granska onödiga fullständiga omberäkningar, arbete varje frame som kunde göras vid förändring, växande datastrukturer och resurser som aldrig frigörs. Mät även största tillåtna normala bana; konstruera inte ett obegränsat stresstest för en produkt som bara stöder fasta banor. För ett annonserat stöd för större banor testas dess angivna gräns med bibehållna regler.

Sänk inte bildkvalitet, antal objekt eller funktioner i ett spår för att vinna hastighet. En kall lokal körning mäter inte internetprestanda; gör inga sådana anspråk. Kontrollera faktisk bild- och ljudminnesanvändning genom tillgängliga browsermått där JS-heap inte täcker resurserna, och redovisa täckningsbegränsningen.

Ett överskridande av budget eller en läcka blockerar nivå 3. Inom budget ska en reproducerad försämring över 20 procent och minst 100 ms för laddning, 10 ms för respons eller 2 ms för bildintervall redovisas som väsentlig prestandaregression även om poängen fortfarande är 3. Bedöm absoluta tider och alla råkörningar; nära mätbruset görs likvärdiga ommätningar i båda spåren.

### 3D. Säkerhet utifrån faktisk angreppsyta

Inventera vad produkten och dess körinstruktioner faktiskt exponerar: URL-parametrar, DOM, eventuell lokal lagring eller filimport, lokal HTTP-server, nätverksanrop, beroenden och byggskript. Frånvaro av en funktion ska styrkas genom en avgränsad kod-/konfigurationskontroll. Kräv inte kontosäkerhet av en produkt utan konton, och skapa inte nya funktioner bara för att kunna säkerhetstesta dem.

Välj relevanta kontroller från [OWASP ASVS](https://owasp.org/projects/asvs) och dokumentera den använda versionen och kontroll-ID:n vid utförandet. ASVS ger ett underlag för verifiering av säkerhetskontroller; denna begränsade granskning innebär ingen generell certifiering.

| Yta | Konkret kontroll när ytan finns |
| --- | --- |
| Otillförlitliga data till UI | Spåra indata till DOM eller annan exekverande funktion. Prova ofarliga markup-/injektionsmarkörer och kontrollera att data inte blir exekverbar kod. |
| Sparläge, banfiler och URL-värden | Prova fel typ, saknade fält, okända värden och en stor men avgränsad testindata. Fel ska hanteras utan kodkörning, oändlig loop eller ett läge som inte kan återställas. |
| Lokal HTTP-server | Kontrollera avsedd loopback-bindning, tillåtna värdnamn, rotkatalog och sökvägsnormalisering. Prova avvisning av traversal och oavsiktlig filåtkomst genom riktiga HTTP-anrop. Projektets hemligheter, Git-data och godtyckliga filer ska inte exponeras. Kontrollera Origin och skydd mot oönskade skrivningar när servern har muterande endpoints; en statisk server behöver inte låtsas ha sådana endpoints. |
| Nätverk och känsliga uppgifter | Inspektera levererade filer och observera nätverkstrafik. Inga hemligheter, oväntad telemetri eller obeställda fjärrberoenden får ingå. |
| Beroenden och byggkedja | Inventera direkta/transitiva beroenden och installationsskript, verifiera reproducerbara versioner där sådana används och granska rapporterade sårbarheters tillämplighet. Kör relevant tillgänglig kontroll; en tom scannerlista eller inga beroenden bevisar inte säkerhet. |
| Resursgränser | Kontrollera att extern eller lagrad indata inte orsakar obegränsad allokering eller loopar. Knyt negativa prov till faktiskt stödda ingångar. |

Kör angreppsfallen endast mot isolerade testkopior och egna lokala testservrar. För varje kontroll sparas ingång, förväntat skydd, observerat resultat och begränsning. ”Ej tillämpligt” måste ha motivering; om samtliga kontroller avfärdas utan analys är säkerheten overifierad.

Varje bekräftad exploaterbar kritisk eller allvarlig sårbarhet blockerar hela produktgodkännandet, oavsett Q. Nivå 3 kräver även att andra kända tillämpliga säkerhetsbrister är åtgärdade och kontrollerna verifierade. Rapportera ”inga kända brister i de prövade gränserna”, aldrig ”helt säker”. Oberoende motexempel och eventuell felinjektion för nivå 4 utförs i disponibel kopia och får inte ändra huvudprodukten.

## 4. Praktiskt bedömningspass

### Oberoende produktgranskare

En granskare som inte byggt produkten sammanställer kravkontroll, browserkontroller och elva delbetyg utifrån speltest, kodläsning, underhållsprov samt prestanda- och säkerhetskontroller. Använd samma granskare eller samma bedömaruppsättning för jämförelsespåren. Bedöm produkterna under neutrala etiketter och variera visningsordningen. Öppna processloggar för discovery först efter produktbedömningen. Kodgranskning kan röja metodval; redovisa denna begränsning i blindningen.

Bedöm vid tre sparade hållpunkter: **första inlämning**, **sista inlämning inom budget** och **efter fortsättningsincrementet**. Om första och sista är samma version görs ingen extra granskning. Frys koden för varje bedömd version; rätta aldrig en produkt i dess bedömda snapshot.

### Kort mänskligt spelartest

För en komplett bedömning av lärbarhet behövs minst en verklig förstagångsspelare per produkt som bedöms. Personen får samma korta instruktion: ”Starta spelet, försök återställa växthuset och använd omstart när du vill. Berätta efteråt hur du tror att reglerna fungerar.” Visa spelets egna instruktioner men inte lösningar, metodnamn eller tidigare spelares kommentarer.

Avsätt 15 minuter för den första upplevelsen och högst 5 minuter för första mötet med den nya banans regel. Registrera tid till första avsiktliga spelhandling, löst första bana, omstart, externa hjälptillfällen och spelarens förklaring av grundregeln. Dessa tider är observationer, inte nya dolda produktkrav. Om en observation inte hinns med är den overifierad; timeout är inte automatiskt bevis för oförmåga.

Ge inte ledtrådar under den oassisterade delen. Om hjälp behövs, registrera exakt vad som gavs och fortsätt som ett separat assisterat försök. Ett assisterat resultat bevisar inte självständig inlärning.

Samma person ska inte räknas som förstagångsspelare för två produkter med samma mekanik. För den nya banan ska spelaren redan känna den egna produktens grundregler, men inte den nya regeln. Om nya spelare saknas, redovisa begränsningen och håll berörda kriterier overifierade. En agents genomgång ersätter inte denna observation.

En spelare per produkt är ett begränsat pilotunderlag. För en robustare bedömning används fler, likvärdigt rekryterade spelare i samtliga spår. Utöka inte bara det spår vars resultat var oväntat.

## 5. Mätning av discovery och kontinuitet

Dessa mått redovisas bredvid produktpoängen och ingår inte i Q. Använd **pass/fail/overifierat/ej tillämpligt** och länka faktisk händelse, beslut eller fil.

| ID | Kontroll |
| --- | --- |
| D1 | Öppet uppdrag: perspektiv/rörelse och huvudmekanik hanteras som betydelsefulla val före större implementation. Provisoriska experiment är tillåtna. |
| D2 | Val förankras i verkliga svar eller faktiskt delegerat mandat; antaganden är märkta och ingen fråga besvaras genom fabricerad användarpreferens. |
| D3 | Detaljerat uppdrag: inga redan besvarade produktval öppnas igen utan dokumenterat sakligt skäl. |
| D4 | Relevant kompetens eller verktygsbehov hanteras i utförandet, med konkret användning eller en ärligt redovisad lucka. Skillnamn ensamma ger inte pass. |
| K1 | Ny session återanvänder de giltiga produktbeslut som den nya banan beror på. |
| K2 | Ny session återanvänder inte antaganden som mänskliga beslut och hittar inte på tidigare acceptans. |
| K3 | Ingen onödig upprepning av onboarding, redan besvarade frågor eller oförändrade planer. |
| K4 | Ny bana lär ut en ny regel och gamla banor klarar regressionstestet. |

Räkna frågor som semantiska beslutspunkter, inte antal meddelanden: tre separata frågor i en dialog är tre. Klassificera dem som nödvändiga, upprepade eller självständigt undersökningsbara och motivera avvikelser. Färre frågor ger inget eget bonusbetyg.

## 6. KPI:er och tidsregistrering

**Primärt KPI: kvalitetsindex Q**, alltid tillsammans med elva delbetyg och godkänd/underkänd/overifierad status:

`Q = 100 × (summan av de elva delbetygen) / 44`

Indexet ligger mellan 0 och 100. Det sammanfattar ordinala bedömningar; fem indexpunkter betyder inte att produkten är fem procent bättre. Saknas bedömning i någon dimension visas ingen komplett Q.

**Kompletterande KPI:er:** andel kvalitetsgodkända körningar, tid till kvalitetsgodkännande, aktiv byggartid, total förloppstid, upprepade frågor, extern användarinsats, rättningsomgångar och kritiska fel. Visa även mänsklig respektive AI-baserad kodförståelse, tid och regressioner i underhållsprovet, kalla/varma laddningstider, bytes, respons, bildintervall, minnesutveckling och säkerhetsfynd med allvarlighetsgrad. Produktens körprestanda är ett separat mått från tiden det tog att utveckla den. Visa discovery- och kontinuitetsresultaten separat.

Registrera tidsstämplar vid start, inlämning, paus/väntan, återupptagning, feedback och stopp. Start är när byggaren får uppdraget i den förberedda miljön. Förloppstid är väggklockans tid till respektive hållpunkt. Aktiv byggartid är unionen av intervall när någon byggaragent eller dess verktyg arbetar; parallella agenttider summeras inte. Tillfälliga väntetider dras bara av om de faktiskt loggats och inget självständigt arbete pågår. Behåll råtiderna.

Tid till kvalitetsgodkännande mäts till inlämningstidpunkten för den första sparade version som senare verifieras uppfylla kvalitetsnivån. Rapportera även när verifieringen var klar. Mellanliggande ogranskade kodversioner får inte ges en påhittad tid för kvalitetsgodkännande. Extern gransknings- och väntetid visas separat från byggartiden.

Vid budgetstopp bedöms senast inlämnad snapshot. Finns ingen inlämning bevaras arbetsläget som ofullständigt, utan att det benämns färdig leverans. En körning som aldrig når kvalitetströskeln får ”ej uppnått inom budget”, inte en uppskattad sluttid. Döljs misslyckanden genom att bara medelvärdesbilda lyckade tider är jämförelsen ogiltig.

## 7. Beslutsregel för före/efter

Användarens korrigerade omfattning är **en baslinje och en kandidatkörning av samma öppna uppdrag**. Tidigare plan om tre körningar per variant gäller inte. Kvalitetsankare, kravkontroller och tekniska mätbudgetar ovan är oförändrade; upprepade prestandaprov görs på samma produkt.

Visa Q och samtliga elva delbetyg sida vid sida när underlaget är komplett. En tydlig observerad kvalitetsförbättring i detta par kräver minst 5 indexpunkter högre Q, kvalitetsgodkänd kandidat, ingen sämre dimension och inga dolda väsentliga råa prestanda-/säkerhetsregressioner. Redovisa även mindre skillnader, utan att kalla dem tydlig vinst enligt tröskeln. Kvalitet får inte kvittas mot snabbare process.

En observerad effektivitetsförbättring kräver kvalitetsgodkända produkter, oförsämrad Q och alla dimensioner samt minst 15 procent kortare aktiv byggartid till den bedömda inlämningen. Om baslinjen inte når kvalitetströskeln är tid till kvalitetsgodkännande inte jämförbar.

Saknas avgörande evidens är slutsatsen ”kan inte avgöras”. Ett enda par kan bara stödja en slutsats om detta uppdrag, inte statistisk signifikans eller generell överlägsenhet. Fler byggarkörningar kräver ny uttrycklig beställning.

## 8. Kort resultatmall per snapshot

```text
Körnings-ID / variant / upprepning:
Produktetikett / snapshot-hash / inlämningstid:
Bedömare / spelare / browser och viewport:
Faktiskt kommunicerade krav och beslut:
Kravkontroll: pass / fail / overifierat, med länkar
Delbetyg produkt: avsikt __; bandesign __; visuellt __; interaktion __; introduktion __; robusthet __
Delbetyg engineering: kodbegriplighet __; modularitet __; underhållbarhet __; prestanda __; säkerhet __
Belägg och begränsning för varje delbetyg:
Q: __ / 100, eller ofullständig
Kritiska fel / övriga kravavvikelser:
Kvalitetsstatus: godkänd / underkänd / overifierad
Browserkontroller och spelartest: observationer och artefakter
Kodförståelse människa / AI: korrekta svar, hjälp, tid och källhänvisningar
Ansvarskarta / underhållsprov: tid, diff, regressioner och felinjektion
Prestanda: råkörningar, kall/varm start, bytes, respons, bildintervall och minne
Säkerhet: ytor, kontroller, källversioner, negativa prov och kvarvarande fynd
Discovery D1–D4 / kontinuitet K1–K4: status och belägg
Aktiv byggartid / förloppstid / användarväntan / extern granskning:
Nödvändiga frågor / upprepade frågor / hjälptillfällen / rättningsomgångar:
Native AIM-status och verklig acceptans:
```

Kvar att bestämma i körningsmanifestet är resursbudget, faktiska modell- och paketversioner, bedömarbemanning och verkligt mandat. Själva kvalitetskriterierna, poängankarna, mätreglerna och jämförelsetrösklarna är definierade här.
