#!/usr/bin/env python3
"""
Script to analyze receipt images using OpenAI Vision API.

This script takes a photo from the testdata directory and submits it to the OpenAI API
to analyze what's in the image.

Environment variables required:
- OPENAI_API_KEY: Your OpenAI API key
"""

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


import httpx

import ssl

import truststore

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

http_client = httpx.Client(verify=ssl_context)

gpt_prompt_pricing = 0.0000020
# Cost per completion token
gpt_completion_pricing = 0.000008

class ImageAnalysis(BaseModel):
    """Structured response model for image analysis."""
    description: str
    objects_detected: list[str]
    text_content: str
    confidence_level: str


def encode_image_to_base64(image_path: Path) -> str:
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_image_with_openai(image_path: Path, prompt: str = "What's in this image?") -> str:
    """
    Send an image to OpenAI Responses API for structured analysis.
    
    Args:
        image_path: Path to the image file
        prompt: The question to ask about the image
        
    Returns:
        The structured API response or None if error
    """
    # Load environment variables
    load_dotenv()
    
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key, http_client=http_client)
      # Encode image to base64
    base64_image = encode_image_to_base64(image_path)
    
    
    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": "what's in this image?" },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )
    usage = response.usage.output_tokens * gpt_completion_pricing + response.usage.input_tokens * gpt_prompt_pricing
    print(f"Total USD burned: ${usage}")
    return response.output_text
        
def main():
    """Main function to run the receipt analysis."""
    # Find the testdata directory relative to this script
    script_dir = Path(__file__).parent
    testdata_dir = script_dir.parent.parent.parent / "testdata"
    
    # Look for image files in testdata
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(testdata_dir.rglob(f"*{ext}"))
        image_files.extend(testdata_dir.rglob(f"*{ext.upper()}"))
    
    if not image_files:
        print("No image files found in testdata directory")
        return
    
    # Use the first image found
    image_path = image_files[0]
    print(f"Analyzing image: {image_path}")
      # Analyze the image
    result = analyze_image_with_openai(
        image_path=image_path,
        prompt="Analyze this image and provide a detailed description, list any objects you can detect, extract any text content, and rate your confidence level (high/medium/low)."
    )
    
    if result:
        print("\n" + "="*50)
        print("OpenAI Responses API Analysis Result:")
        print("="*50)
        print(f"Description: {result}")
        #print(f"Objects Detected: {', '.join(result.objects_detected)}")
        #print(f"Text Content: {result.text_content}")
        #print(f"Confidence Level: {result.confidence_level}")
    else:
        print("Failed to analyze image")


if __name__ == "__main__":
    main()
