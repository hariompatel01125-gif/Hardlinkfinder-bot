FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
# Port 8080 expose karna zaroori hai Render ke liye
EXPOSE 8080
CMD ["python", "bot.py"]
