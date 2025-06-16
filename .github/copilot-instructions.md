# papermes - a document management system

This is a document management system built around paperless-ngx. 

paperless-ngx lives in ./paperless-ngx and is fully setup and running. Documents can be submitted to paperless-ngx via the consume directory in ./paperless-ngx.

## General
- Secrets are stored in .env

## Python
- Use uv for managing dependencies
- Source code is in the ./src directory
- Use type hints with pydantic
- Use f-strings for string formatting

## Python libraries
- Use httpx over requests for HTTP requests
- Use pydantic for data validation and settings management
- Use pytest for testing
