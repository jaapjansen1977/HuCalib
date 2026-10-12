# OpenCap Processing GRF: rechten en aansluiting op HU3D

Onderzocht op 12 oktober 2026, repository
[`utahmobl/opencap-processing-grf`](https://github.com/utahmobl/opencap-processing-grf/tree/6369b19d9b53fa357befe651401af25b8350622d),
commit `6369b19d9b53fa357befe651401af25b8350622d`.
Dit is een verkenning; er is geen integratie of simulatie uitgevoerd.

## Gratis commerciële integratie van de code

De [hoofdlicentie](https://github.com/utahmobl/opencap-processing-grf/blob/6369b19d9b53fa357befe651401af25b8350622d/LICENSE.md)
is Apache 2.0. Deze staat kosteloos commercieel gebruik, wijziging en
verspreiding toe. De eigen app hoeft hierdoor niet volledig openbaar te worden.
Bij verspreiding moeten de licentie en relevante copyright-/attributieteksten
worden behouden, wijzigingen worden aangegeven en eventuele toepasselijke
NOTICE-informatie worden meegeleverd. De licentie geeft geen algemeen recht op
de handelsmerken van de auteurs.

De onderzochte simulatiebestanden dragen Apache 2.0-headers. In de doorzochte
tekstbestanden is geen non-commercial of research-only beperking gevonden.
Er is niet dezelfde aantoonbare VideoPose3D-herkomstkwestie gevonden als bij
ForcePose. Dit is geen volledige audit van alle transitieve afhankelijkheden.

De code noemt CasADi onder LGPL 3.0. LGPL verbiedt commercieel gebruik niet;
bij bundeling gelden wel eigen voorwaarden, onder meer voor vervanging van de
bibliotheek en eventuele wijzigingen eraan. OpenSimAD downloadt daarnaast
platformspecifieke pakketten van SourceForge; de inhoud en licenties daarvan
zijn in deze verkenning niet uitgepakt en beoordeeld.

## Wat het daadwerkelijk toevoegt

De [README](https://github.com/utahmobl/opencap-processing-grf/blob/6369b19d9b53fa357befe651401af25b8350622d/README.md)
beschrijft een hybride machine learning–simulatie-aanpak voor krachten,
gewrichtsmomenten en gewrichtscontactkrachten, gebaseerd op OpenCap-kinematica.

Het [batchscript](https://github.com/utahmobl/opencap-processing-grf/blob/6369b19d9b53fa357befe651401af25b8350622d/batchDownload_ForGRFTrack.py)
maakt model-/bewegingsinvoer, vraagt GRF op bij
`gradio_client.Client("alanttan/GaitDynamics")` en vervangt de voorspelde COP
vervolgens met een afzonderlijke COP-voorspelling. Het gaat dus om aanvulling
op GaitDynamics, niet om een volledig onafhankelijke GRF-voorspeller.
De hybride simulatie probeert de kinematica en voorspelde krachten samen te
volgen met een biomechanisch model en voet-grondcontact.

Er is een COP-checkpoint `OpenSimPipeline/ForGaitDynamics/cop_mlp_ar.pt` in de
repository opgenomen. Er is geen afzonderlijke modellicentie in de bekeken
bestanden gevonden; het bestand wordt als onderdeel van de Apache-repository
aangeboden. Een afzonderlijke bevestiging van herkomst en toepasselijkheid op
dit checkpoint kan een productdossier versterken. Externe GaitDynamics-gewichten
en de hosted dienst zijn afzonderlijke onderdelen en krijgen niet automatisch
de Apache-licentie van deze clientcode. De openbare GaitDynamics-hoofdcode
heeft MIT; de voorwaarden van de daadwerkelijk gebruikte modelbestanden en
dienst blijven apart te controleren.

## Aansluiting op HU3D

- Gebruik lokaal beschikbare Pose2Sim-resultaten in plaats van downloaden via
  een OpenCap-account. Daarvoor moeten model, markers, assen, eenheden en
  coördinaten op het verwachte OpenCap-model worden aangesloten.
- Vervang de hosted GaitDynamics-aanroep door de bestaande lokale HU3D/WSL2-route.
  De huidige voorbeeldcode uploadt de bewegings- en modelbestanden naar de dienst.
- Voeg de COP-voorspelling en voetoptimalisatie als afzonderlijk testbare stappen
  toe voordat de volledige hybride simulatie wordt geprobeerd.
- Controleer het verwachte spier-/contactmodel. Het bestaande HU3D-model is niet
  zonder verificatie een vervanging voor de modellen van dit project.

Windows wordt in de installatie-instructies ondersteund: OpenSim 4.5 en een
C++-compiler met Visual Studio zijn nodig voor de simulatiecomponent. Dat maakt
dit project niet automatisch een native Windows-vervanging voor de huidige
lokale GaitDynamics-runtime. De gratis Visual Studio Community-editie heeft
eigen organisatie-/gebruiksvoorwaarden; de README-claim dat zij voor iedereen
gratis is, moet niet als algemene commerciële licentiegarantie worden gebruikt.

De aanpak verwacht 3D-kinematica en modeldata, geen rechtstreekse Sports2D-invoer.
Een vlakke reconstructie kan worden onderzocht, maar valt buiten de hier
bevestigde werking. De voorbeelden focussen op lopen; de bestaande korte
evenwichtsoefening van HU3D is geen passende validatie van loopdynamica.

Het [loopvoorbeeld](https://github.com/utahmobl/opencap-processing-grf/blob/6369b19d9b53fa357befe651401af25b8350622d/Example_GRFTrack/example_walking_opensimAD_GRF.py)
waarschuwt expliciet dat de voorbeelden demonstreren hoe simulaties draaien en
geen biomechanische validiteit garanderen. De code adviseert korte segmenten
van minder dan twee seconden voor simulatie; `[]` kan de volledige trial kiezen.
Dit is een aanbeveling vanwege de simulatiebelasting, geen vaste maximale
videolengte.

## Besluit

Dit is een concrete, commercieel bruikbare kandidaat op het niveau van de
gepubliceerde broncode. Er is geen verplichte licentievergoeding voor die code.
Een volledige lokale HU3D-integratie vereist nog een adapter, verificatie van
de model-/pakketvoorwaarden en tests op geschikte loopdata. Gratis licentie
betekent geen gratis ontwikkeltijd, onbeperkte hosted dienst of bewezen
meetnauwkeurigheid.
