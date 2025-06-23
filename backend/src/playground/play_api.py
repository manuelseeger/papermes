#!/usr/bin/env python3
"""
Quick script to test the host API by uploading a receipt image
"""

import httpx
import json
import asyncio
from pathlib import Path

async def upload_receipt_to_host_api():
    """Upload the Shopping Aldi receipt to the host API"""
    
    # Path to the test image
    image_path = Path("../testdata/photos/receipts/Shopping Aldi.jpg")
    
    if not image_path.exists():
        print(f"Error: Image file not found at {image_path}")
        return
    
    # Prepare metadata for the receipt
    metadata = {
        "document_type": "receipt",
        "source": "test_upload",
        "store": "Aldi",
        "user_id": "test_user",
        "timestamp": "2025-06-23T10:00:00Z",
        "tags": ["grocery", "receipt", "aldi"],
        "notes": "Test upload of Shopping Aldi receipt"
    }
    
    print(f"Uploading {image_path.name} to host API...")
    print(f"File size: {image_path.stat().st_size} bytes")
    print(f"Metadata: {json.dumps(metadata, indent=2)}")
    
    # Make request to the API
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Open and upload the file
            with open(image_path, "rb") as f:
                files = {"file": (image_path.name, f, "image/jpeg")}
                data = {"metadata": json.dumps(metadata)}
                
                print("\nSending request to http://localhost:8090/analyze_file...")
                response = await client.post(
                    "http://localhost:8090/analyze_file",
                    files=files,
                    data=data
                )
            
            print(f"\n✅ Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"📄 Filename: {result['filename']}")
                print(f"📊 File size: {result['file_size']} bytes")
                print(f"🔍 Content type: {result['content_type']}")
                print(f"📋 Analysis status: {result['analysis_status']}")
                print(f"🔬 Analysis results: {json.dumps(result['analysis_results'], indent=2)}")
            else:
                print(f"❌ Upload failed: {response.text}")
                
        except httpx.ConnectError:
            print("❌ Error: Could not connect to the host API server.")
            print("💡 Make sure the server is running on http://localhost:8090")
            print("   You can start it with: 'Run Host API Only' launch configuration")
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_health_endpoint():
    """Test the health check endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            print("🔍 Testing health endpoint...")
            response = await client.get("http://localhost:8090/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data}")
            else:
                print(f"⚠️  Health check returned: {response.status_code}")
        except httpx.ConnectError:
            print("❌ Health check failed: Could not connect to server")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    return True

async def main():
    """Main function to test the host API"""
    print("🚀 Testing Papermes Host API with Shopping Aldi receipt...")
    print("=" * 60)
    
    # First check if the API is running
    is_healthy = await test_health_endpoint()
    
    if is_healthy:
        print("\n📤 Uploading receipt...")
        await upload_receipt_to_host_api()
    else:
        print("\n💡 Start the Host API first using the 'Run Host API Only' configuration")

if __name__ == "__main__":
    asyncio.run(main())