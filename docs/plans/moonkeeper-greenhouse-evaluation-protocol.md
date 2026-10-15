# Testuppdrag: Månvaktens växthus

Version 0.4, 2026-10-13. Omfattningen är korrigerad enligt användarens uttryckliga order: ett baslinjespel och en ny körning med förbättrat AIM. Det tidigare utökade upplägget med fler varianter och byggarupprepningar gäller inte.

## Arbetsordning

1. Låt befintligt AIM bygga testprojektet.
2. Bevara resultatet och mät baslinjen enligt [kvalitetskriterierna](moonkeeper-greenhouse-quality-measurement.md).
3. Genomför [AIM-förbättringarna](aim-product-quality-requirements.md).
4. Låt förbättrat AIM lösa samma uppdrag från samma utgångsläge i en ny session.
5. Jämför produkterna enligt samma kvalitetskriterier och mätmetod.

Inga extra produktvarianter, separata appar, externa jämförelsespår eller upprepade byggarkörningar får läggas till utan användarens uttryckliga beställning. Metoden anpassas till uppdraget; ett mer omfattande experiment är inte ett mål i sig.

## Samma produktuppdrag till båda körningarna

> Jag vill skapa ett litet, lokalt körbart webbläsarspel om en vaktmästare som återställer ett övergivet växthus på en månbas. Det ska kännas stillsamt och nyfiket, och belöna eftertanke snarare än reflexer. Jag tänker mig några korta banor och att det ska vara lätt att försöka igen.
>
> Hjälp mig hitta en stark spelidé och bygg ett spelbart spel när idén har tillräckligt stöd. Ta reda på vilka vägval som verkligen påverkar spelupplevelsen, använd små prototyper när de kan besvara en fråga bättre än diskussion och välj själv tekniska detaljer som går lätt att ändra. Fråga mig när ett svar från mig kan ändra spelets riktning väsentligt.

Ingen skill namnges i produktbriefen. Metod- och körningskonfiguration tillförs separat och likvärdigt enligt respektive spårs fastställda villkor.
## Förberett svar

När AIM frågar om den betydelsefulla öppna frågan om upplevelse/perspektiv/rörelse, ge följande svar. Ge inte ledtråden i förväg om AIM inte frågar.

> Jag föreställer mig en liten synlig figur i en 2D-värld sedd från sidan, som rör sig genom platsen. Jag vill att det ska kännas som att utforska en värld, inte flytta markörer på ett bräde. Rörelsen ska vara lugn, utan precisionskrav. Du får välja resten.

Fakta som byggaren kan undersöka ska inte göras till användarfrågor. Ett produktval eller genomförandemandat är inte fabricerad acceptans.

## Likvärdiga villkor

Båda byggare använder GPT-6 Luna med hög resonemangsnivå, samma produktbrief, tekniska kvalitetskrav, verktyg och tillgängliga skillkatalog. Starta från tom produktkatalog i en ny session utan jämförelseprodukt, bedömningsanteckningar eller denna planeringschatt. Den enda avsiktliga skillnaden är det frysta AIM-paketet. Dokumentera faktiska skillval och miljöskillnader.

Bevara första inlämningen med kontrollsumma och faktisk tid. Handrätta inte baslinjen. Utför bedömning och det redan definierade avgränsade underhållsprovet i kopior av samma produkt; de är verifiering, inte nya beställda spel. Tekniska mätningar upprepas enligt mätbilagan för att redovisa variation i laddning och körning.

Byggarbudgeten är samma i båda körningarna:45min aktiv tid inklusive intern granskning. Väntan räknas bort endast när den faktiskt loggats och inget arbete pågår. Produktens körprestanda och utvecklingstiden redovisas separat. Användaracceptans och mänskliga observationer får inte hittas på.

## Aktiv baslinje och bevarande

Den första ordinarie öppna körningen, `baseline-open-02-first`, är baslinje. Den valdes genom körordning, inte genom poäng. Dess frysta SHA-256 är `d2a89f66fe8aaf8c8299912fe2c2c4f03a2bfa01d155f204b3fbc456bc1c4ad0`. Övriga redan skapade spel ligger kvar som historiskt sidomaterial; de ingår inte i denna jämförelse och ska inte vidareutvecklas.

Lokala produkter, kontrollsummor och råmätningar finns i `output/aim-quality-evaluation/2026-10-13-run01/`. Det frysta gamla protokollet bevaras som historik; denna korrigerade omfattning styr fortsatt arbete.

## Bedömning och slutsats

Produktkvalitet har företräde framför processtid. Redovisa alla elva dimensioner, kravbrister, kodbegriplighet, underhållsprov, faktiska prestandavärden och säkerhetsfynd. Saknad mänsklig observation är overifierad; ingen komplett Q beräknas när en dimension saknar belägg.

Ett före/efter-par visar skillnaden i detta uppdrag. Det bevisar inte generell överlägsenhet, statistisk signifikans eller bättre resultat än Pocock. Känd försämring får inte döljas av högre totalpoäng eller kortare tid. Ingen extra testkampanj startas för att förstärka en önskad slutsats.

Kontinuitet mellan increment ingår i förbättringskravet. En faktisk fortsättning förutsätter att den ryms i användarens uppdrag och dess verkliga acceptansstatus; om den inte genomförts redovisas detta som en evidenslucka, inte som godkänt beteende.
