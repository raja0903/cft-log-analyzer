# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the code
COPY . .

# Expose port
EXPOSE 5000

# Environment variables
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000

# Run app
CMD ["python", "AI_app.py"]
