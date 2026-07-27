FROM python:3.12-slim

WORKDIR /workspace
RUN apt-get update && \
    apt-get install --yes --no-install-recommends tesseract-ocr tesseract-ocr-fra && \
    rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY app.py ./
COPY pages ./pages

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
