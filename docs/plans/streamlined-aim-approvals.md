# Planförslag: färre avbrott och snabbare Jag godkänner administration i AIM

Datum: 2026-09-29. Uppdaterad: 2026-09-30 efter granskning och förtydligande av chatt-/CLI-flödet.
Status: godkänd och implementerad i repositoryt 2026-09-30, inklusive chatt/CLI och UI, för release 3.2.0. Releasehistorik finns i [CHANGELOG](../../CHANGELOG.md). Jämförande mätning av hela agentkörningar och mänsklig begriplighetsutvärdering återstår; se [implementationsrapporten](streamlined-aim-implementation.md). Texten nedan bevarar planens problemformulering och acceptanskriterier. Gällande kontrakt finns i [samlade beslut](../workflow/streamlined-decisions.md).

## Förslag och önskat resultat

AIM ska samla användarens beslut vid två konkreta tillfällen i ett normalt Strict-flöde: före implementation av ett Inkrement och vid acceptans av leveransen.

Chatt och CLI är primära användningsvägar för detta förslag. Hela flödet ska fungera utan att AIM UI är öppet eller används. UI återger samma beslut, mandat och nästa steg; det tillför presentation, inte en separat arbetsgång.

- Vid starten presenteras Epicens mål och första Inkrementet tillsammans. Ett godkännande omfattar den redovisade riktningen och det konkreta Inkrementet.
- Vid leveransen presenteras resultatet tillsammans med AIM:s rekommendation om nästa steg. När hela Epicen är verifierad kan ett godkännande både acceptera Inkrementet och avsluta Epicen.
- Nödvändig uppdatering av `.aim` utförs samlat av ett deterministiskt verktyg. Agenten ansvarar för bedömningar och underlag; verktyget registrerar besluten och uppdaterar tillståndet.
- Vid varje överlämning eller paus framgår nästa konkreta steg, vad Continue kommer att utföra och när användarens nästa beslut behövs. Informationen ska finnas redan i chatt-/CLI-svaret och kunna hämtas via status.

Målet är färre användaravbrott, mindre aktiv administration och kortare tid till en korrekt avslutad eller fortsatt leverans. Granskning, verifiering, mänsklig beslutanderätt och återupptagning efter avbrott ska bevaras.

## Problem och nuläge

Nuvarande Strict-flöde separerar godkännande av Epicen vid Gate A från godkännande av Inkrementet vid Gate B. Efter Gate E ska AIM bedöma Epicen och föreslå `close`, `continue` eller `split`. Vanliga Strict- och Auto-körningar kräver ett separat beslut om Epicens disposition.

Användarupplevelsen kan därför innehålla flera godkännanden och långa administrativa turer för samma leverans. Något tredje användargodkännande för att verkställa ett redan beslutat avslut finns inte i det granskade avslutskontraktet.

AIM har redan kod för kontrollerat Epic-avslut. Förslaget bygger vidare på den och ändrar när beslut förbereds och hur flera uttryckligen godkända övergångar verkställs tillsammans.

Den publicerade jämförelsen visar 56,47 minuters utveckling för AIM mot 23,88 minuter utan AIM i en specifik kedja. Den sammanställningen fastställer inte hur stor del av skillnaden som orsakas av godkännanden eller `.aim`-administration. Förslaget innehåller därför mätning, inte ett löfte om halverad körtid.

## Föreslaget användarflöde

### 1. Ett samlat förslag före första implementationen

AIM tolkar uppdraget, formulerar Epicen och planerar första Inkrementet innan ett godkännande efterfrågas. Planeringen får ske före godkännandet; implementation kräver rätt beslut eller ett redan giltigt mandat.

Förslaget visar kort:

- Epicens mål, viktiga avgränsningar och avgörande antaganden.
- Vad första Inkrementet levererar och hur det ska verifieras.
- Vad som återstår i Epicen efter leveransen.
- Väsentliga risker och kostsamma eller irreversibla vägval.

Exempel på beslut: **”Godkänn riktningen och första Inkrementet.”**

Epicens fullständiga kriterier ska finnas tillgängliga. De får inte döljas bakom en alltför snäv beskrivning av första Inkrementet. Godkännandet ger inte automatiskt rätt att implementera framtida Inkrement i Strict.

Om en obesvarad fråga väsentligt påverkar målet, omfattningen eller lösningen ställer AIM den konkreta frågan före förslaget. Ett rutinmässigt separat Epic-godkännande ska inte ersätta sådan klargörande dialog. Separat målbeslut kan användas när användaren uttryckligen vill besluta riktningen först eller en tillämplig projektpolicy kräver det.

### 2. Implementation, granskning och verifiering

Dev, Reviewer och TDO behåller sina kvalitetsansvar. Krav på oberoende granskning vid väsentliga ändringar gäller fortsatt enligt befintlig policy.

Godkända kontroller återanvänds så länge relevanta indata och antaganden gäller. Berörda kontroller körs om efter ändringar. Obligatorisk integrationsverifiering och kontroll av hela Epicens mål får inte tas bort för att spara administrationstid.

### 3. Rekommendationen om Epicen blir klar före acceptansfrågan

Efter verifieringen bedömer PO hela Epicen och förbereder exakt en rekommendation:

| Rekommendation | Vad användaren får se | Vad acceptansen innebär |
| --- | --- | --- |
| `close` | Inkrementets resultat och bevis för att hela Epicens mål är uppfyllda | Acceptera Inkrementet och avsluta Epicen i samma svar |
| `continue` | Inkrementets resultat, återstående mål och föreslagen inriktning för nästa Inkrement | Acceptera Inkrementet och låta AIM planera nästa Inkrement |
| `split` | Inkrementets resultat och tydlig åtskillnad mellan ursprungliga krav och nytillkommen omfattning | Acceptera leveransen samt den uttryckligen presenterade hanteringen av ny omfattning |

`split` får inte användas för att flytta bort ouppfyllda ursprungliga krav. Ett beslut att avskilja ny omfattning innebär inte automatiskt godkännande att implementera den eller avsluta en ofärdig Epic.

Rekommendationen före användarens svar är ett förslag, inte registrerad acceptans. När användaren accepterar det oförändrade förslaget behöver AIM inte göra om hela analysen.

Användaren ska kunna acceptera Inkrementet men uttryckligen avstå från att stänga Epicen. AIM registrerar då bara den givna acceptansen och behåller Epicen öppen. Ett generiskt godkännande får omfatta båda besluten endast när det aktuella förslaget otvetydigt angav båda.

### 4. Fortsatt arbete efter ett accepterat Inkrement

AIM behåller ansvaret för att upptäcka återstående arbete. Vid `continue` tar AIM efter acceptansen fram nästa konkreta Inkrement utan att kräva ett extra ”fortsätt” för själva planeringen.

I Strict presenteras nästa Inkrement för godkännande före implementation. Epicen behöver inte godkännas på nytt när riktningen är oförändrad. Om användaren begär en ändring av leveransen eller målet uppdaterar AIM berörda underlag och omprövar rekommendationen innan den verkställs.

Rekommendationen `continue` är ett förslag om Epicens fortsättning. Kommandot `/aim continue` återupptar däremot arbetet från aktuellt tillstånd och mandat. Kommandot är inte i sig ett godkännande av en plan, en leverans eller ett Epic-avslut. Vid en väntande beslutspunkt visar det vilket beslut som behövs.

### 5. Körlägen och befintliga mandat

Två användarbeslut beskriver normalfallet för en Epic med ett Inkrement i Strict. En Epic med flera Inkrement har fortsatt planering och acceptans för varje leverans.

Auto behåller sin befintliga rätt att fortsätta inom godkänd riktning. Förslaget ska inte införa fler pauser där. Den slutliga användaracceptans som krävs i vanlig Auto kan omfatta både sista Inkrementet och Epic-avslutet.

Portfolio Auto behåller sitt avgränsade mandat och sina kontroller av återstående kandidater. Ett samlat avslut får aldrig hoppa över arbete som mandatet fortfarande kräver. Förslaget ger inga nya rättigheter att driftsätta, publicera eller utföra andra separat reglerade åtgärder.

### 6. Continue ska vara begripligt före användning

Vid varje överlämning eller paus ska AIM i en eller två meningar ange följande innebörd. Punkterna är inte tre obligatoriska rubriker:

- **Nästa steg:** en konkret handling med dess omfattning, exempelvis planera exportfunktionen eller återuppta dess godkända implementation.
- **Vad Continue gör:** om AIM planerar, implementerar, verifierar, slutför registrering eller presenterar ett beslut som ännu saknas.
- **Nästa beslutspunkt:** när användaren behöver ta ställning igen, eller vilket villkor som kräver eskalering inom ett befintligt Auto-mandat.

Användaren ska kunna förstå detta utan kunskap om interna roller, gates eller tillståndsnamn. Följande exempel förutsätter att det beskrivna tillståndet och mandatet är verifierade:

| Aktuellt läge | Besked i chatt och CLI |
| --- | --- |
| Accepterat Inkrement och beslutad fortsättning i Strict, men planeringen har avbrutits | **Nästa steg: planera exportfunktionen.** Kör `/aim continue` så tar jag fram nästa Inkrement. Du får godkänna planen innan implementationen börjar. |
| Godkänd implementation har avbrutits | **Nästa steg: återuppta exportfunktionen.** Kör `/aim continue` så kontrollerar jag sparat läge och fortsätter implementation, granskning och verifiering inom godkänd omfattning. Nästa ordinarie beslut är din acceptans av leveransen. |
| Granskningen har hittat fel inom godkänd omfattning och arbetet har pausats | **Nästa steg: rätta granskningsfynden.** Kör `/aim continue` så rättar jag felen och upprepar berörda kontroller innan leveransen presenteras för acceptans. |
| Strict väntar på godkännande av nästa plan | **Nästa steg: ta ställning till planen.** `/aim continue` visar det aktuella förslaget; implementation börjar först när du godkänt det. |
| Avslutsunderlaget är klart men användarens acceptans saknas | **Nästa steg: ta ställning till leveransen och avslutet.** `/aim continue` visar förslaget och dess underlag. Det accepterar eller avslutar inget åt dig. |
| Auto har kvarvarande arbete inom giltigt mandat | **Nästa steg: fortsätta med exportfunktionen.** `/aim continue` återupptar planering och implementation inom mandatet. AIM återkommer vid en mandatgräns eller den slutliga acceptans som krävs för körningen. |
| Sparat läge är motsägelsefullt eller saknar nödvändigt mandat | **Nästa steg är blockerat:** ange den konkreta bristen och minsta åtgärd som löser den. Continue får inte gissa ett mandat eller börja ändra produktkod. |

Exemplen beskriver verkliga överlämningar och avbrott. AIM ska inte skapa nya pauser för att kunna visa ett Continue-besked. Efter ett accepterat `continue` fortsätter planeringen direkt när sessionen kan fortsätta.

`/aim status` och relevant hjälp ska ge samma besked utan att flytta arbetet framåt. Ett direkt `/aim continue` i en ny session ska läsa aktuellt tillstånd, kort ange vad som händer och sedan utföra redan auktoriserat arbete utan en extra bekräftelsefråga. Saknas ett nödvändigt beslut presenteras det konkreta förslaget.

Beskedet ska grundas på samma tillstånd och mandat som styr utförandet. Om de ändrats sedan förra beskedet förklarar AIM den betydelsefulla skillnaden före fortsatt handling. En sammanfattning eller UI-etikett får inte bli en egen källa till mandat. Testerna ska kontrollera att utlovat och utfört steg stämmer överens.

CLI betyder här AIM via en terminalbaserad kodagent och dess stödda kommandoväg. Förslaget kräver ingen ny fristående CLI-produkt. Där slash-kommandon saknas ska den stödda motsvarigheten eller vanlig text ge samma beteende.

UI kan senare visa exempelvis ”Fortsätt: planera nästa Inkrement” eller ”Återuppta implementation”. Underlaget och betydelsen ska vara desamma som i chatt och CLI.

## Samlad administration

### Ett gemensamt beslutsunderlag från första Inkrementet

Agenten förbereder ett kompakt, versionshanterat underlag med förslagets identitet och version, Epic och Inkrement, exakt vilka beslut som föreslås, aktuellt tillstånd, verifieringsreferenser och giltighetsvillkor. Användarens faktiska godkännande och dess källa läggs till först när det finns. Det ska framgå om svaret godkände hela förslaget eller bara vissa beslut.

Representationen införs redan i första Inkrementet och delas av chatt, CLI och senare UI. Äldre åtgärder behåller sin tidigare innebörd. Naturligt språk behöver inte innehålla ett tekniskt förslags-ID, men agenten måste kunna knyta svaret entydigt till rätt aktuellt förslag; verklig tvetydighet kräver en avgränsad fråga.

### Avslutsberedskap före acceptans, behörighet vid verkställighet

Nuvarande avslutsflöde kräver redan accepterat Inkrement och giltig avslutsauktoritet. Det kan därför inte oförändrat användas för hela kontrollen före den nya samlade acceptansfrågan.

Inför en skrivskyddad kontroll av teknisk avslutsberedskap som återanvänder de befintliga kvalitets- och evidenskontrollerna. Den kan visa att leveransen är redo att erbjudas för acceptans, men registrerar ingen acceptans och ger ingen rätt att avsluta. Ingen tillfällig acceptans eller påhittad beslutskälla får skapas för att få kontrollen att passera.

Vid verkställighet kontrolleras det faktiska användarbeslutet eller befintliga mandatet tillsammans med tillståndets och bevisens fortsatta giltighet. Återanvänd samma kontrollfunktioner så att förhandsbedömning och verkställighet inte utvecklar olika kvalitetsregler.

### Samlad registrering och återhämtning

Ett verktyg validerar och verkställer underlaget i en sammanhängande operation. Internt kan två logiska beslut fortfarande registreras med samma användarsvar som källa. Två spårbara beslut ska inte kräva två användarsvar eller två nya modellresonemang.

Krav på verktyget:

- Kontrollera rätt Epic, Inkrement, förslagets version och aktuellt tillstånd.
- Bevara befintliga kontroller av acceptanskriterier, bevisens giltighet, behörighet och säkra sökvägar.
- Återanvänd verifieringsresultat genom referenser i stället för nya snarlika rapporter.
- Kontrollera färskhet direkt före skrivning. Filhashar visar ändrade bytes, inte att ett sakpåstående är sant; relevanta miljö- och indataberoenden måste också beaktas.
- Hantera upprepade anrop utan dubbla beslut. Ändrat innehåll med samma operationsidentitet ska avvisas.
- Hantera konkurrerande operationer mot samma tillstånd. Godkännande i UI samtidigt med en ändringsbegäran i chatten får inte leda till tyst överskrivning eller att ett inaktuellt förslag verkställs. Välj en avgränsad mekanism för serialisering eller villkorad skrivning; återhämtning måste respektera senare giltiga beslut.
- Kunna återhämta sig efter avbrott mellan filskrivningar. En filersättning är inte automatiskt en transaktion över flera filer; välj och testa en minimal mekanism för återställning eller deterministisk återupptagning.
- Hålla runtime, Backlog och UI-kopplingar konsekventa där de berörs. Ofullständig bokföring får inte visas som ett helt genomfört avslut.
- Ge ett kort kvitto. Om ett gammalt godkännande blivit inaktuellt ska AIM förklara ändringen och bara begära ett nytt beslut när det behövs.

Förslaget behåller nödvändiga statusövergångar för UI och återupptagning. Det inför inte en ny databas eller ett generellt händelsesystem. Spårbarhet ska bevaras med minsta tillräckliga artefakter.

### När krävs ett nytt beslut?

Skilj ändrad teknisk färskhet från ändrad innebörd av det användaren godkände:

| Förändring eller fel | Hantering |
| --- | --- |
| Samma godkända operation avbröts under bokföringen | Återuppta eller återställ säkert och försök igen inom samma mandat; begär inte samma godkännande på nytt. |
| Administrativa metadata eller en UI-koppling behöver repareras | Kontrollera att leverans, omfattning och beslutets innebörd är oförändrade. Förnya tekniskt underlag vid behov, utan att automatiskt kräva nytt användarbeslut. |
| Relevant bevisfil, produktkod, miljö eller indata har ändrats | Stoppa användningen av det gamla tekniska underlaget och verifiera berörda delar på nytt. Bedöm därefter om det tidigare beslutet fortfarande täcker exakt den aktuella leveransen. |
| Mål, omfattning, leverans, väsentlig risk eller föreslagen disposition har ändrats så att beslutet inte längre täcker dem | Presentera skillnaden och begär ett nytt beslut för den berörda delen. |

Ett gammalt digest får aldrig godtas mot ändrade bytes. Bevarat användarmandat kan däremot ligga till grund för ett nytt tekniskt underlag när innebörden är oförändrad. Registrera skälet kort och knyt eventuell förnyelse till det ursprungliga beslutet. Ett fel som rättas inom en redan godkänd implementationsplan kan omfattas av den planen. En beteendeändring i en redan accepterad leverans kräver däremot ett nytt avgränsat förslag; den får inte döljas som administrativ förnyelse. Giltig acceptans av en del får inte försvinna för att en annan del, exempelvis Epic-avslutet, behöver nytt underlag eller beslut.

## Kvalitet: förväntad effekt och huvudsakliga risker

Bedömningen är att teknisk kvalitet kan bevaras och beslutsunderlaget förbättras, men detta är ännu en hypotes.

| Risk | Föreslagen hantering |
| --- | --- |
| Första Inkrementet skymmer Epicens fullständiga mål | Visa mål, avgränsningar och återstående arbete i samma förslag |
| Ett godkänt Inkrement misstolkas som en färdig Epic | Kräv fortsatt verifiering av varje Epic-kriterium före erbjudande om avslut |
| Ett generiskt eller gammalt `approve` får större innebörd | Bind beslut till ett tydligt presenterat, aktuellt förslag; bevara äldre beslutssemantik |
| Feedback gör en förberedd rekommendation inaktuell | Ompröva berörda kriterier och verifieringar före verkställighet |
| Avbrott lämnar motsägelsefulla filer | Testa fel vid varje skrivgräns och säker återupptagning |
| Chatt och UI verkställer konkurrerande beslut | Testa samtidiga operationer och säkerställ att äldre skrivningar eller återställningar inte skriver över senare giltiga beslut |
| Continue utför något annat än användaren förväntar sig | Härled besked och utförande från samma aktuella tillstånd och mandat; verifiera överensstämmelsen i chatt, CLI och UI |
| Färskhetskontroller leder till upprepade godkännanden av samma sak | Skilj teknisk omverifiering och återförsök från ändringar som kräver ett nytt användarbeslut |
| Tiden flyttas bara från efter till före godkännandet | Mät hela arbetskedjan och aktiv administration separat |

Möjliga positiva effekter är färre rutinmässiga godkännanden, mer konkreta beslut och färre inkonsekvenser från manuell administration. Dessa effekter ska utvärderas, inte marknadsföras som redan bevisade.

## Genomförande i två användbara Inkrement

### Inkrement 1: hela det förenklade flödet i chatt och CLI

Leverera samlad start, samlad acceptans, korrekt fortsatt planering och tydliga Continue-/statusbesked för en enskild Epic genom den portabla AIM-skillen och stödda terminalbaserade adaptrar. Bygg på befintliga tillstånd, kontrollfunktioner och filformat; inför inget generellt arbetsflödesramverk. Inkrementet omfattar gemensam versionshanterad beslutsrepresentation, skrivskyddad avslutsberedskap, verktyg för samlade uppdateringar, säkra felvägar, berörda adapterkontrakt, dokumentation och tester. Chatt och CLI ska vara kompletta användningsvägar i denna leverans.

Demonstrera både en Epic som avslutas efter en leverans och en Epic som kräver ytterligare ett Inkrement. En gammal körning ska kunna fortsätta utan att dess tidigare godkännanden omtolkas. AIM UI måste fortsatt visa sann status och får inte erbjuda en åtgärd med fel innebörd; äldre knappflöden kan tills vidare hänvisa till chatten för den nya samlade åtgärden.

### Inkrement 2: samma beslut direkt i AIM UI

Leverera tydliga knappar och samma beslutsunderlag i AIM UI, inklusive fortsatt Epic och begärd ändring. Använd beslutsrepresentationen och Continue-betydelsen från första Inkrementet. Komplettera UI-kopplingar och berörda paket så att UI, chatt och CLI ger samma besked och utför samma övergång för samma tillstånd och mandat.

Äldre åtgärdsmeddelanden som bara godkänner Gate E får fortsatt bara acceptera Inkrementet. Pågående och avslutade äldre körningar ska vara läsbara utan automatisk omskrivning av historik. Samma förslag ska kunna visas i en kanal och beslutas i en annan utan dubbla beslut eller utökat mandat.

Mätning ingår i båda Inkrementen. Resultatet från det första används för att bedöma vilka administrativa delar som fortfarande behöver förenklas.

### Möjlig senare förenkling: acceptera föregående och godkänn nästa

För en Epic med flera Inkrement kan AIM senare förbereda nästa konkreta plan före acceptansfrågan och erbjuda ett uttryckligt samlat beslut: ”Acceptera leveransen och godkänn nästa Inkrement.” Det kräver samma fullständiga planunderlag som ett separat Strict-godkännande och möjlighet att acceptera endast föregående leverans. Feedback på leveransen kan göra nästa plan inaktuell.

Detta ingår inte i de två Inkrementens acceptanskriterier. Utvärdera behovet efter första mätningen så att förslaget inte växer innan grundflödet fungerar. Den nu föreslagna ordningen med acceptans följd av nästa plan kvarstår som normalfall.

## Berörda områden

Följande är en preliminär ändringskarta. Exakta filer och ansvar fastställs inför respektive Inkrement.

| Område | Kända berörda källor |
| --- | --- |
| Metod, beslut och kvalitet | `docs/workflow/agile-iteration-method.md`, `adapter-command-contract.md`, `epic-closure-truth-audit.md`, `role-skill-po.md`, `role-skill-tdo.md` |
| Övergångar och validering | `scripts/aim_runtime_contract.py`, `scripts/aim_actions.py`, `scripts/aim_validator/runtime_state.py`, `schemas/aim-runtime-state.schema.json` |
| Continue, status och nästa beslut | Portabla skillens och adaptrarnas kanoniska instruktioner, `adapter-command-contract.md`, berörda läsare av runtime och mandat; gemensamt underlag för chatt, CLI och UI |
| Portfolio och UI | `scripts/aim_portfolio_run.py`, `scripts/aim_portfolio.py`, `scripts/aim_ui.py`, `aim-ui/app.js`, berörda scheman |
| Paketering och användarguider | Kanoniska adapterkällor under `adapters/`, generering via `scripts/build_public_skill.py`, berörda produkt- och introduktionsguider |
| Regressioner | `tests/test_aim_runtime_contract.py`, `tests/test_aim_actions.py`, `tests/test_aim_portfolio_run.py`, `tests/test_aim_ui.py`, adapter-, schema- och pakettester |

Genererade skillfiler ska byggas från sina källor. Denna plan inför ingen aktiv Epic och ändrar inte körläge, Backlog eller `.aim`.

## Acceptanskriterier

1. En tydlig Epic med ett Inkrement kan i Strict genomföras med ett godkännande före implementation och ett samlat godkännande efter verifierad leverans.
2. Första förslaget visar Epicens mål, Inkrementets omfattning och återstående arbete. Ingen separat rutinmässig Gate A-fråga behövs.
3. AIM presenterar en underbyggd rekommendation om `close`, `continue` eller `split` tillsammans med leveransen.
4. Efter accepterat `continue` planerar AIM nästa Inkrement utan extra startuppmaning. Strict kräver godkännande av nästa plan före implementation.
5. Ett saknat, misslyckat eller motsägelsefullt Epic-kriterium förhindrar avslut. Inaktuella bevis kräver berörd omverifiering; ändrad innebörd som inte täcks av mandatet kräver nytt beslut. Administrativa återförsök utlöser inte automatiskt ny användaracceptans.
6. Användaren kan acceptera enbart Inkrementet. Historiska godkännanden och äldre UI-åtgärder får ingen utökad innebörd.
7. Upprepade anrop, samtidiga beslut, avbrott och återupptagning skapar varken dubbla beslut, tyst överskrivning, förlorad acceptans eller felaktigt färdig status.
8. Auto och Portfolio Auto behåller sina mandatgränser och får inga nya rutinmässiga pauser.
9. Tekniska kvalitetskontroller och nödvändig granskning finns kvar. Vinsten ska kunna härledas till färre avbrott och mindre administration.
10. En jämförbar mätning redovisar total tid, aktiv administration, användarväntan och kvalitetsutfall för gammalt och nytt flöde.
11. Hela flödet kan genomföras i chatt respektive stödd terminalbaserad kodagent utan AIM UI. Vid varje överlämning eller paus framgår nästa konkreta steg, vad Continue gör och nästa nödvändiga användarbeslut. Status visar samma innebörd utan att ändra runtime.
12. Direkt Continue i en ny session återläser aktuellt tillstånd, förklarar nästa handling och utför auktoriserat arbete utan en extra rutinfråga. Det ger inget nytt mandat och passerar inte en väntande acceptans. Ändrad förutsättning eller blockering förklaras konkret.
13. Besked och faktiskt utfört steg överensstämmer för samma tillstånd och mandat i chatt, CLI och, när andra Inkrementet levererats, UI. Ett gammalt besked får inte styra utförandet efter en relevant tillståndsändring.
14. Avslutsberedskap kan kontrolleras före användaracceptans utan skrivningar eller fabricerad auktoritet. Verkställighet återanvänder samma kvalitetskontroller och kräver verkligt, giltigt mandat.
15. Första Inkrementet innehåller gemensam versionshanterad beslutsrepresentation. Ett partiellt godkännande registrerar endast de angivna besluten och bevaras vid senare återförsök.

## Verifiering och mätning

Testa genom chatt och stödd CLI-väg utan UI samt, när Inkrement 2 är klart, genom UI. Använd samma förväntade mandat och övergångar för alla kanaler:

- En tydlig Epic med ett Inkrement och komplett verifiering.
- En Epic med flera Inkrement och kvarvarande kriterier efter första leveransen.
- Begärd ändring, ändrat mål och acceptans utan Epic-avslut.
- Saknade bevis, ändrade filer efter förslaget, fel Epic och upprepat godkännande.
- Avbrott under varje del av den samlade uppdateringen samt återupptagning i en ny session.
- Samtidigt godkännande och ändringsbegäran mot samma tillstånd, två samtidiga godkännanden samt återhämtning efter att en annan operation redan gjort ett giltigt framsteg. Styr ordningen i testerna så att de faktiskt utövar konkurrerande skrivningar.
- Skrivskyddad avslutsberedskap före acceptans, utebliven verklig auktoritet vid verkställighet och enbart partiell acceptans av ett samlat förslag.
- Administrativt skrivfel eller ändrad UI-koppling med oförändrad leverans: återförsök utan ny acceptans. Jämför med ändrad omfattning eller leverans som faktiskt kräver nytt beslut.
- Äldre Gate A-, Gate B- och Gate E-lägen, stängd historik samt en Portfolio med återstående kandidater.
- Continue vid väntande plangodkännande, avbruten implementation, granskningsfynd, accepterad fortsättning, väntande avslutsacceptans, Auto-mandat och blockerande tillstånd. Kontrollera både beskedet, faktiskt arbete och frånvaro av obehöriga övergångar.
- Status och hjälp utan tillståndsändring, direkt Continue i ny session, kanalskifte och ett ändrat tillstånd mellan senaste besked och Continue. Kör även hela normalfallet utan att starta UI.

Mät först själva arbetsflödet mot frysta, giltiga leveransunderlag för att isolera administrationskostnaden. Använd därefter nya jämförbara utvecklingsuppdrag med samma modell, verktyg, resurser och kvalitetskrav för att kontrollera att vinsten även finns i verklig leverans. Upprepa jämförelser och redovisa variationen.

Skilj på:

- Antal nödvändiga användarsvar och tid i väntan på användaren.
- Aktiv modelltid för planering, implementation, granskning respektive administration.
- Administrativa verktygsanrop, skrivningar och tillgänglig tokenförbrukning.
- Tid från mottaget godkännande till registrerat resultat, separat för verktyget och hela agentturen.
- Om användaren utifrån det senaste beskedet kan förutse vad Continue gör och vilket beslut som kommer därefter. Prova med en mänsklig genomgång av representativa chatt-/CLI-utskrifter; skilj den observationen från automatiska kontraktstester och markera den som ej verifierad om den inte utförts.
- Total leveranstid, omarbete, missförstådda krav, kvarvarande fel och felaktiga avslut.

Föreslagna mål att granska: exakt två användarbeslut i det enkla Strict-fallet; minst 50 procent mindre aktiv administration i de isolerade flödestesterna; högst fem sekunder för själva registreringsverktyget i minst 95 procent av dokumenterade lokala testkörningar med färdiga underlag. Målen är preliminära och är inte löften om hela agentturens svarstid eller om halverad total utvecklingstid.

Kvalitetsutfall ska redovisas separat från tidsvinsten. Snabbare körning med felaktigt avslut eller tappade krav uppfyller inte målet.

## Frågor till granskare

1. Ger det samlade startförslaget tillräcklig insyn i hela Epicen? Vilka uppdrag kräver ett tidigare vägval?
2. Är innebörden av samlad acceptans tydlig, inklusive möjligheten att acceptera bara Inkrementet?
3. Bevaras AIM:s ansvar att själv föreslå nästa Inkrement när målet inte är nått?
4. Är mekanismen för samlade uppdateringar tillräckligt liten, säker och återupptagbar?
5. Är kompatibilitet, körlägen och mätmål tillräckligt specificerade för implementation?
6. Förstår en användare av enbart chatt eller CLI vad Continue gör, vilket mandat som används och när nästa beslut behövs?
7. Skiljer förslaget tillräckligt tydligt mellan omverifiering, administrativa återförsök och en ändring som faktiskt kräver nytt godkännande?

## Underlag

- [AIM-metoden](../workflow/agile-iteration-method.md)
- [Kommandon, beslut och åtgärdskontrakt](../workflow/adapter-command-contract.md)
- [Verifiering inför Epic-avslut](../workflow/epic-closure-truth-audit.md)
- [Ingenjörsarbete och återanvändning av bevis](../workflow/engineering-delivery.md)
- [Publicerad utvärdering och dess begränsningar](../features/aim-3.1-evaluation.md)
- [Nuvarande kod för tillståndsövergångar](../../scripts/aim_runtime_contract.py)

Dokumentation: CC BY 4.0. Attribution: Jonas Eriksson, Agile Iteration Method.
