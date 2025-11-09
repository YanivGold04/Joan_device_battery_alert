FROM python:3.11-slim
  
WORKDIR /app
  
COPY requirements.txt requirements.txt
  
RUN pip install --no-cache-dir -r requirements.txt
  
COPY joan_device_battery_alert.py .
  
EXPOSE 8080
  
CMD ["python", "joan_device_battery_alert.py"]
