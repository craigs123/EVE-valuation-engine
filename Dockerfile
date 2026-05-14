FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

RUN python -c "import streamlit, pathlib, re; \
p = pathlib.Path(streamlit.__file__).parent / 'static' / 'index.html'; \
p.write_text(re.sub(r'<title>.*?</title>', '<title>EVE</title>', p.read_text()))"

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
