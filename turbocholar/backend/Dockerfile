FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Initialize database and start server
CMD ["sh", "-c", "python scripts/init_db.py && python scripts/populate_data.py && python server.py --host 0.0.0.0 --port 8000"]