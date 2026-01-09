# ============================================
# STUDIO OS BACKEND - PRODUCTION DOCKERFILE
# ============================================
# Build: docker build -t studio-os-api .
# Run: docker run -p 8000:8000 --env-file .env studio-os-api

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies including ODBC driver for Azure SQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    gnupg2 \
    unixodbc-dev \
    apt-transport-https \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-prod.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY app/ app/
COPY wsgi.py gunicorn.conf.py ./

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run gunicorn
CMD ["gunicorn", "--bind=0.0.0.0:8000", "--timeout=600", "wsgi:app"]
