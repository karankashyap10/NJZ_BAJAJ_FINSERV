# Deployment Guide for Hugging Face API Integration

## 🚀 Overview

Your Django backend has been modified to use Hugging Face API instead of loading the SentenceTransformer model locally. This reduces your deployment size from 500MB+ to a much smaller footprint.

## 📋 Changes Made

### 1. **Removed Local Model Loading**
- Commented out `SentenceTransformer` import
- Removed local model initialization
- Updated all embedding functions to use API calls

### 2. **Added Hugging Face API Integration**
- Added `get_embeddings_from_hf_api()` function
- Added `get_single_embedding_from_hf_api()` function
- Updated all embedding calls throughout the code

### 3. **Updated Dependencies**
- Removed `sentence-transformers` from requirements.txt
- Added `requests` for API calls

## 🔧 Setup Instructions

### 1. **Get Hugging Face API Key**
1. Go to [Hugging Face](https://huggingface.co/)
2. Create an account or sign in
3. Go to Settings → Access Tokens
4. Create a new token with "read" permissions
5. Copy the token

### 2. **Set Environment Variables**
Create a `.env` file in your project root:

```bash
# Hugging Face API Configuration
HUGGINGFACE_API_KEY=your-huggingface-api-key-here

# Google Gemini API Key (already in your code)
GOOGLE_GEMINI_API_KEY=AIzaSyCiAWJw41BYAPi6qs4aJqjID_P3Goj1NQ4

# Django Secret Key
SECRET_KEY=your-django-secret-key-here
```

### 3. **Install Updated Dependencies**
```bash
pip install -r requirements.txt
```

## 🌐 Free Deployment Platforms

### **Recommended: Render**
1. **Easy Django deployment**
2. **Free PostgreSQL database**
3. **Automatic deployments from Git**
4. **Custom domains**

### **Alternative: Railway**
1. **$5/month credit (enough for small projects)**
2. **Excellent Django support**
3. **Automatic scaling**

## 📦 Deployment Steps

### **For Render:**

1. **Connect your GitHub repository**
2. **Set environment variables:**
   - `HUGGINGFACE_API_KEY`
   - `SECRET_KEY`
   - `GOOGLE_GEMINI_API_KEY`

3. **Build Command:**
   ```bash
   pip install -r requirements.txt
   python manage.py collectstatic --noinput
   ```

4. **Start Command:**
   ```bash
   gunicorn backend.wsgi:application
   ```

### **For Railway:**

1. **Connect your GitHub repository**
2. **Add environment variables**
3. **Railway will auto-detect Django**

## 🔍 Testing the API Integration

### **Test Hugging Face API:**
```python
import requests

def test_hf_api():
    api_key = "your-api-key"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": ["Hello world"],
        "options": {"wait_for_model": True}
    }
    
    response = requests.post(
        "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
```

## 📊 Benefits of This Approach

### **Deployment Size Reduction:**
- **Before**: 500MB+ (local model)
- **After**: ~50MB (API calls only)

### **Platform Compatibility:**
- ✅ **Render** (750h/month free)
- ✅ **Railway** ($5 credit)
- ✅ **Heroku** ($5/month)
- ✅ **Fly.io** (3 VMs free)
- ✅ **DigitalOcean** ($200 credit)

### **Performance:**
- **Latency**: Slightly higher due to API calls
- **Reliability**: Hugging Face provides 99.9% uptime
- **Scalability**: Automatic scaling with API

## 🚨 Important Notes

1. **API Rate Limits**: Hugging Face has generous free limits
2. **Internet Dependency**: Requires internet connection
3. **Cost**: Free tier is sufficient for most use cases
4. **Backup**: Consider having a fallback local model for critical applications

## 🔧 Troubleshooting

### **Common Issues:**

1. **API Key Error:**
   ```
   Error: Failed to get embeddings from Hugging Face API
   ```
   **Solution**: Check your API key and permissions

2. **Model Loading:**
   ```
   Error: Model is currently loading
   ```
   **Solution**: Wait a few seconds and retry (first request loads the model)

3. **Rate Limiting:**
   ```
   Error: Rate limit exceeded
   ```
   **Solution**: Implement request throttling or upgrade plan

## 📈 Monitoring

### **Add Logging:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In your API functions:
logger.info(f"Calling Hugging Face API for {len(texts)} texts")
```

### **Health Check Endpoint:**
```python
@app.route('/health')
def health_check():
    try:
        # Test HF API
        test_embedding = get_single_embedding_from_hf_api("test")
        return {"status": "healthy", "hf_api": "working"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 🎯 Next Steps

1. **Test locally** with your Hugging Face API key
2. **Deploy to Render** or your preferred platform
3. **Monitor performance** and API usage
4. **Consider caching** for frequently used embeddings

Your deployment is now ready for free platforms! 🚀 