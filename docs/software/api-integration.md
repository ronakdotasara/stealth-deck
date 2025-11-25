# File 114: docs/software/api-integration.md

```markdown
# Stealth Deck - API Integration Guide

Complete guide for integrating external APIs with Stealth Deck.

---

## Gemini API Integration

### Overview

Stealth Deck uses Google's Gemini API for AI-powered features:
- Text generation and chat
- Image analysis and OCR
- Vision-based queries
- Code generation

### Getting API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key
5. Add to configuration:

```
# Add to config.json
"api_keys": {
    "gemini_api_key": "your-api-key-here"
}

# Or set environment variable
export GEMINI_API_KEY="your-api-key-here"
```

### Configuration

```
{
  "ai": {
    "model": "gemini-pro",
    "vision_model": "gemini-pro-vision",
    "temperature": 0.7,
    "max_tokens": 1024,
    "top_p": 0.95,
    "top_k": 40,
    "cache_responses": true,
    "timeout": 30
  }
}
```

### Usage Example

```
from src.ai.gemini_client import GeminiClient

# Initialize client
client = GeminiClient(api_key="your-api-key")

# Text generation
response = client.generate_text("What is Python?")
print(response)

# Image analysis
with open("image.jpg", "rb") as f:
    image_data = f.read()

response = client.analyze_image(image_data, "Describe this image")
print(response)

# Streaming response
for chunk in client.generate_text_stream("Tell me a story"):
    print(chunk, end='', flush=True)
```

### Rate Limits

**Free Tier:**
- 60 requests per minute
- 1,500 requests per day
- 1 million tokens per month

**Paid Tier:**
- Higher limits based on plan
- Contact Google Cloud for details

### Error Handling

```
from google.api_core.exceptions import GoogleAPIError

try:
    response = client.generate_text(prompt)
except GoogleAPIError as e:
    if e.code == 429:
        # Rate limit exceeded
        print("Rate limit reached, retry later")
    elif e.code == 401:
        # Invalid API key
        print("Invalid API key")
    else:
        print(f"API error: {e}")
```

### Best Practices

1. **Cache Responses**: Store common queries
2. **Batch Requests**: Combine multiple prompts
3. **Error Handling**: Always handle API errors
4. **Rate Limiting**: Implement exponential backoff
5. **Token Management**: Monitor token usage

---

## Custom API Integration

### Adding New API

1. Create API client in `src/ai/`
2. Implement base API interface
3. Add configuration
4. Update documentation

**Example:**
```
# src/ai/custom_api_client.py

class CustomAPIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.custom.com/v1"
    
    def make_request(self, endpoint: str, data: dict):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/{endpoint}",
            json=data,
            headers=headers
        )
        
        return response.json()
```

### API Configuration

```
{
  "api_keys": {
    "custom_api_key": "your-key"
  },
  "custom_api": {
    "base_url": "https://api.custom.com/v1",
    "timeout": 30,
    "max_retries": 3
  }
}
```

---

## Web Search API (Optional)

### Supported Providers

- **SerpAPI**: Google search results
- **DuckDuckGo**: Privacy-focused search
- **Brave Search**: Independent search

### SerpAPI Example

```
from serpapi import GoogleSearch

params = {
    "api_key": "your-serpapi-key",
    "q": "Python programming",
    "num": 5
}

search = GoogleSearch(params)
results = search.get_dict()

for result in results.get("organic_results", []):
    print(result["title"])
    print(result["link"])
```

### DuckDuckGo Example

```
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("Python programming", max_results=5))
    
    for result in results:
        print(result["title"])
        print(result["href"])
```

---

## OCR API Integration

### Tesseract OCR

**Local OCR (No API key needed):**

```
import pytesseract
from PIL import Image

# Load image
image = Image.open("document.jpg")

# Extract text
text = pytesseract.image_to_string(image)

print(text)
```

### Google Cloud Vision API

```
from google.cloud import vision

client = vision.ImageAnnotatorClient()

with open("image.jpg", "rb") as f:
    content = f.read()

image = vision.Image(content=content)

response = client.text_detection(image=image)

for text in response.text_annotations:
    print(text.description)
```

---

## QR Code Generation

### Local Generation (No API)

```
import qrcode

# Create QR code
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data("https://example.com")
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("qr_code.png")
```

---

## Weather API (Optional)

### OpenWeatherMap Example

```
import requests

api_key = "your-openweather-key"
city = "London"

url = f"http://api.openweathermap.org/data/2.5/weather"
params = {
    "q": city,
    "appid": api_key,
    "units": "metric"
}

response = requests.get(url, params=params)
data = response.json()

print(f"Temperature: {data['main']['temp']}°C")
print(f"Weather: {data['weather']['description']}")
```

---

## API Security

### Secure API Key Storage

**Environment Variables:**
```
export GEMINI_API_KEY="your-key"
```

**Encrypted Configuration:**
```
from cryptography.fernet import Fernet

# Generate key
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt API key
encrypted_key = cipher.encrypt(b"your-api-key")

# Decrypt when needed
api_key = cipher.decrypt(encrypted_key).decode()
```

**Secure File Storage:**
```
# Restrict permissions
chmod 600 /etc/stealth-deck/config.json

# Encrypt file
gpg -c config.json
```

### API Key Rotation

```
class APIKeyManager:
    def __init__(self):
        self.keys = []
        self.current_index = 0
    
    def add_key(self, key: str):
        self.keys.append(key)
    
    def get_key(self) -> str:
        key = self.keys[self.current_index]
        return key
    
    def rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.keys)
```

---

## Rate Limiting

### Implementation

```
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
    
    def allow_request(self) -> bool:
        now = time.time()
        
        # Remove old calls
        while self.calls and self.calls < now - self.period:
            self.calls.popleft()
        
        # Check if we can make request
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        if not self.calls:
            return 0
        
        oldest = self.calls
        wait = self.period - (time.time() - oldest)
        
        return max(0, wait)
```

**Usage:**
```
limiter = RateLimiter(max_calls=60, period=60)

if limiter.allow_request():
    # Make API request
    response = api_client.make_request()
else:
    wait = limiter.wait_time()
    print(f"Rate limited. Wait {wait:.1f}s")
```

---

## Response Caching

### Implementation

```
import hashlib
import pickle
from pathlib import Path

class ResponseCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def get(self, prompt: str):
        key = self.get_cache_key(prompt)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        return None
    
    def set(self, prompt: str, response):
        key = self.get_cache_key(prompt)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(response, f)
```

---

## Monitoring & Analytics

### Request Logging

```
import logging

class APILogger:
    def __init__(self):
        self.logger = logging.getLogger('api_monitor')
    
    def log_request(self, endpoint: str, duration: float, 
                   status: int, tokens: int):
        self.logger.info(
            f"API Request: {endpoint} | "
            f"Duration: {duration:.2f}s | "
            f"Status: {status} | "
            f"Tokens: {tokens}"
        )
```

### Usage Statistics

```
class APIStats:
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def record_request(self, tokens: int, cost: float):
        self.total_requests += 1
        self.total_tokens += tokens
        self.total_cost += cost
    
    def get_stats(self) -> dict:
        return {
            'requests': self.total_requests,
            'tokens': self.total_tokens,
            'cost': self.total_cost
        }
```

---

## Testing APIs

### Mock API Responses

```
from unittest.mock import Mock, patch

@patch('src.ai.gemini_client.GeminiClient.generate_text')
def test_api_call(mock_generate):
    mock_generate.return_value = "Mocked response"
    
    client = GeminiClient(api_key="test-key")
    response = client.generate_text("Test prompt")
    
    assert response == "Mocked response"
```

### Integration Tests

```
@pytest.mark.integration
def test_real_api():
    client = GeminiClient(api_key=os.getenv('GEMINI_API_KEY'))
    
    response = client.generate_text("Hello")
    
    assert response is not None
    assert len(response) > 0
```

---

## Troubleshooting

### Common Issues

**API Key Invalid:**
- Verify key is correct
- Check key hasn't expired
- Ensure proper permissions

**Rate Limit Exceeded:**
- Implement rate limiting
- Add exponential backoff
- Consider caching

**Timeout Errors:**
- Increase timeout value
- Check network connection
- Verify API status

**Response Parsing Errors:**
- Validate response format
- Handle edge cases
- Add error logging

---

**Version**: 1.0  
**Last Updated**: 2025-11-25
```

***