# papermes

A document management system built around paperless-ngx with an Android app for automatic document scanning and upload.

## Components

- **paperless-ngx**: The core document management system (in `./paperless-ngx`)
- **Android App**: Background document scanner app (in `./app`)
- **Backend**: Python backend services (in `./backend`)

## Quick Start

1. **Start paperless-ngx**: 
   ```bash
   cd paperless-ngx
   docker-compose up -d
   ```

2. **Build Android App**:
   ```bash
   cd app
   ./gradlew build
   ```

3. **Configure Android App**:
   - Install APK on your Android device
   - Set API endpoint to your paperless-ngx instance
   - Grant necessary permissions
   - Enable the background service

The Android app will automatically detect new document photos and upload them to paperless-ngx for processing.

