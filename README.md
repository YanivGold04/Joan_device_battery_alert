# Joan Device Battery Alert

This repository contains a lightweight Python Flask application designed to monitor Joan display devices and send daily Slack alerts when any device’s battery falls below a specified threshold. The service is deployed on Google Cloud Run and scheduled to execute automatically every day at 10:00 AM using Google Cloud Scheduler.

## Overview

The application performs the following actions:
1. Fetches device data from the Joan API.
2. Checks for devices with battery levels below the configured threshold.
3. Formats and sends notifications to a designated Slack channel through an incoming webhook.

Example Slack output:

<img width="1697" height="1028" alt="Screenshot 2025-11-09 at 15 09 13" src="https://github.com/user-attachments/assets/132fe5ff-f8a0-493e-b03d-62cac3f9c991" />


Israel devices below 20%  
- Israel Office – Allison: 19%

US devices below 20%  
- US – Huron: 13%

## Cloud Run and Scheduler Deployment

### 1. Build and Push Docker Image
```bash
gcloud builds submit --tag gcr.io/<YOUR_PROJECT_ID>/joan-device-battery-alert
```

### 2. Deploy to Cloud Run
```bash
gcloud run deploy joan-device-battery-alert   --image gcr.io/<YOUR_PROJECT_ID>/joan-device-battery-alert   --platform managed   --region <YOUR_REGION>   --allow-unauthenticated   --set-env-vars     JOAN_CLIENT_ID=your_client_id,     JOAN_CLIENT_SECRET=your_client_secret,     SLACK_WEBHOOK=https://hooks.slack.com/services/your/webhook,     BATTERY_THRESHOLD=20
```

### 3. Schedule Daily Trigger (10 AM)
```bash
gcloud scheduler jobs create http daily-joan-alert   --schedule "0 10 * * *"   --uri https://<YOUR_CLOUD_RUN_URL>   --http-method=GET
```

## Environment Variables

| Variable | Description | Example |
|-----------|-------------|----------|
| JOAN_CLIENT_ID | Joan API client ID | your_joan_client_id |
| JOAN_CLIENT_SECRET | Joan API secret | your_joan_client_secret |
| SLACK_WEBHOOK | Slack webhook URL for posting alerts | https://hooks.slack.com/services/... |
| BATTERY_THRESHOLD | Minimum battery percentage before alert | 20 |
| PORT | Flask app port | 8080 |

Create a `.env` file for local testing:
```
JOAN_CLIENT_ID=your_joan_client_id_here
JOAN_CLIENT_SECRET=your_joan_client_secret_here
SLACK_WEBHOOK=https://hooks.slack.com/services/your/slack/webhook
BATTERY_THRESHOLD=20
```

## Local Development

Run locally using Docker:
```bash
docker build -t joan-alert .
docker run -p 8080:8080 --env-file .env joan-alert
```

Access the app locally at:
```
http://localhost:8080
```

### Endpoints

| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/` | GET | Executes a full device battery check and sends Slack alerts |
| `/health` | GET | Returns a simple JSON response indicating service health |

## Slack Integration

The application integrates directly with Slack Incoming Webhooks. Alerts are posted automatically in the designated Slack channel (e.g., `#on-site-support-alerts`). Each message is grouped by region and lists devices that require battery replacement.

## Project Structure

```
joan_device_battery_alert/
├── Dockerfile
├── joan_device_battery_alert.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Security

This repository does not contain any real credentials or internal identifiers. All sensitive data, including Joan API credentials and Slack webhooks, must be supplied through environment variables or a secure secret management system.

## Summary

| Component | Purpose |
|------------|----------|
| Google Cloud Run | Hosts the Flask service |
| Google Cloud Scheduler | Triggers the service daily at 10 AM |
| Slack Webhook | Delivers battery alerts to Slack |
| Docker | Packages and deploys the application |
