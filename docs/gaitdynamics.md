# Experimentele GaitDynamics-koppeling

Na een geslaagde Pose2Sim-analyse biedt **GaitDynamics voorbereiden** een
invoercontrole van het MOT-bestand en het bijbehorende OpenSim-model. Deze
controle draait in de Windows-app, zonder GaitDynamics te installeren.
Het venster geeft aan wat geschikt is en wat eerst aangepast moet worden.
Je kunt het controlerapport bewaren. Bij meerdere resultaten kies je zelf de
juiste combinatie van model en beweging.

De eerste rekenmodule voorspelt grondreactiekrachten en aangrijpingspunten
voor beide voeten, met de officiële refinement-gewichten op CPU. Ze draait
apart op Linux. Voor lokaal gebruik op een Windows-computer is **WSL2** de
beoogde route: dat is een Linux-omgeving op dezelfde computer. Native Windows
wordt niet ondersteund, omdat nimblephysics geen Windows-wheels publiceert.
De WSL2-koppeling is nog niet automatisch vanuit het Windows-venster gestart.

## Wat nog niet rechtstreeks kan

Het huidige Pose2Sim-model levert 62 coördinaten met een gesegmenteerde rug.
GaitDynamics verwacht een ander lichaamsmodel met 23 onafhankelijke
coördinaten, waaronder `lumbar_extension`, `lumbar_bending` en
`lumbar_rotation`. De Pose2Sim-rugsegmenten mogen niet zomaar worden hernoemd
of opgeteld. Ook anatomische assen, gewrichtsdefinities en schaal moeten passen.

Daarom blokkeert deze eerste koppeling het huidige Pose2Sim-model. De volgende
stap is de gemeten/gereconstrueerde markertrajecten met een passend, geschaald
GaitDynamics-model opnieuw verwerken via inverse kinematica, en die
conversie valideren. Ontbrekende kinematica wordt in deze eerste versie niet
met diffusie gegenereerd. Het gebruik van een willekeurig voorbeeldmodel bij
jouw MOT-bestand is geen geldige vervanging voor modelconversie.

## Afzonderlijke runtime voor een ontwikkelproef

Op Linux of binnen WSL2, met Python 3.12 en de repository beschikbaar:

```bash
python3.12 -m venv .venv-gaitdynamics
.venv-gaitdynamics/bin/python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
.venv-gaitdynamics/bin/python -m pip install -r requirements-gaitdynamics.txt
.venv-gaitdynamics/bin/python tools/setup_gaitdynamics.py --output gait-runtime
.venv-gaitdynamics/bin/python tools/smoke_gaitdynamics.py --runtime gait-runtime --output gait-validation/result
```

De runtime-download gebruikt GaitDynamics-commit
`8dc5aed58161a129fd2d58ff071cb802f2654be9`. Broncode, licentie en beide
modelbestanden worden met vastgelegde SHA-256 gecontroleerd. Modellen blijven
lokaal en komen niet in Git. Installatie gebeurt niet in de HuCalib- of
Pose2Sim-omgeving. De setup overschrijft geen bestaande runtime.

Voor compatibele eigen invoer, met de juiste persoonslengte, massa en
loopbandsnelheid (0 voor overground):

```bash
.venv-gaitdynamics/bin/python -m mocap_app.analysis.gaitdynamics \
  --motion /pad/naar/beweging.mot --model /pad/naar/geschaald-model.osim \
  --check-only

.venv-gaitdynamics/bin/python -m mocap_app.analysis.gaitdynamics \
  --motion /pad/naar/beweging.mot --model /pad/naar/geschaald-model.osim \
  --output /pad/naar/nieuwe-resultaten --runtime gait-runtime \
  --python .venv-gaitdynamics/bin/python --height 1.75 --mass 70 \
  --treadmill-speed 0
```

Lengte en massa in dit commando zijn voorbeelden; vul werkelijke waarden in.
De interfacecontrole is een eerste structurele controle. De worker verifieert
daarnaast de onafhankelijke modelcoördinaten en hun volgorde met nimblephysics.
De oorspronkelijke bestanden blijven bestaan; de worker gebruikt kopieën.
Alleen visuele meshes worden uit een aparte numerieke modelkopie verwijderd.
Gewrichtstransformaties en lichaamsdimensies blijven behouden.

Resultaten: `gaitdynamics.json`, `gaitdynamics.log`, `environment.json` en
`ground_reaction_forces.mot`. Het rapport bevat checksums, runtimeversies,
persoonsgegevens en eenheden. `force1` is de rechtervoet, `force2` de linkervoet;
krachten zijn in N, aangrijpingspunten in m. De `torque`-kolommen zijn nullen
uit de upstream-export: vrije momenten worden hiermee niet voorspeld.
De resultaten zijn modelvoorspellingen, geen krachtplaatmetingen. Er worden
geen kniebelastingen of gewrichtsmomenten berekend in deze eerste koppeling.

## Proef en beperkingen

De workflow **GaitDynamics-CPU-proef** draait de officiële voorbeeldbeweging
met volledige kinematica. De voorbeeldbestanden komen uit de officiële
Hugging Face-demo op commit `c905e7af6f7a32e8cc99f413ff6559dd897a91b5`.
Voor deze technische proef worden 1,75 m, 70 kg en 0 m/s gebruikt als
expliciete demo-aannames; dit zijn niet bevestigde gegevens van de proefpersoon.
De proef toetst werking, 499 uitvoerregels en eindige waarden, geen nauwkeurigheid.

Twee upstream-headerfouten worden expliciet afgehandeld: de officiële demo
vermeldt 2000 regels, terwijl er 499 zijn; alleen een kopie krijgt de juiste
header. De GRF-export vermeldt 9 kolommen terwijl er 19 zijn; de worker
corrigeert die metadata en legt de oorspronkelijke header vast. De numerieke
gegevens worden daarmee niet gewijzigd.

De cloudmachine kan de officiële modeldownloads momenteel niet bereiken
(HTTP 403 via de netwerkproxy). De CPU-proef wordt daarom op de Linux-runner
van GitHub Actions uitgevoerd. Een geslaagde Linux-proef bevestigt geen
native Windows- of WSL2-uitvoering en valideert de Pose2Sim-modelconversie niet.
Je hebt voor deze voorbeeldproef geen webcams of ChArUco-bord nodig.
