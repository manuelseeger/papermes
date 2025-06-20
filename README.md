# papermes

A document management system built around paperless-ngx with an Android app for automatic document scanning and upload.

---

## Document Upload API Specification

The Android app uploads detected documents to a backend service using an HTTP POST request with multipart form data. Below is the API specification for backend implementation:

### Endpoint

- **URL:** `/api/documents/` (configurable in the app; for paperless-ngx: `/api/documents/post_document/`)
- **Method:** `POST`
- **Authentication:** Optional API token (sent as a header, e.g., `Authorization: Token <token>`)

### Request (multipart/form-data)

| Field           | Type    | Description                                 |
|-----------------|---------|---------------------------------------------|
| `document`      | file    | The image file (photo of the document)      |
| `filename`      | string  | Original filename of the image              |
| `mime_type`     | string  | MIME type of the image (e.g., image/jpeg)   |
| `size`          | int     | File size in bytes                          |
| `width`         | int     | Image width in pixels                       |
| `height`        | int     | Image height in pixels                      |
| `date_added`    | string  | ISO 8601 timestamp when image was added     |
| `date_modified` | string  | ISO 8601 timestamp when image was modified  |
| `confidence`    | float   | Document detection confidence score (0-1)   |

#### Example Request

```
POST /api/documents/
Authorization: Token <token>
Content-Type: multipart/form-data; boundary=...

--boundary
Content-Disposition: form-data; name="document"; filename="scan.jpg"
Content-Type: image/jpeg

(binary image data)
--boundary
Content-Disposition: form-data; name="filename"

scan.jpg
--boundary
Content-Disposition: form-data; name="mime_type"

image/jpeg
--boundary
Content-Disposition: form-data; name="size"

123456
--boundary
Content-Disposition: form-data; name="width"

2480
--boundary
Content-Disposition: form-data; name="height"

3508
--boundary
Content-Disposition: form-data; name="date_added"

2025-06-19T12:34:56Z
--boundary
Content-Disposition: form-data; name="date_modified"

2025-06-19T12:34:56Z
--boundary
Content-Disposition: form-data; name="confidence"

0.92
--boundary--
```

### Response

- **Success:** `201 Created` (or `200 OK`)
  - JSON body with document metadata or upload status
- **Failure:** Appropriate error code (`400`, `401`, `500`, etc.) with error message

### Notes

- The backend should validate the API token if provided.
- The backend should process the uploaded image and metadata, and return a JSON response.
- The endpoint must accept multipart form data.

---

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

