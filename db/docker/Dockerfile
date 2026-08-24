FROM postgres:18

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-18-postgis-3=3.6.4+dfsg-2.pgdg13+1 \
        postgresql-18-postgis-3-scripts=3.6.4+dfsg-2.pgdg13+1 \
    && rm -rf /var/lib/apt/lists/*
