FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt
COPY backend/ ./backend/
EXPOSE 8000
CMD ["python","-m","uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
