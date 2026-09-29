# Separat API-prov: samma verifierade funktion, olika kostnader

Genomfört 29 september 2026. Två tomma projekt fick identisk PRD för en lokal
Team Notes-API med SQLite, tenantisolering, roller och atomisk versionskontroll.
A använde GPT-6 Astra High utan AIM; B använde samma modell med det frysta
AIM-paketet. Varje färsk session hade 20 minuter utan delegering. API-kraven,
HTTP-proven, mätarbetslasten och tre typer av felinjektion låstes före start.
Detta kravunderlag hade inte använts för att justera AIM-instruktionerna.

## Resultat

| Mått | A: utan AIM | B: AIM |
| --- | ---: | ---: |
| Rapporterad bygg- och verifieringstid | **8:54** | 13:48,7 |
| Oberoende HTTP-kontroller | 129/129 | 129/129 |
| Beständig data efter omstart | Godkänt | Godkänt |
| Egna tester, återkörda av bedömaren | 10 grupper godkända | 12 grupper godkända |
| Upptäckta säkerhets-/konkurrensmutationer | 3/3 | 3/3 |
| Lista 50 poster, median | 0,502 ms | 0,501 ms |
| Läs en post, median | 0,421 ms | 0,425 ms |
| Versionskontrollerad uppdatering, median | **1,358 ms** | 1,407 ms |
| Serverns topp-RSS under hela mätprocessen | 19,61 MiB | **18,53 MiB** |
| Server-CPU, inklusive uppläggning av data | 12,27 s | 12,18 s |

AIM tog cirka 55 procent längre att leverera i detta par. Medianlatens och CPU
är nära varandra; små skillnader i en körning bevisar ingen stabil rangordning.
Toppminnet var cirka 5,5 procent lägre med AIM. Det är ett observerat resultat,
inte en generell resursgaranti.

## Oberoende bedömning

Båda kördes via samma publika `run.sh`-gräns utan importer av produktkod.
HTTP-kontrollerna omfattar roller, cross-tenant CRUD, dubbla auth-headers,
felaktiga JSON-typer och fält, storleksgränser, fråga/ID-validering, inert
SQL/HTML-innehåll, stale-version-avvisning, samtidiga ändringar/raderingar,
ordning och begränsning av listor samt felkontrakt utan tokenläckage.
Datan kontrollerades igen efter stopp och omstart mot samma SQLite-fil.
Fem kompletterande startkonfigurationsfall passerade för varje produkt.

Varje mutation ändrade en avgränsad kontroll i en separat kopia: tenantkontroll
vid läsning, versionskontroll vid uppdatering respektive viewer-skrivskydd.
Båda sviterna gav verkliga assertionsfel för alla tre, utan setup- eller syntaxfel.
Samma avvikande publika beteende bekräftades av det oberoende HTTP-provet.
B:s versionsmutant behöll den extra SQL-villkorskontrollen, men returnerade
felaktigt lyckad status; dess tester fångade även det felet.

Prestandaprovet kördes sekventiellt efter båda inlämningarna, med samma Python
3.9.6/macOS/arm64-miljö. En ny databas per produkt fylldes med 10 000 poster per
tenant genom HTTP: totalt 20 000 skapanden, 128 byte innehåll per post.
Uppläggningen tog 32,60 respektive 30,92 sekunder och räknas separat från latens.
Efter 25 uppvärmningsanrop mättes 200 listor, 500 läsningar och 200 uppdateringar,
med kontroll av tenant, ID-ordning och version. Varje anrop använde en ny HTTP-
anslutning. Råvärden, p95 och max finns i arkivet. `wait4` mätte serverprocessens
CPU och topp-RSS, inklusive uppstart och dataladdning, utan klientprocessen.

## Struktur, säkerhet och dokumentation

A har en formatterad servermodul med konfiguration, HTTP och lagring i samma
fil. B separerar dessa ansvar i `notes/config.py`, `notes/server.py` och
`notes/storage.py`. Det ger tydligare ändringsställen vid inspektion; ingen ny
underhållsuppgift genomfördes på API-apparna, så en tidsvinst är inte belagd.
Båda använder parameteriserad SQL, korta skrivtransaktioner, ett tenant/ID-index
och en begränsning på 32 arbetstrådar.

Ett kompletterande, uttryckligen icke poängsatt prov bekräftade extra lokala
HTTP-skydd i B: främmande Host fick 400 och främmande Origin fick 403, medan
motsvarande autentiserade anrop fick 200 i A. Dessa kontroller var inte uttryckliga
PRD-kriterier, och resultatet används därför inte för att underkänna A.
Det demonstrerar en extra försvarsmekanism, inte en åtkomst utan token i A.
B har också begränsad konfigurationsläsning och restriktiva rättigheter på nya
filer; dess dokumentation redovisar gränser och avsaknad av publik driftgaranti.

B:s review upptäckte och rättade problem med långa Content-Length-värden i
Expect-flödet och normalisering av numeriska värden. Den efterfrågade även
prov av överlast och relativa filsökvägar. Den slutliga dokumentationen stämmer
med de granskade modulerna; B:s källbundna kunskapsposter kontrollerades aktuella.
Reviewresultaten är användbara, men ett par isolerar inte AIM som deras orsak.

## Evidens och avgränsning

[Maskinläsbar sammanfattning](evidence/2026-09-29-paired-api.json).
Beständigt arkiv:
`/Users/jonaseriksson/Documents/Codex/2026-09-29/aim-permissions-pilot`.
Alla 60 låsta indatasfiler och 31 frysta inlämningsfiler var oförändrade efter
bedömningen. Originalapparna och de frysta AIM-paketen har inte efterkorrigerats.

Inget totalpoäng skapades efter att resultaten var kända. Detta är ett par,
en maskin och ett lokalt API-kontrakt. Alla säkerhetsstandarder eller generell
överlägsenhet mot en modell utan metod är inte verifierade.
