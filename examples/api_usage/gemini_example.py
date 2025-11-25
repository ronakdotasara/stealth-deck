#!/usr/bin/env python3
"""
Example: Using Gemini API with Stealth Deck
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'raspberry-pi'))

from src.ai.gemini_client import GeminiClient


def main():
    """Gemini API usage examples."""
    
    # Initialize client
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not set")
        return
    
    client = GeminiClient(api_key)
    
    print("Stealth Deck - Gemini API Examples")
    print("=" * 60)
    
    # Example 1: Simple text generation
    print("\n1. Text Generation:")
    print("-" * 60)
    
    response = client.generate_text("What is Python programming?")
    print(response[:200] + "...")
    
    # Example 2: Streaming response
    print("\n2. Streaming Response:")
    print("-" * 60)
    
    print("Question: Explain AI in simple terms")
    print("Response: ", end='', flush=True)
    
    for chunk in client.generate_text_stream("Explain AI in simple terms"):
        print(chunk, end='', flush=True)
    
    print()
    
    # Example 3: Image analysis
    print("\n3. Image Analysis:")
    print("-" * 60)
    
    # Create a test image
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='blue')
    img.save('/tmp/test_image.jpg')
    
    with open('/tmp/test_image.jpg', 'rb') as f:
        image_data = f.read()
    
    response = client.analyze_image(image_data, "What color is this image?")
    print(response)
    
    # Example 4: Conversation
    print("\n4. Multi-turn Conversation:")
    print("-" * 60)
    
    messages = [
        "Hello! I'm learning Python.",
        "What's a good first project?",
        "How do I get started with that?"
    ]
    
    for msg in messages:
        print(f"\nYou: {msg}")
        response = client.generate_text(msg)
        print(f"AI: {response[:150]}...")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
