# Krav: Från användarens avsikt till verifierad produktkvalitet

Med rätt kompetens och kontinuitet mellan increment.

- Datum: 2026-10-13.
- Status: Försöket är underkänt av användaren. Experimentets beteendeändringar är återställda och sparade separat; baslinje och mätdata är arkiverade. Ingen kvalitetsvinst är fastställd. Kravunderlaget bevaras för senare beslut.
- Dokumentroll: Planeringsunderlag, inte ett nytt kanoniskt beteendekontrakt eller en ändring av gällande AIM-regler. Vid implementation ska berörda befintliga kontrakt uppdateras.
- Underlag: Det granskade förbättringskravet, kompletterat med olika mognadsgrad på indata och ett baslinjeupplägg inför utvärdering. Ett konkret testförslag och en bedömningsbilaga finns länkade nedan. Aktiv utvärdering följer användarens fem steg med ett baslinjespel och en ny kandidatkörning.
- Konkret testförslag: [Månvaktens växthus — utvärderingsprotokoll](moonkeeper-greenhouse-evaluation-protocol.md). Protokollet är avgränsat till samma öppna uppdrag före och efter AIM-ändringen enligt användarens korrigering.
- Kvalitetskriterier och mätmetod: [Månvaktens växthus — bedömningsbilaga](moonkeeper-greenhouse-quality-measurement.md), med elva dimensioner, konkreta skalankare, kodläs- och underhållsprov, browserkontroller, prestandamätning, säkerhetskontroller och KPI-definitioner.

## Problem

AIM kan följa sin leveransprocess och ändå skapa en produkt som missar användarens avsikt, har ett svagt visuellt uttryck eller ger en otillfredsställande användarupplevelse. Genomförda processteg och godkända tekniska tester är inte tillräckliga bevis för en bra slutprodukt.

I klonpusselsförsöket undersökte AIM alternativa klonmekaniker, men använde ett rutnät uppifrån utan att först klarlägga hur spelaren skulle uppleva och röra sig genom världen. Experimentet gav underlag om mekaniken, men besvarade inte hela produktfrågan. Den tekniska verifieringen styrkte heller inte presentationen eller den faktiska spelarupplevelsen.

Försöket visar brister som behöver hanteras. Det fastställer inte att en viss modell, User Stories eller avsaknaden av en viss skill ensam orsakade resultatet.

AIM har redan regler om avsikt, skillanvändning, verifiering och kunskapsåteranvändning. Förbättringen måste därför säkerställa att rätt beteende faktiskt sker, utan att lägga till överlappande instruktioner och administration.

## Önskat utfall

AIM ska leverera produkter som motsvarar användarens avsikt och håller hög kvalitet i funktion, användbarhet, visuellt uttryck och tekniskt utförande, utifrån vad som är relevant för uppdraget.

AIM ska:

- upptäcka betydelsefulla öppna produktval innan de låses genom implementation,
- använda relevant kompetens och fungerande verktyg,
- pröva och förbättra den faktiska produkten,
- återanvända giltig kunskap mellan increment och agentsessioner,
- minska onödiga omtag, upprepade frågor och processarbete.

Produktkvalitet har företräde framför processbesparingar. Kortare genomförandetid får inte motivera en känd väsentlig kvalitetsförsämring. Extra processtid ska kunna motiveras genom bättre beslut, minskad risk eller ett bättre verifierat resultat.

## User story

Som användare vill jag att AIM förstår vad jag försöker åstadkomma, använder rätt kompetens och förbättrar resultatet tills det uppfyller överenskommen kvalitet, så att jag får en genomarbetad produkt utan att behöva välja skills, detaljstyra arbetet eller upprepa redan klarlagd information.

## Underlagets mognadsgrad

Användarens avsikt kan uttryckas som en kort idé, ett detaljerat krav, en specifikation eller en kombination. AIM ska anpassa förarbetet efter vilka relevanta frågor som redan är besvarade.

Ett genomarbetat underlag ska kunna leda direkt till leveransplanering och genomförande inom gällande mandat. AIM ska endast komplettera betydelsefulla luckor eller reda ut motsägelser och får inte kräva att användaren återberättar underlaget i ett särskilt format.

Detaljrikedom är inte i sig bevis för att underlaget är komplett eller genomförbart. AIM ska fortfarande kontrollera relevanta motsägelser, beroenden och antaganden, men inte öppna redan fattade beslut utan sakligt skäl.

Mer moget underlag ska normalt minska behovet av discovery. Kraven på slutproduktens kvalitet och relevant verifiering kvarstår.

## Beteendekrav

### 1. Återanvänd relevant underlag och kontrollera vad som saknas

När arbete startar eller återupptas ska AIM läsa det aktuella uppdraget, relevanta produktbeslut, berörd profilkunskap och kvarvarande öppna frågor.

Kontrollen ska avgöra:

- vad användaren vill uppnå,
- vilka beslut som fortfarande gäller,
- vilka osäkerheter som påverkar nästa arbete,
- vilken kompetens och vilka verktyg arbetet behöver,
- vilken tidigare evidens som fortfarande kan användas.

Kontrollen ska vara avgränsad till det aktuella arbetet och dess betydelse för produktens helhet.

En saknad profil är inte i sig ett skäl för onboarding eller ny intent discovery. Ett tydligt uppdrag i ett tomt projekt ska kunna påbörjas direkt. Föråldrade tekniska fakta ska kunna uppdateras utan att redan klarlagda produktbeslut öppnas igen.

### 2. Upptäck betydelsefulla produktval innan fördjupning

Vid öppna uppdrag ska AIM göra en kort genomgång av de val som kan förändra produktens grundläggande upplevelse, användning eller omfattning.

Genomgången ska även fånga betydelsefulla val som användaren inte uttryckligen har nämnt. AIM får inte begränsa sin förståelse till den mest uppenbara tekniska frågan.

För ett spel kan detta exempelvis gälla perspektiv, rörelse, tidsmodell, kärnmekanik och önskad känsla. För andra produkter ska motsvarande relevanta dimensioner identifieras.

Genomgången ska först göras genom egen analys och befintligt underlag. Den ska inte automatiskt bli ett frågeformulär.

AIM ska skilja mellan sådant som måste klarläggas nu, sådant som kan undersökas genom ett experiment och sådant som kan vänta.

### 3. Fråga om resultatet när användarens svar behövs

AIM ska ställa en riktad fråga när olika rimliga tolkningar skulle ge väsentligt olika resultat och frågan inte redan är besvarad eller delegerad.

Frågorna ska:

- handla om upplevelse, användning, målgrupp, kvalitet eller begränsningar,
- vara få och konkreta,
- beskriva alternativ genom deras konsekvenser,
- innehålla en motiverad rekommendation när underlaget räcker,
- respektera beroenden mellan beslut.

AIM ska själv undersöka fakta som går att kontrollera och själv välja relevanta skills. Användaren ska inte behöva känna till skillnamn eller styra agenternas interna arbetsfördelning.

Delegerade tekniska och visuella val ska göras inom mandatet. Frågor som behövs senare ska inte stoppa oberoende arbete nu.

### 4. Bestäm hur produktkvaliteten ska bedömas

Före större implementation ska AIM konkretisera vilka kvaliteter som avgör om resultatet lyckas.

Bedömningen ska vara anpassad till uppdraget och kan omfatta:

- funktionell och domänmässig korrekthet,
- begriplighet och sammanhängande användarflöden,
- visuellt uttryck och konsekvens,
- interaktionskvalitet eller spelkänsla,
- tillgänglighet och relevanta användningsmiljöer,
- funktionell robusthet,
- kodens läsbarhet och begriplighet för både människa och AI,
- tydliga komponentansvar, modularitet och verifierbar underhållbarhet,
- laddningstid, körprestanda och resursbruk,
- säkerhet utifrån faktiska indata, beroenden och exponerade gränser.

AIM ska använda befintliga designregler och relevanta referenser när sådana finns. Saknade kvalitetsmål ska kompletteras med konkreta förslag. Agentens föreslagna mål ska skiljas från användarens uttryckliga krav.

Kvalitetskriterierna ska innehålla observerbara kännetecken och viktiga exempel på misslyckanden. Ord som ”snygg”, ”intuitiv” och ”professionell” räcker inte ensamma.

Om en avgörande kvalitet kräver användar- eller spelartest ska det framgå. Agentens egen bedömning får inte presenteras som genomförd användarvalidering.

### 5. Matcha förmågor, skills och verktyg till arbetet

AIM ska identifiera vilka förmågor arbetet kräver, exempelvis produktdesign, speldesign, visuell design, domänkunskap, implementation eller verifiering.

För varje väsentligt behov ska AIM välja lämpligt stöd och säkerställa att det går att använda i den utförande agentens miljö.

Relevant skillanvändning innebär att:

- instruktionerna har identifierats och lästs,
- de är tillämpliga på uppgiften,
- den utförande agenten har tillgång till dem,
- de används i konkreta beslut, arbetsmoment eller kontroller.

Ett skillnamn, en installerad fil eller en expertetikett är inte bevis för tillräcklig kompetens.

AIM ska välja ett begränsat, relevant stöd. Det ska inte ladda alla skills, skapa en skill per increment eller skapa en separat agent för varje kompetensområde.

Specialistskills ska tillämpas inom användarens mandat och AIM:s ansvarsfördelning. Motstridiga arbetsflödesinstruktioner ska hanteras uttryckligt.

### 6. Åtgärda väsentliga kompetens- och verktygsluckor

Om ett nödvändigt arbetsmoment saknar tillräcklig täckning ska AIM beskriva konsekvensen och välja en konkret åtgärd.

Åtgärden kan vara att använda en tillgänglig skill, inhämta tillförlitligt referensmaterial, använda specialiststöd, komplettera verktyg eller välja ett verifierbart alternativt arbetssätt. Installation eller skapande av skills kan användas när det är lämpligt och tillåtet.

En saknad särskild skill behöver inte vara blockerande om förmågan kan täckas på annat sätt.

En nyskriven skill får inte räknas som att kunskapsluckan är löst enbart för att instruktioner har skapats. AIM ska kontrollera att åtgärden faktiskt möjliggör det nödvändiga arbetet.

Kvarvarande luckor ska redovisas som begränsningar. De får inte döljas bakom ett påstående om full beredskap.

### 7. Använd prototyper för avgränsade beslut

När en liten prototyp eller ett experiment ger bättre beslutsunderlag än ytterligare diskussion ska AIM genomföra det inom befintligt mandat.

Experimentet ska ha:

- en tydlig osäkerhet att undersöka,
- relevanta observationer som kan stödja eller motbevisa en hypotes,
- ett avgränsat utförande,
- ett tydligt nästa beslut eller arbetssteg.

Detaljnivån ska passa frågan. En förenklad regelmodell kan pröva mekanik, men räcker inte för slutsatser om slutlig visuell kvalitet, rörelsekänsla eller användarens förståelse.

Experimentets förenklingar ska förbli märkta som förenklingar. De får inte automatiskt bli produktbeslut.

När underlaget räcker ska AIM rekommendera en riktning och fortsätta enligt gällande mandat. Om en avgörande osäkerhet återstår ska nästa nödvändiga observation eller användarfråga anges.

### 8. Granska och förbättra den faktiska produkten

AIM ska kontrollera produkten i den miljö där resultatet ska användas, med en omfattning som motsvarar uppdraget och riskerna.

För visuella och interaktiva produkter ska granskningen omfatta renderat resultat och relevanta användarflöden. Kodgranskning, DOM-stubbar och regeltester ersätter inte dessa kontroller.

AIM ska jämföra det demonstrerade resultatet med avsikten och kvalitetskriterierna, även när alla automatiska tester passerar.

Upptäckta väsentliga brister inom överenskommen omfattning ska rättas och berörda delar verifieras på nytt innan leveransen rekommenderas för acceptans. Om rättning kräver ändrad omfattning eller ett nytt användarbeslut ska det göras tydligt.

En utebliven kontroll ska redovisas som overifierad. Godkänd process eller ett högt sammanvägt betyg får inte dölja ett centralt produktfel.

Kodkvalitet ska bedömas genom faktisk förståelse och ändringsförmåga: en efterträdare ska kunna hitta ansvar, följa data och göra en avgränsad ändring med relevant verifiering. Filantal eller komponentantal räcker inte. Prestandapåståenden ska stödjas av mätningar på jämförbara arbetslaster med bibehållen funktion och presentation. Säkerhetsbedömningen ska omfatta tillämpliga positiva och negativa kontroller; ett lokalt spel eller en grön scanner är inte i sig ett säkerhetsbevis.

### 9. Bevara slutmålet genom incrementen

Varje increment ska ha ett tydligt bidrag till den beställda produktens utfall.

AIM ska skilja mellan:

- ett genomfört experiment,
- ett färdigt och verifierat increment,
- en produkt som uppfyller hela uppdraget.

Ett godkänt experiment får inte göra att kvarvarande produktbehov försvinner. AIM ska bevara en tydlig bild av vad som återstår och rekommendera nästa relevanta arbete.

Ett mindre increment får ha begränsad omfattning, men ska uppfylla den kvalitet som gäller för dess avsedda användning. AIM får inte tyst sänka kvalitetsmålet för att få ett processteg färdigt.

Fortsättning och acceptans ska följa befintligt mandat och AIM:s gällande beslutspunkter.

### 10. Bevara kunskap utan att låsa fast antaganden

AIM ska spara bestående kunskap i projektets avsedda produkt-, besluts-, profil- och kompetensytor. Körningsstatus och tillfälliga protokoll ska hållas åtskilda från bestående kunskap.

Betydelsefull information ska skilja mellan:

- användarbeslut,
- agentval inom delegerat mandat,
- antaganden,
- observationer och verifierade fakta,
- öppna frågor.

Källa, tillämpningsområde och skäl för omprövning ska framgå när det behövs för korrekt återanvändning.

Vid nästa increment eller agentsession ska AIM ladda relevant kunskap och återanvända den. Ett sparat antagande får inte uppgraderas till ett användarbeslut. Tidigare verifiering får bara återanvändas när dess relevanta förutsättningar fortfarande gäller.

Förändrad avsikt, ny evidens eller ändrade beroenden ska leda till riktad omprövning. Orelaterade förändringar ska inte orsaka full omkalibrering.

### 11. Integrera förbättringen i befintligt AIM

Förbättringen ska införas i AIM:s befintliga arbetssätt och kanoniska instruktioner.

Inför implementation ska befintlig täckning skiljas från:

- beteenden som saknar instruktion,
- instruktioner som är otydliga eller motstridiga,
- instruktioner som finns men inte får genomslag i utförandet.

Ansvar ska fördelas inom befintliga roller:

- PO bevakar avsikt, produkthelhet och kvalitetskriterier.
- TDO säkerställer genomförande, kompetenstäckning och verifieringsmöjligheter.
- Dev bygger, demonstrerar och förbättrar resultatet.
- Reviewer granskar funktion och faktisk användning mot kraven.

Förbättringen ska inte införa obligatoriska nya godkännandesteg, fullständig omkalibrering eller parallella register för samma information.

## Acceptanskriterier

1. **Tydligt uppdrag utan profil:** AIM kan börja relevant arbete utan en allmän onboarding och kompletterar bara nödvändig information.
2. **Öppet produktval:** AIM upptäcker ett betydelsefullt, outtalat vägval innan det låses genom större implementation och hanterar det genom en riktad fråga, ett experiment eller ett uttryckligt delegerat val.
3. **Dukat bord:** Ett nytt increment med giltiga beslut och relevant kompetenstäckning fortsätter utan upprepade frågor, återskapade skills eller full omkalibrering.
4. **Antagande kontra beslut:** En sparad förenkling från en prototyp återanvänds inte som ett fastställt användarkrav.
5. **Faktisk kompetenstäckning:** Den utförande agenten kan använda valda instruktioner och verktyg. En väsentlig lucka leder till en konkret åtgärd eller en tydligt redovisad begränsning.
6. **Produktkvalitet trots gröna tester:** AIM upptäcker och hanterar ett väsentligt visuellt eller interaktivt problem även när funktionstesterna passerar.
7. **Beslutande experiment:** En prototyp redovisar vad den prövade, vad observationerna stödjer och vilket nästa steg som följer. Slutsatserna överskrider inte experimentets räckvidd.
8. **Sammanhängande leverans:** Efter ett avslutat experiment eller increment finns kvarvarande produktbehov och nästa relevanta steg bevarade.
9. **Riktad förändring:** Ny avsikt eller evidens uppdaterar berörda beslut, skills och kontroller utan att oberoende giltig kunskap kastas bort.
10. **Proportionerligt utförande:** En liten, tydlig ändring leder inte till en full produktutforskning eller en omfattande kompetensinventering.
11. **Kontinuitet mellan sessioner:** En ny agentsession kan fortsätta med rätt avsikt, beslut och relevanta instruktioner utan tillgång till hela den tidigare chatten.
12. **Spårbar bedömning:** AIM kan kort redovisa vilken kunskap som återanvändes, hur specialiststödet användes, vilken produktkvalitet som verifierades och vad som återstår osäkert.
13. **Moget kravunderlag:** Ett detaljerat, sammanhängande krav används direkt som underlag. AIM ställer inte frågor som redan besvarats, kräver ingen omskrivning till en kort intention och bibehåller kvalitetskraven även när discovery kan förkortas. En betydelsefull motsägelse i ett annars detaljerat underlag klarläggs riktat.
14. **Kod och underhåll:** Mänsklig kodläsare och ny AI-session kan följa centrala ansvar utan författarhjälp. En standardiserad ändring verifierar avgränsning, återanvändning och tester som upptäcker relevant regression.
15. **Produktprestanda:** Laddning, interaktionsrespons, bildflyt och resursutveckling mäts på representativa jämförbara arbetslaster. Optimering får inte bestå av borttagen funktion eller sänkt visuell kvalitet.
16. **Säkerhet:** Faktiska angreppsytor identifieras och tillämpliga kontroller verifieras. Kvarvarande kända exploaterbara brister hindrar säkerhetsgodkännande och får inte kompenseras med andra kvalitetsbetyg.

## Utvärdering av förbättringen

Beteendekriterierna ska verifiera att AIM arbetar på avsett sätt. Därutöver ska produktutvärdering undersöka om förändringen faktiskt förbättrar resultatet.

Den aktiva utvärderingen är det enda före/efter-par som anges i testprotokollet. Detaljerat underlag, kontinuitet och andra relevanta användningsfall ska beaktas i instruktionernas granskning. Detta ger inget mandat att starta ytterligare spel, produkttyper eller byggarkörningar. Om ett beteende inte har prövats i faktisk användning ska dess evidenslucka redovisas.

Den beställda jämförelsen omfattar tidigare och förbättrat AIM på samma uppdrag. Ytterligare spår, såsom specialiststöd utan AIM eller Pocock, kräver uttrycklig ny beställning och ingår inte i detta arbete.

Uppgift, modellinställningar, verktyg, information, användarsvar och resurser ska hållas jämförbara. Skillnader och ingrepp under körning ska redovisas.

Bedömningskriterier och gränser för väsentliga försämringar ska fastställas före körning. Bedömningen ska skilja mellan:

- produktkvalitet,
- tid till överenskommen kvalitetsnivå,
- aktiv arbetstid och användarinsats,
- rättningar och omtag,
- metodens egen leveransstatus.

Visuell kvalitet och användarupplevelse ska bedömas uttryckligt. Där det är praktiskt möjligt ska bedömaren inte känna till vilket arbetssätt som producerat resultatet.

Förändringen ska inte betecknas som en bekräftad förbättring enbart för att instruktionerna följs. Det ska finnas observerad nytta och inga upptäckta väsentliga kvalitetsförsämringar i den överenskomna utvärderingen. Otillräckliga resultat ska leda till justering eller ett redovisat osäkert utfall.

Uppfyllda kvalitetskriterier visar att en nivå har nåtts. Påståenden om överlägsenhet kräver jämförande evidens. Enstaka körningar får användas diagnostiskt men räcker inte för generella påståenden om att AIM alltid är bäst.

### Baslinje före metodändringen

Före implementation av AIM-förbättringarna ska testprojektets uppdrag och bedömningsprotokoll fastställas och en referenskörning med den befintliga AIM-versionen genomföras. Bevara den exakta versionen, instruktionerna, miljön, produktresultatet och råa mätvärden så att jämförelsen kan granskas och upprepas.

Baslinjeprodukten ska byggas genom det arbetssätt som utvärderas. Den ska inte handbyggas eller rättas utanför den redovisade körningen av den som utvecklar AIM-förbättringen.

Efter metodändringen ska samma uppdrag köras från en likvärdig ursprungsmiljö i en ny agentsession. Körningen får inte tillgång till baslinjeproduktens lösningskod eller tidigare körningars lösningsanteckningar. Den får samma tillåtna startunderlag och tillgång till samma stödresurser; vilka resurser respektive metod faktiskt väljer att använda registreras.

För fortsatt arbete mellan increment används respektive körnings egen produkt, profil och beslutshistorik. Återupptagning ska prövas i en ny session så att kontinuitet inte förutsätter att den ursprungliga chatten finns kvar.

Protokollet ska ange hur användarfrågor och acceptans hanteras likvärdigt. Svar får inte styra ett spår med extra produktkunskap eller efterhandsförbättrade krav. För öppna uppdrag kan en i förväg definierad svarspolicy användas, utan att ge byggaren svar på frågor som testet avser att den själv ska upptäcka.

Före första mätningen ska följande fastställas:

- testprojektets utfall, omfattning och startunderlag,
- kvalitetsdimensioner, bedömningsskalor och kritiska fel som hindrar godkänt resultat,
- primärt KPI och kompletterande mått, inklusive hur kvalitetsskillnader hålls synliga,
- villkor för en meningsfull förbättring och gränser för kvalitetsregression,
- körbudget, stoppvillkor, antal upprepningar och hantering av variation,
- modell, inställningar, verktyg, skillversioner och miljö,
- likvärdig hantering av frågor, godkännanden, feedback och miljöfel.

Redovisa både produktkvalitet vid en gemensam budget och tid till en gemensam kvalitetsnivå när protokollet medger det. En körning som inte når kvalitetsnivån inom budgeten ska redovisas som sådan, inte räknas som snabbare. Eventuell extra kvalitetsbudget ska vara bestämd och tillgänglig för samtliga jämförelsespår.

Spara även första inlämningen, fel och rättningsarbete. Ett sammanvägt KPI får inte dölja en väsentlig försämring i exempelvis avsiktsträff, visuellt uttryck eller användbarhet. Överhead för AIM-förbättringens utveckling och extern utvärdering redovisas separat från byggarkörningarna.

Om protokollet behöver ändras efter baslinjen ska ändringen versionsmärkas och berörda jämförelser köras om. Efterhandsändrade kriterier får inte användas för att utse en vinnare mot en gammal mätning.

### Fastställd utvärderingsomfattning

Månvaktens växthus byggs en gång med befintligt AIM och en gång med förbättrat AIM, från samma öppna uppdrag i nya sessioner. GPT-6 Luna hög används enligt användarens val. Bedömningsbilagan definierar kvalitetsdimensioner och tekniska mätningar. Inga ytterligare jämförelsespår eller produktvarianter ingår utan ny beställning.

## Avgränsning

Kravet inför ingen obligatorisk mängd skills, agenter, prototyper, frågor eller dokument.

Jämförande benchmarkarbete hör till utvärderingen av AIM-förändringen och ska inte behöva genomföras för varje vanligt produktincrement.

Användaren äger produktbeslut som kräver mänsklig preferens eller auktoritet och kan delegera val. AIM ansvarar för förberedelser, rekommendationer, genomförande, relevant verifiering och förbättring inom mandatet.

Målet är att nästa increment ska börja med bättre förståelse och bättre förutsättningar — och att den fördelen ska märkas i produkten.
