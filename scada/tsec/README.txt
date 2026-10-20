Module 6 railroad SCADA

Structure follows scada/manufacturing and scada/traffic:
  Dockerfile
  diagrams.yaml
  templates/diagram_base.html
  templates/diagrams/railroad_overview.html

Inheritance: railroad_overview.html -> diagram_base.html -> upstream base.html.
The upstream base.html is retained from wtaylor8/generic-scada:latest.
The Docker build compiles both templates and checks that upstream base.html
exposes title/content/scripts blocks before producing the image.

Build from the repository root:
  docker build -t evankunkel/generic-scada-railroad-control:latest -f scada/tsec/Dockerfile .

Jenkins builds/pushes that image when PROJECT_ID includes a line with 480-6.
480-6-build.py uses the dedicated generic-scada-railroad-control template and
SCADA_DIAGRAM_CONFIG=tsec/diagrams.yaml. Other projects' shared generic-scada
template is preserved. The root deployment Dockerfile needs no extra COPY:
the scenario templates are built into the separate SCADA image.

Dashboard uses the same GET /api/sensors contract as the other SCADA diagrams:
  {"TRACK-101":{"value":0,"status":"normal"}, ...}
POST /rediscover uses the same upstream discovery action.
Expected tags: TRACK-101, SIGNAL-101, GATE-201, APPROACH-201, SWITCH-301,
YARD-301, ROUTE-401, OCCUPANCY-401. These match the 480-6 builder exactly.

The page displays PLC telemetry, not generated train traffic. Missing/stale/
invalid values or failed API requests become UNKNOWN. The API receipt time
is not represented as the PLC sample time. Source freshness still depends on
the upstream API status. Switch/route numeric codes remain uninterpreted.
Occupancy/gate/aspect display conventions are documented on the diagram;
confirm them against the deployed scenario before interpreting process state.

Live acceptance after Jenkins builds the image:
1. Open railroad-scada at its GNS3 HTTP console. Check the railroad overview
   renders through the actual upstream base.html with no Jinja errors.
2. Inspect GET /api/sensors: confirm all eight tag keys, numeric values and
   statuses. Confirm PLC discovery/polling over TCP/502 to .31 through .34.
3. Compare dashboard values with the actual HMI/historian/PLC readings.
4. Stop one lab data source and confirm the API marks its tags stale and the
   page shows UNKNOWN. Restore it and check recovery.
5. Confirm a browser API failure removes prior valid-looking state.

Checked locally: dashboard JavaScript with normal/changing/stale/missing/
invalid/error fixtures; browser layout with labeled fixture data; Docker
copy-path/config consistency; builder offline validation; eight-tag matching.
Docker is unavailable locally, so the actual image build, upstream Jinja
contract check and live PLC connectivity must run in Jenkins/GNS3.
