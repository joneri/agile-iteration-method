# Kravunderlag för en möjlig omarbetning av AIM 4

- Datum: 2026-10-15.
- Status: Färdigställt kravunderlag efter användarens beslut och RnD:s granskning. Implementation och lansering ingår inte i detta uppdrag.
- Omfattning: Ansvar, User Stories, leveransåtagande, konsekvensbedömning, självständighet, produktkvalitet och copy.
- Dokumentroll: Planeringsunderlag. Ändrar inte befintliga beteendekontrakt, installationer, webbplats eller pågående produktprojekt.
- Beslutad målbild: PO äger Epics; TDO äger User Stories och incrementets leverans. Att dagens implementation har annat ägarskap gör inte målbilden till en öppen fråga.

## 1. Syfte och utgångspunkt

AIM ska ge användaren en bättre slutprodukt genom välgrundade produktbeslut och genomarbetat utförande. Processen får ta längre tid när det förbättrar resultatet, inom användarens mandat. Fler roller, dokument, Stories eller tester är inte i sig ett bättre resultat.

AIM 3.2.1 är referens för det arbetssätt användaren vill bevara: TDO formar ett sammanhängande increment från en Epic och ansvarar för att leverera det. User Stories ska tillföra användbar detaljering av detta increment. De får inte medföra att helheten, kvaliteten eller leveransansvaret försvinner mellan separata delar.

De tidigare försöken motiverar omprövning av AIM 4. De bevisar inte att User Stories eller en enskild ansvarsfördelning orsakade sämre produkter. En ny version ska bedömas efter resultat, inte efter versionsnummer eller processens ambitionsnivå.

Detta dokument innebär inget mandat att återställa till AIM 3.2.1, bygga fler testprodukter, starta jämförelser, ändra modeller eller driva två aktiva versioner parallellt.

## 2. Ansvar och sammanhängande leverans

### ANS-01 — PO äger Epics

Product Owner äger Epicens produktavsikt, önskade utfall, målgrupp, omfattning, produktprioritet och övergripande kvalitetskrav. PO ska kunna bedöma om incrementet för produkten mot det avsedda utfallet.

### ANS-02 — TDO äger User Stories och incrementet

TDO ansvarar för att skapa och förfina User Stories från Epicen, formulera deras acceptanskriterier, hantera beroenden och sätta samman ett genomförbart increment. TDO äger både detaljeringen och det sammanhängande leveransåtagandet.

User Stories är en mer detaljerad uppdelning av arbetet mot incrementets mål. De ersätter inte det gemensamma målet och får inte bli isolerade leveranser vars sammanlagda användarupplevelse ingen ansvarar för.

PO och TDO ska reda ut konflikter mellan produktavsikt och genomförande. TDO får inte tyst ändra produktprioritet, skära bort nödvändigt innehåll eller sänka kvalitetskrav genom hur Stories formuleras.

I befintlig leveransplan ska TDO beskriva vilken sammanhängande användbar förmåga eller förbättring incrementet ska ge och varför de valda Stories räcker för det. Ett litet urval som är lätt att avsluta är inte tillräckligt om det missar det överenskomna värdet. Verifierat lärande får vara huvudutfall när uppdraget uttryckligen gäller utforskning; det får inte ersätta en beställd fungerande produkt.

### ANS-03 — Genomförande, granskning och acceptans

Dev genomför arbetet. Reviewer granskar både om nedbrytningen täcker det överenskomna bidraget till Epicens avsikt och om Story-kriterierna, teknisk kvalitet och produktens faktiska beteende håller. Hela Epicen behöver inte slutföras i ett increment. TDO ansvarar för integration och samlad leveransevidens. PO bedömer produktutfallet. Användaren behåller acceptansmandatet; en agent får inte tillskriva användaren ett godkännande som inte finns.

Produktprioritet och teknisk genomförandeordning ska skiljas åt. PO äger produktprioritet även mellan Stories. TDO får ordna arbetet efter beroenden inom mandatet, men får inte omprioritera produktmål enbart för att något bedöms svårt.

### ANS-04 — TDO väljer genomförandeordning inom incrementet

TDO bestämmer ordningen utifrån beroenden, integrationsrisk och befintligt mandat. Stories kan implementeras sekventiellt eller parallellt när resurser och mandat medger det. Parallellisering ger inte i sig rätt att starta fler agenter, ändra kostnadsprofil eller utöka uppdraget.

Delar ska verifieras och vid behov granskas under arbetet så att betydelsefulla fel upptäcks tidigt. Integration ska ske så tidigt som relevanta delar kan fungera tillsammans. Den samlade granskningen och valideringen omfattar incrementets produktutfall och kriterierna för samtliga valda Stories. En fullständig roll- och acceptanscykel krävs inte för varje enskild Story. Användarens acceptansmandat kvarstår.

Korrigeringar ska följas av ny granskning och verifiering av berörda kriterier och integrationer. Oförändrad, fortfarande relevant evidens får återanvändas; hela processen behöver inte startas om.

## 3. Krav på User Stories

### US-01 — Varje Story ska beskriva ett begripligt behov

En Story ska ha:

- ett stabilt ID och en tydlig koppling till en primär Epic,
- en kort, konkret titel,
- en relevant användare eller aktör, ett behov och det värde behovet ger,
- observerbara acceptanskriterier med stabila identifierare,
- relevanta beroenden och avgränsningar, direkt eller genom tydlig hänvisning till leveransplanen.

Felbeteenden, kvalitetskrav och risker ska beskrivas där de påverkar utfallet. Tekniska uppgifter får finnas under Stories eller i leveransplanen. AIM ska inte hitta på användarpersonor eller användarnytta för att klä varje kodändring i ett Story-format.

### US-02 — Detaljering ska hjälpa genomförandet

Storleken och antalet Stories ska styras av vad som gör behov, ansvar och verifiering tydliga. Det finns inget mål för antal Stories och inget krav på att varje Story ska kunna driftsättas fristående. AIM får inte dela upp arbetet så att en fungerande användarresa eller sammanhängande design tappas bort.

Utkast får vara ofullständiga. Innan TDO gör ett leveransåtagande ska berörda Stories vara tillräckligt klara för att genomföra och bedöma. Gemensamma kvalitetskrav får refereras från ett gemensamt kontrakt i stället för att kopieras till varje Story.

### US-03 — Inga Story Points

Story Points behövs inte och ska inte införas som obligatoriskt fält, uppskattningsritual eller grund för kapacitet. Generiska komplexitetspoäng eller påhittade tidsestimat ska inte ersätta dem.

### US-04 — Åtagandet gäller hela den valda leveransen

Alla Stories som TDO åtar sig för leveranskörningen ska planeras för att bli färdiga, integrerade och verifierade inom åtagandet. En leveranskörning är här arbetet mot det valda incrementet, inte en enskild agentsession eller ett kontextfönster. Sessionsslut får inte användas som skäl att lämna över ett ofullständigt åtagande som färdigt. Godkända deltester eller stängda Stories räcker inte om incrementets sammanhängande resultat saknas.

Svårigheter ger inte rätt att tyst lämna delar till senare eller deklarera en ofullständig leverans färdig. Om ett verkligt hinder eller en konflikt med mandat eller resursram uppstår ska TDO redovisa vad som återstår och föreslå en konkret väg framåt. Åtagandet ger inte rätt att överskrida mandatet för att framtvinga ett avslut.

Avbrott och återupptagning ska bevara beslut, färdigt arbete och kvarvarande åtaganden. Färdigimplementerat och verifierat ska skiljas från användaraccepterat. Väntan på användaracceptans innebär inte att implementationen måste göras om, och medger inte att AIM själv registrerar acceptans.

### US-05 — Bevara överenskomna krav och historisk acceptans

Valda Story-kriterier och incrementets överenskomna utfall ska bevaras som grund för granskning. TDO får ändra tekniskt genomförande inom mandatet, men får inte skriva om kraven i efterhand för att få resultatet godkänt.

Ändrat produktutfall, ändrad omfattning eller sänkta godkända krav kräver tillämpligt ägarbeslut. Vid uttryckligen beslutad omplanering ska ursprungligt åtagande, beslut, ändringsskäl och kvarvarande behov bevaras. Redan accepterade krav och resultat får inte skrivas över. Använd befintliga historik- och beslutsytor, inte ett nytt parallellt protokoll.

## 4. Komplexitet och resursbeslut

### KOM-01 — Beskriv vad som gör arbetet osäkert

TDO ska uppmärksamma konkreta osäkerheter och konsekvenser: exempelvis ett okänt tekniskt beroende, en känslig dataändring, flera berörda komponenter eller ett produktval som påverkar upplevelsen. Bedömningen ska leda till en användbar åtgärd när det behövs, såsom en avgränsad undersökning, prototyp eller riktad granskning.

En etikett som ”hög komplexitet” är inte tillräcklig motivering för fler agenter, mer administration, ändrad kostnadsprofil eller sänkt ambition.

### KOM-02 — Ingen automatisk ändring av kostnad eller prioritet

Automatisk koppling mellan komplexitet, kostnadsprofil och produktprioritet är inte beslutad. Den ska inte införas som del av dessa krav utan separat ställningstagande.

TDO får rekommendera en annan insats när en konkret nytta eller risk motiverar det. Rekommendationen ska beskriva konsekvensen och följa befintligt mandat. Svårare arbete får inte automatiskt nedprioriteras eller få sämre kvalitet.

## 5. Generella krav på mandat och konsekvensbedömning

### MAN-01 — Självständighet inom det överenskomna uppdraget

AIM ska fatta självständiga beslut inom uppdraget och fortlöpande hålla arbetet inom användarens avsikt, överenskommen omfattning, kvalitetskrav, resursramar och befintliga godkännanden. Inför en möjlig väsentlig avvikelse ska konsekvenserna klarläggas innan den nya investeringen eller effekten uppstår. Rutinbeslut inom mandatet kräver inget separat bedömningsprotokoll.

Att AI:n bedömer något som bättre, säkrare eller mer tillförlitligt ger inte i sig mandat att utöka uppdraget. Uttryckligen överenskomna antal och begränsningar gäller även när agenten ser metodmässiga fördelar med mer arbete.

### MAN-02 — Skilj genomförandebeslut från ändrat uppdrag

AIM ska normalt själv välja ändamålsenlig kodstruktur, komponentindelning, tekniska detaljer och relevant verifiering samt rätta fel inom det beslutade arbetet.

Förändringar som innebär väsentligt annan produktriktning, fler självständiga leveranser, en utökad experimentkampanj eller väsentligt större resursåtgång kräver stöd i befintligt mandat eller ett nytt ägarbeslut innan det beroende arbetet startar. Detsamma gäller externa, publicerande eller destruktiva åtgärder när de inte redan är auktoriserade.

Tidigare godkännanden ska återanvändas. Förslag, tystnad och förfluten tid är inte godkännanden.

### MAN-03 — Bedöm den samlade konsekvensen

Bedömningen ska täcka de relevanta konsekvenserna för tid, kostnad, produkt, kvalitet, externa effekter och återställbarhet. Även summan av flera små åtgärder och samtliga agenters arbete ska räknas in. Områdena är stöd för omdömet, inte en obligatorisk checklista för varje verktygsanrop.

Att filer kan återställas betyder inte att förbrukad tid och kostnad kan återställas. Ett större åtagande får inte kringgå begränsningar genom att delas upp i små steg eller delegeras till flera agenter.

### MAN-04 — Kvalitet och resurser ska hanteras tillsammans

Hög kvalitetsambition är inte ett obegränsat resursmandat. Begränsad budget är inte tillåtelse att tyst sänka överenskommen kvalitet. Om dessa krav inte går att förena ska AIM synliggöra konflikten och ge en konkret rekommendation med konsekvenser.

Avsaknad av en numerisk budget betyder inte obegränsad budget. Arbetet ska stå i rimlig proportion till uppdraget. AIM får inte hitta på ett eget gränsvärde som ger rätt att utöka uppdraget.

### MAN-05 — Gemensamma gränser för alla roller

TDO ansvarar för att leveransplanen ryms inom mandatet och att förändringar bedöms innan de blir nya åtaganden. Alla roller och delegerade agenter ska följa samma gränser. En agents förslag till en annan agent utökar inte användarens mandat.

När en avvikelse upptäcks ska den berörda utökningen stoppas. AIM ska redovisa vad som faktiskt gjorts, vad som återstår och kända resurskonsekvenser. Annat redan auktoriserat arbete kan fortsätta när det är oberoende av beslutet.

### MAN-06 — Lättviktigt i vardagen, kontrollerbart vid gränserna

Konsekvensbedömningen ska vara en del av det vanliga arbetet, inte ett obligatoriskt formulär eller nytt godkännandesteg för varje implementation. Frågor ska gälla verkliga mandatkonflikter och betydelsefulla öppna produktval.

Vid framtida implementation bör uttryckliga, mätbara gränser även kunna kontrolleras tekniskt där det är praktiskt, exempelvis tillåtet antal byggarkörningar, resursgränser och delegerade uppdrag. En allmän instruktion om gott omdöme eller en självskattad risksiffra ska inte räknas som bevis för att gränserna efterlevs.

## 6. Produktkvalitet och återanvändning av kunskap

### KVA-01 — Bedöm den faktiska produkten

Funktion, begriplighet, visuellt uttryck, samspel mellan delar och relevant användarupplevelse ska bedömas i den fungerande produkten. I ett spel omfattar detta exempelvis rörelsekänsla, återkoppling, presentation och hur spelaren lär sig mekaniken.

Godkända tekniska tester är nödvändig evidens för det de prövar, men bevisar inte ensamma god design eller användarupplevelse. Brister i helheten ska inte döljas bakom uppfyllda enskilda Story-kriterier.

Kodens läsbarhet för människa och AI, lämplig komponentindelning, underhållbarhet, laddnings- och körprestanda samt säkerhet ska fortsatt ingå när de är relevanta. Visuell kvalitet får inte användas som skäl att bortse från dem.

Före större implementation ska avgörande kvaliteter konkretiseras genom observerbara kännetecken, relevanta referenser eller exempel på vad som inte skulle uppfylla uppdraget. Giltiga tidigare kvalitetsmål ska återanvändas. Detta ingår i befintlig krav- och leveransplanering och kräver inget nytt formulär eller godkännandesteg.

Upptäckta väsentliga krav- och kvalitetsbrister inom mandatet ska rättas och berört beteende verifieras igen. Att bara lista bristerna i slutrapporten räcker inte när de kan åtgärdas inom uppdraget. Skilj brister mot överenskommen kvalitet från valfria förbättringar och granskarens personliga smak. En föreslagen förbättring ska inte bli ett nytt krav utan stöd i uppdraget.

Om en avgörande upplevelsekvalitet inte kan bedömas med tillgängliga verktyg och evidens ska den redovisas som overifierad. AIM ska inte låta fungerande kod eller en stillbild bevisa egenskaper de inte visar. En verklig konflikt med mandat eller resurser hanteras enligt MAN-04.

### KVA-02 — Anpassa förarbetet till underlaget

En avsikt kan uttryckas som en idé eller som ett detaljerat krav. AIM ska återanvända det som redan är klarlagt och endast komplettera betydelsefulla luckor eller motsägelser. Ett moget underlag ska normalt ge kortare förarbete, utan sänkta krav på genomförande och verifiering.

Tidigare beslut, relevanta skills och bestående projektkunskap ska användas även mellan sessioner. Ett nytt increment är inte i sig skäl för ny onboarding eller full omkalibrering. Skillanvändning ska vara relevant och faktisk; namn på skills är inte kvalitetsbevis.

### KVA-03 — Förbättringar ska styrkas utan att testuppdraget växer

En framtida utvärdering ska följa överenskommet testuppdrag, antal körningar och förhandsbestämda kvalitetskriterier. Jämförbar utgångspunkt, modellinställningar, resurser och bedömning ska dokumenteras. Begränsningar och osäkerhet i slutsatserna ska redovisas.

Ett högre sammanvägt resultat får inte dölja en oacceptabel försämring av ett viktigt kvalitetskrav. Snabbare eller billigare leverans räcker inte som förbättring om produkten blir väsentligt sämre.

Detta krav startar ingen utvärdering. Tidigare underkända försök och sparad evidens ska bevaras med korrekt status.

## 7. Copy som fyller en funktion

### COPY-01 — Varje text ska hjälpa den avsedda läsaren

AIM ska producera konkret text som hjälper människor att förstå, orientera sig, agera, fatta beslut eller ta del av en avsedd upplevelse. Säljande men innehållslösa formuleringar och text som bara beskriver den uppenbara layouten ska omarbetas eller tas bort.

### COPY-02 — Rubriker är val, inte obligatorisk dekoration

Rubrik, underrubrik och överrubrik ska var för sig ha en tydlig funktion; alla nivåer behöver inte finnas. En rubrik ska identifiera innehåll, uppgift, faktiskt tillstånd eller konkret relevant nytta. När sammanhanget redan är tydligt kan ingen extra synlig rubrik vara rätt lösning.

Att ta bort dekorativ text får inte ta bort nödvändiga tillgängliga namn, begriplig navigering eller relevant semantisk struktur.

### COPY-03 — Varje extra rad ska tillföra något

Ta bort upprepningar och text som bara fyller en visuell mall. Behåll förklaringar som tillför nödvändig information, exempelvis nästa steg, en begränsning eller följden av ett val.

Om en beskrivning kan klistras in i många helt olika produkter utan att ändras är det en signal att pröva om den behöver konkretiseras eller tas bort. Detta gäller inte etablerade funktionella ord som ”Spara”, ”Inställningar” eller ”Avbryt”.

### COPY-04 — Ton och påståenden ska passa produkten

En funktionell appvy ska inte få reklamtext som standard. Marknadsföring får vara övertygande men ska vara konkret och hålla sig till styrkta påståenden. Ord som ”smart”, ”kraftfull”, ”sömlös”, ”bäst” eller ”AAA” ska inte ersätta information eller belägg. Personlighet, humor, berättande och dramatik är välkomna när de fyller produktens syfte; detta är ingen ordlista med förbjudna uttryck.

Instruktioner, knappar, status- och felmeddelanden ska beskriva verkligt beteende. De får inte lova att data sparats, att något är säkert eller att en åtgärd kan ångras utan stöd i produkten.

### COPY-05 — Produkten ska stå på egna ben

Behåll befintliga krav på mottagarens sammanhang: privat konversation, tidigare AI-misstag, övergivna alternativ och intern arbetsprocess ska inte läcka in i produkttext för en publik som inte behöver informationen. Historik hör hemma där den fyller ett syfte, exempelvis i en ändringslogg. Produktens vanliga gränssnitt ska uttrycka vad som gäller nu.

### COPY-06 — Granska copy i sitt faktiska sammanhang

PO ansvarar för målgrupp och kommunikativt syfte. TDO omsätter relevanta krav i acceptanskriterier och säkerställer helheten. Dev skriver och anpassar text i produkten. Reviewer granskar begriplighet, relevans, redundans, ton och faktiska påståenden i den renderade vyn eller motsvarande användningssammanhang.

En ordlista eller automatisk textkontroll räcker inte. Meningslös eller vilseledande copy är ett produktkvalitetsfel, inte automatiskt valfri slutputs.

| Text eller mönster som ska ifrågasättas | Lämpligare lösning i rätt sammanhang | Skäl |
| --- | --- | --- |
| ”Två flikar – en app” över en kontrollpanel | ”Kontrollpanel”, eller ingen extra rubrik | Identifierar vyn när det behövs; säljer inte layouten. |
| ”En smartare upplevelse” ovanför inställningar | ”Inställningar” | Beskriver vad användaren hittar. |
| ”Allt du behöver, på ett ställe” under en redan tydlig rubrik | Ta bort raden, eller skriv den specifika information användaren saknar | Undviker ett generiskt löfte. |
| Överrubrik, rubrik och underrubrik som alla säger att användaren kan hantera projekt | Behåll nödvändig orientering och eventuellt en konkret instruktion | Varje nivå behöver inte finnas. |

## 8. Acceptansfall

Dessa fall konkretiserar kraven inför en eventuell implementation. De ger inget mandat att starta nya produktbyggen. Kontrollernas omfattning ska väljas inom det då överenskomna uppdraget.

| ID | Situation | Förväntat beteende |
| --- | --- | --- |
| A-01 | En Epic ska bli ett increment | PO äger Epicen. TDO skapar och äger Stories, deras kriterier och den sammanhängande leveransplanen. |
| A-02 | Alla enskilda Stories passerar sina lokala tester men användarresan fungerar dåligt | Helheten rapporteras som bristfällig och hanteras innan leveransen påstås uppfylla kraven. |
| A-03 | TDO åtar sig flera Stories | Samtliga ingår i leverans och verifiering; ingen försvinner tyst eller flyttas för att ge sken av färdig leverans. |
| A-04 | Ett hinder gör åtagandet omöjligt inom mandatet | AIM redovisar hindret och återstående arbete, rekommenderar en väg framåt och tillskriver inte ägaren ett ändrat beslut. |
| A-05 | Ägaren beställer en baselineprodukt och efterfrågar tillförlitlig jämförelse | AIM bygger inte flera fristående produkter. Behov av fler körningar blir en motiverad rekommendation, inte ett eget nytt uppdrag. |
| A-06 | En komponent behöver refaktoreras eller ett relevant fel rättas inom uppdraget | AIM gör arbetet och lämplig verifiering utan onödig tillståndsfråga. |
| A-07 | Flera små åtgärder eller delegerade uppdrag skulle tillsammans utöka omfattningen väsentligt | Den sammanlagda konsekvensen upptäcks före den nya investeringen; delegering används inte som undantag. |
| A-08 | Arbetet bedöms komplext | Konkreta osäkerheter och proportionerliga åtgärder beskrivs. Ingen automatisk omprioritering, modelländring eller kostnadsökning sker. |
| A-09 | Ett detaljerat krav eller ett nytt increment med giltiga tidigare beslut lämnas in | AIM återanvänder underlaget, respekterar tidigare mandat och frågar bara om betydelsefulla kvarvarande luckor. |
| A-10 | En appvy innehåller ”Två flikar – en app” utan ytterligare informationsvärde | Texten tas bort eller ersätts av en saklig, användbar benämning. |
| A-11 | En vy har upprepande överrubrik, rubrik och underrubrik | Överflödiga nivåer tas bort. Nödvändig orientering, förklaring och tillgänglighet bevaras. |
| A-12 | Copy innehåller generiska löften eller hänvisningar till privata AI-korrigeringar | Texten skrivs om utifrån verklig funktion och publikens sammanhang; granskning sker i produkten. |
| A-13 | Ett marknadsförings- eller berättande uppdrag behöver uttrycksfull text | AIM tillåter relevant personlighet och kreativitet utan tomma eller ogrundade påståenden. |
| A-14 | En kandidat är snabbare men brister i överenskommen produktkvalitet | Kandidaten förklaras inte bättre enbart på grund av tidsvinsten eller ett högre totalpoäng. |
| A-15 | Stories har olika beroenden och integrationsrisker | TDO väljer lämplig ordning, verifierar delar löpande och planerar samlad granskning av samtliga kriterier och helheten. Varken parallella agenter eller full rollcykel per Story införs automatiskt. |
| A-16 | Implementationen missar ett överenskommet kriterium | Kriteriet skrivs inte om för att få godkänt. Bristen rättas, eller en faktisk mandatkonflikt redovisas. Beslutade kravändringar bevarar ursprung och skäl. |
| A-17 | Story-urvalet uppfyller alla sina kriterier men ger inte det avsedda värdet | Reviewer och PO bedömer även incrementets överenskomna bidrag till Epicen. Ett för tunt urval räknas inte som tillräcklig leverans. |
| A-18 | En teknisk osäkerhet kan lösas med en liten kontroll inom mandatet | AIM genomför den avgränsade kontrollen, använder resultatet och fortsätter utan rutinmässig tillståndsfråga eller ny experimentkampanj. |
| A-19 | En väsentlig visuell eller funktionell kravbrist upptäcks inom mandatet | AIM rättar bristen självständigt och verifierar berörda delar igen; oförändrad giltig evidens återanvänds. |
| A-20 | En session avbryts eller leveransen inväntar acceptans | Åtagande, krav och evidens bevaras. Återupptagning kräver ingen ny rutinmässig mandatfråga. Teknisk verifiering förväxlas inte med användaracceptans. |
| A-21 | Avgörande upplevelsekvalitet saknar tillräcklig evidens | Egenskapen redovisas som overifierad. AIM påstår inte att exempelvis rörelsekänsla har bevisats genom ett kodtest eller en stillbild. |

## 9. Avgränsning för implementation och utvärdering

Kravens målbild är färdigställd. Följande gränser gäller för en eventuell implementation:

- Befintligt stöd för Stories från flera Epics ska bevaras. TDO får använda det inom mandatet när urvalet bidrar till ett tydligt gemensamt leveransmål; en leverans får inte bli en samling orelaterade uppdrag. Varje Story behåller sin primära Epic och relevanta produktprioritet. Stödet får inte i sig utöka godkänd omfattning.
- Automatisk komplexitetsstyrning av kostnadsprofil eller produktprioritet ingår inte. En sådan framtida förändring behöver ett separat motiverat beslut.
- TDO väljer proportionerliga tekniska kontroller av uttryckliga mandatgränser inom implementationsuppdraget. Kontroller ska om möjligt förhindra en otillåten utökning innan den genomförs. Begränsningar i kontrollen ska redovisas; enbart en instruktion är inte en teknisk spärr.
- Acceptansfallen ska användas i relevant dokument-, kod- och beteendeverifiering. De innebär inte ett separat appbygge per fall. Antal produktbyggen, modell, resursram och mätmetod för en produktjämförelse ska följa det då uttryckligen beslutade utvärderingsuppdraget. Ingen ny testkampanj är beställd här.

Vid implementation ska befintliga kontrakt, roller, mallar och berörda adapterinstruktioner uppdateras konsekvent. Ett parallellt regelsystem får inte lämnas kvar med motstridiga ägarskap. Befintliga projekt, identifierare, beslut och historisk evidens ska bevaras; migrering får inte ske underförstått.

Kravunderlaget ska omsättas i koncentrerade arbetsinstruktioner och relevanta kontroller. Hela dokumentet ska inte rutinmässigt laddas av varje agent eller omvandlas till nya formulär. Detaljerade motiv och exempel kan ligga kvar här som referens.

## 10. Relaterat underlag

- [RnD:s granskning 2026-10-15](/Users/jonaseriksson/Documents/RnDAIM/research/2026-10-15.json): fynd R-20261015-001–004 har arbetats in som skydd för krav, konkret incrementvärde, handlingsbart kvalitetsarbete och lättviktig tillämpning. Det kompletterande förtydligandet om genomförandeordning finns i ANS-04. Granskningen är en dokumentanalys, inte verifierad kvalitetsvinst. Kraven här är självständigt läsbara utan den externa filen.
- [Tidigare krav på avsikt, kompetens och produktkvalitet](aim-product-quality-requirements.md): bevarat kravunderlag från det underkända försöket, inte bevis för förbättring. Detta dokument preciserar de nya kraven och det önskade ägarskapet.
- [Kvalitetskriterier och mätmetod](moonkeeper-greenhouse-quality-measurement.md): tidigare produkt- och tekniska bedömningsdimensioner.
- [Tidigare avgränsat testuppdrag](moonkeeper-greenhouse-evaluation-protocol.md): historiskt utvärderingsunderlag, ingen ny körorder.
- [Nuvarande Story-kontrakt](../workflow/user-stories.md): innehåller det befintliga ägarskap som måste ändras om förslaget genomförs.
- [Nuvarande övergripande kontrakt och krav på mottagarens sammanhang](../workflow/agile-iteration-method.md#audience-context-integrity): copykraven ovan kompletterar detta med krav på informationsvärde och relevans.
