# Sử dụng bản python slim cho nhẹ image
FROM python:3.10-slim

WORKDIR /app

# Copy và cài đặt thư viện trước để tận dụng Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code backend vào container
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]