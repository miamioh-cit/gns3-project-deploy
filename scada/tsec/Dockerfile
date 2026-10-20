FROM wtaylor8/generic-scada:latest

COPY scada/tsec/diagrams.yaml /app/scenarios/tsec/diagrams.yaml
COPY scada/tsec/templates/diagram_base.html /app/scada/templates/diagram_base.html
COPY scada/tsec/templates/diagrams/railroad_overview.html /app/scada/templates/diagrams/railroad_overview.html

# Fail the image build if the upstream template contract changes.
RUN python -c "from jinja2 import Environment, FileSystemLoader; e=Environment(loader=FileSystemLoader('/app/scada/templates')); base=e.get_template('base.html'); assert {'title','content','scripts'} <= set(base.blocks), 'Upstream base.html blocks changed'; [e.get_template(p) for p in ('diagram_base.html','diagrams/railroad_overview.html')]; print('Railroad Jinja templates compiled')"
