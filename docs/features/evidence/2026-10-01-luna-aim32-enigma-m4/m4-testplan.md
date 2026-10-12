# Låst plan: M4-följdändring, Luna-AIM och Luna-naked

Datum: 2026-10-01. Planen skrevs innan M4-lösningarnas kod granskades. Båda bedöms från sina frysta filversioner. Originalprojekten ändras inte.

## Gemensamt kontrakt

Det ursprungliga `enigma.prd` gäller fortsatt för M3. M4-tillägget är det identiska uppdrag som gavs till båda: M3/M4 i samma app; M4 med stillastående Beta/Gamma, tre olika rörliga rotorer I–VIII, B-Thin/C-Thin, fyra ringar och startlägen, 0–10 giltiga panelpar, korrekt dubbelstegning och dubbla hack på VI–VIII. M4-knäckning får känna rotorordning, reflektor, ringar och grekisk start, men inte de tre rörliga startlägena eller panelen. Känd/okänd cribplacering, förenliga och ärligt märkta kandidater, kandidatöverföring, progress, avbrytning och ofullständighetsstatus krävs. M3 ska inte regrediera. Ingen viss intern arkitektur eller exakt ursprungsnyckel krävs vid tvetydig crib.

## Oberoende prov

1. Kör respektive README:s installation, egna tester, typkontroll och bygge i kopior.
2. Jämför M3 mot de tidigare frysta 123 externa Py-Enigma-vektorerna och M4 mot nygenererade Py-Enigma 1.0.2-vektorer med Beta/Gamma, båda tunna reflektorer, rotor VI–VIII, skilda ringar, panelstorlekar 0/1/3/6/10 och notch/dubbelstegning. Kontrollera exakta chiffer och slutpositioner; rundtur ensam räcker inte.
3. Generera M4-sökfall utanför apparnas exempel med känt/okänt cribläge, 0/1/3/6/10 panelpar, crib över stegring, flera och inga kandidater samt avbruten sökning. Kontrollera varje returnerad kandidats förenlighet med extern referens. Skilj ofullständig sökning från bevisat felaktigt nollresultat. Fullständig ursprungsnyckel krävs bara när data räcker.
4. Kör samma utvalda prestandafall på samma maskin: en uppvärmning, tre växlade mätningar per app och fall, samma kandidatgräns och timeout, median och fullständighetsstatus. Jämför bara lika arbete.
5. Prova simulator, fel, crib, avbrott och kandidatöverföring i webbläsare på desktop och 390 px mobilbredd där verktygen tillåter det. Oprövade flöden märks ej verifierade.
6. Granska ändringsytan sedan den frysta M3-jämförelsen: ansvar, tillståndsägande, testernas felupptäckt, dokumentationens aktualitet och faktisk mängd omarbete. Fil- eller testantal ger inga poäng i sig.

## Poäng

Samma produktvikter som tidigare: Enigma-korrekthet 25 %, knäckningsförmåga/giltiga resultat 30 %, övrig kravuppfyllelse 15 %, prestanda/stabilitet 10 %, användbarhet 10 %, underhållbarhet/testkvalitet 10 %. Poäng 0–10 per KPI; samma rotfel dras inte flera gånger. M4-kraven väger tungt inom relevanta KPI:er men ursprunglig M3-funktion räknas också. Centralt funktionsfel framhävs även vid hög totalsumma.

Utvecklingseffektivitet redovisas separat efter produktpoäng: faktisk väggtid från användaren/loggar, token eller krediter där tillgängligt, mänskliga ingrepp, tjänstefördröjning/komprimering där observerbar, samt kvalitet per leverans. AIM:s öppna tidigare acceptans och längre befintliga tråd är försöksvillkor; ingen tid räknas bort i efterhand.
