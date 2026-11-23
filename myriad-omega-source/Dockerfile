FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MYRIAD_DB_PATH=/var/lib/myriad/myriad_events.sqlite3 MYRIAD_ALLOW_CONTAINER_BIND=1
WORKDIR /opt/myriad
RUN groupadd --system myriad && useradd --system --gid myriad --home /opt/myriad myriad && mkdir -p /var/lib/myriad && chown myriad:myriad /var/lib/myriad
COPY --chown=myriad:myriad index.html server.py fabric.py agent_mesh.py operations.py workflows.json ./
COPY --chown=myriad:myriad assets/ ./assets/
USER myriad
EXPOSE 8788
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import json,urllib.request,sys; d=json.load(urllib.request.urlopen('http://127.0.0.1:8788/api/health',timeout=3));sys.exit(0 if d.get('healthy') and d.get('live_actor_coroutines')==10000 else 1)"
CMD ["python","server.py","--host","0.0.0.0"]
