# Document Scanner Android App

A background-only Android app that automatically detects and uploads document photos to your paperless-ngx instance.

## Features

- **Background monitoring**: Continuously monitors device photo gallery for new images
- **On-device document detection**: Uses ML Kit to identify document photos locally
- **Configurable HTTP upload**: Sends detected documents to any HTTP endpoint
- **WiFi scheduling**: Optionally wait for WiFi connection before uploading
- **Retry logic**: Automatically retries failed uploads
- **Auto-start**: Starts automatically on device boot
- **Privacy-focused**: All document detection happens on-device

## Installation

1. Build and install the APK on your Android device
2. Grant the required permissions:
   - Storage access (to read photos)
   - Notification access (for background service status)
3. Open the app to configure settings

## Configuration

The app provides a settings screen to configure:

- **API Endpoint**: URL where documents will be uploaded (default: http://localhost:8000/api/documents/)
- **API Token**: Optional authentication token
- **WiFi Only**: Whether to upload only when connected to WiFi
- **Document Detection Confidence**: Minimum confidence level for document detection
- **Scan Interval**: How often to scan for new images

## How it works

1. **Photo Monitoring**: The app monitors your device's MediaStore for new images
2. **Document Detection**: New images are analyzed using ML Kit's text recognition
3. **Confidence Scoring**: Images are scored based on:
   - Amount of text detected
   - Presence of structured content (dates, numbers, headers)
   - Image aspect ratio
   - Number of text blocks
4. **Upload**: Documents meeting the confidence threshold are uploaded with metadata
5. **Network Awareness**: Uploads are scheduled based on your WiFi preferences

## API Integration

The app uploads documents via HTTP POST with multipart form data containing:

- `document`: The image file
- `filename`: Original filename
- `mime_type`: Image MIME type
- `size`: File size in bytes
- `width`/`height`: Image dimensions
- `date_added`/`date_modified`: Timestamps
- `confidence`: Document detection confidence score

## Permissions

- `READ_MEDIA_IMAGES` / `READ_EXTERNAL_STORAGE`: Read photos from gallery
- `INTERNET`: Upload documents
- `ACCESS_NETWORK_STATE` / `ACCESS_WIFI_STATE`: Check network conditions
- `FOREGROUND_SERVICE`: Run background service
- `RECEIVE_BOOT_COMPLETED`: Auto-start after device boot
- `POST_NOTIFICATIONS`: Show service status notifications

## Paperless-ngx Integration

To integrate with paperless-ngx:

1. Set API Endpoint to: `http://your-paperless-server:8000/api/documents/post_document/`
2. Set API Token to your paperless-ngx API token
3. Enable the service

Documents will be automatically consumed by paperless-ngx when uploaded.

## Troubleshooting

- **No documents detected**: Lower the confidence threshold in settings
- **Upload failures**: Check API endpoint URL and network connection
- **Service not running**: Ensure the service is enabled in settings and permissions are granted
- **Battery optimization**: Add the app to battery optimization whitelist if it stops working

## Privacy

- All document detection happens on-device using ML Kit
- No data is sent to external services except your configured endpoint
- The app only accesses images added after installation (configurable scan time)
