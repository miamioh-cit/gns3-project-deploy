# Use a slim Python base image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy required files explicitly
COPY gns3-project-deploy.py /app/
COPY 181-build.py /app/
COPY 182-build.py /app/
COPY 225-build.py /app/
COPY 281-build.py /app/
COPY 282-build.py /app/
COPY 284-build.py /app/
COPY 285-build.py /app/
COPY 325-build.py /app/
COPY 358-build.py /app/
COPY 386-build.py /app/
COPY 480-1-build.py /app/
COPY 480-2-build.py /app/
COPY 480-3-build.py /app/
COPY requirements.txt /app/
COPY project-id /app/
COPY datastore /app/
# Explicitly rename deploy_gns3_course.py to deploy-gns3-course.py upon copying
COPY course-config/course_it_ot_convergence/gns3_water_treatment/deploy_gns3_course.py /app/course/deploy-gns3-course.py
COPY course-config/course_it_ot_convergence/gns3_water_treatment/configs /app/course/configs
COPY course-config/course_it_ot_convergence/gns3_water_treatment/plc_sim /app/course/plc_sim

COPY scada/freshwater_treatment /app/scada/freshwater_treatment
COPY scada/templates/diagrams /app/scada/templates/diagrams
# Optional: install system utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        iputils-ping \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["python3", "gns3-project-deploy.py"]
