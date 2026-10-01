PRD: Enigma-dekrypterare i webbläsaren

Syfte

Bygg en webbaserad app som låter en användare kryptera och dekryptera med en historiskt korrekt tre-rotors Enigma I/M3 och försöka knäcka ett meddelande när startpositioner och kopplingspanel är okända. Appen ska visa vilka antaganden en sökning bygger på och låta användaren verifiera en kandidat i simulatorn.

Målgrupp och användningsfall

En intresserad besökare ska kunna (1) skriva text och ställa in en Enigma, (2) få tillbaka samma text när chiffertexten körs med samma inställningar och (3) ange en chiffertext och en gissad klartextfras, en crib, och söka efter möjliga inställningar inom den avgränsade sökrymden nedan.

Funktionella krav

1. Simulera Enigma I/M3 med rotorerna I–V, reflektor B eller C, valfri ordning av tre olika rotorer, ringinställning A–Z för varje rotor, startposition A–Z för varje rotor och kopplingspanel med 0–10 disjunkta bokstavspar. Tillämpa historisk rotorstegring inklusive dubbelstegning. Kryptering och dekryptering ska använda samma maskinoperation.
2. Erbjud ett tydligt simulatorläge där användaren kan ange alla inställningar, skriva eller klistra in text och se resultatet. Hantera A–Z utan att tappa bokstäver. Visa tydligt hur mellanslag, skiljetecken och andra tecken behandlas samt om de påverkar stegringen.
3. Erbjud ett separat knäckningsläge. Indata är chiffertext, rotorordning, reflektor, ringinställningar och en crib. Startpositionerna och kopplingspanelens par är okända. Användaren ska kunna ange var cribben börjar eller välja att söka efter möjliga placeringar. Sökningen ska använda cribben för att hitta kandidater som är förenliga med Enigmas funktion, inklusive rotorstegring och kopplingspanelens begränsningar. Enbart en lista över positioner utan hänsyn till okänd kopplingspanel uppfyller inte kravet.
4. Visa kandidaternas startpositioner, cribplacering, funna eller föreslagna kopplingspanelpar och dekrypterad förhandsvisning. Märk ofullständiga eller tvetydiga inställningar som sådana. Låt användaren öppna en kandidat i simulatorn, komplettera olösta kopplingar och pröva hela meddelandet.
5. Förklara i gränssnittet när en crib är omöjlig på grund av att en bokstav skulle krypteras till sig själv, när inga kandidater hittas och när flera kandidater återstår. Ge en begriplig indikation på framsteg och möjlighet att avbryta en längre sökning utan att sidan låser sig.
6. Lägg till minst ett färdigt exempel som användaren kan köra. Exemplet ska ha en känd ursprungsinställning och ett förväntat resultat som dokumenteras i repot.

Avgränsning

Knäckningsläget får anta att rotorordning, reflektor och ringinställningar är kända. Det får inte anta att startpositionerna eller kopplingspanelen är kända. Det krävs inte att appen knäcker godtycklig chiffertext utan crib. M4, andra historiska nätverksprocedurer och automatisk språkidentifiering ingår inte.

Kvalitet och leverans

* Kör lokalt i en modern webbläsare utan betald tjänst, konto eller serverberoende för själva krypteringen och sökningen.
* Ha ett begripligt gränssnitt för normal skrivbordsskärm och mobilskärm. Ange tydligt vad appen kan respektive inte kan härleda från en crib.
* Inkludera README med installation, start, bygg, test, sökningens antaganden och ett reproducerbart exempel.
* Lägg till automatiska tester för kända Enigma-vektorer, dubbelstegning, ringinställningar, kopplingspanel, rundtur kryptering/dekryptering och ett knäckningsfall där en känd giltig inställning återfinns bland kandidaterna. Testa även ett fall med flera eller inga kandidater.
* Välj själv språk, ramverk, arkitektur, algoritm, pakethanterare och intern arbetsordning. Undvik beroenden som gör att grundfunktionen kräver nätverk vid körning.

Acceptans

En extern granskare kan starta appen enligt README, verifiera simulatorn mot minst en oberoende känd Enigma-vektor och skapa en egen chiffertext med en okänd startposition och minst ett kopplingspanelpar. Med korrekt rotorordning, reflektor, ringar och crib ska knäckningsläget kunna hitta en förenlig kandidat, visa dess begränsningar och låta granskaren kontrollera den i simulatorn. Appen får inte presentera en tvetydig kandidat som en säkert återfunnen full nyckel.