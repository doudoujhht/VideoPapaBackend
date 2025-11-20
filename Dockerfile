# Use an official lightweight Python image
FROM python:3.9-slim

# 1. Install FFmpeg and system dependencies
# We run apt-get update and install ffmpeg -y
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 2. Set up working directory
WORKDIR /app

# 3. Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code
COPY server.py .

# 5. Create the temp folder explicitly (optional but good practice)
RUN mkdir -p /tmp

# 6. Expose port 5000
EXPOSE 5000

# 7. Command to run the app using Gunicorn (Production server)
# formatting is 'gunicorn -w 4 -b 0.0.0.0:5000 filename:app_variable_name'
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "--timeout", "120", "server:app"]