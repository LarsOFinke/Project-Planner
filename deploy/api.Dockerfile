FROM python:3.13.10-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    SQLAlchemy==2.0.54 alembic==1.20.0 fastapi==0.141.1 \
    python-multipart==0.0.32 starlette==0.52.1 uvicorn==0.53.0
COPY src /app/src
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["uvicorn", "project_planner.api.http.app_factory:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
