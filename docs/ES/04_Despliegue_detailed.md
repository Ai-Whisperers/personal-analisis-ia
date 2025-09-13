# 🚀 Deployment Guide - Personal Comment Analyzer

## Streamlit Cloud Deployment (Recommended)

### Prerequisites
1. GitHub repository with your code
2. OpenAI API key (optional - app works in mock mode without it)

### Step 1: Prepare Repository
Ensure your repository has:
- `streamlit_app.py` (main entry point)
- `requirements.txt` (dependencies)
- `.streamlit/config.toml` (app configuration)
- Proper `.gitignore` (secrets are excluded)

### Step 2: Deploy to Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Connect your GitHub account**

3. **Deploy new app**:
   - Repository: `your-username/personal-analisis-ia`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

4. **Configure Secrets** (in the deployment dashboard):
   ```toml
   # Add your OpenAI API key here
   OPENAI_API_KEY = "sk-your-actual-openai-key-here"
   
   # Optional: Override default configurations
   MODEL_NAME = "gpt-3.5-turbo"
   MAX_BATCH_SIZE = 100
   MAX_TOKENS_PER_CALL = 500
   MAX_WORKERS = 4
   LOG_LEVEL = "INFO"
   DEBUG_MODE = false
   MOCK_FALLBACK_ENABLED = true
   ```

5. **Click "Deploy"**

### Step 3: Verify Deployment
- App should be accessible at `https://your-app-name.streamlit.app`
- Test file upload functionality
- Verify mock mode works (without API key)
- Test with real API key (if provided)

## Local Development

### Setup
```bash
# Clone repository
git clone https://github.com/your-username/personal-analisis-ia
cd personal-analisis-ia

# Install dependencies
pip install -r requirements.txt

# Configure secrets (optional)
# Edit .streamlit/secrets.toml and add your OpenAI API key
```

### Running Locally
```bash
# Run the Streamlit app
streamlit run streamlit_app.py

# App will be available at http://localhost:8501
```

## Configuration Options

### Environment Variables / Secrets
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | No (mock mode) |
| `MODEL_NAME` | OpenAI model | gpt-3.5-turbo | No |
| `MAX_BATCH_SIZE` | Comments per batch | 100 | No |
| `MAX_WORKERS` | Parallel workers | 4 | No |
| `MAX_TOKENS_PER_CALL` | Token limit | 500 | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `DEBUG_MODE` | Debug mode | false | No |

### Features
- ✅ **Mock Mode**: Works without API key for demonstration
- ✅ **16 Emotion Analysis**: Individual percentage for each emotion
- ✅ **Parallel Processing**: Optimized for large datasets
- ✅ **NPS Analysis**: Automatic categorization
- ✅ **Churn Prediction**: Risk scoring
- ✅ **Export Options**: Excel, CSV, JSON

### Performance
- **SLA Target**: ≤10 seconds for 800-1200 comments
- **File Size Limit**: 50MB
- **Supported Formats**: .xlsx, .xls, .csv
- **Required Columns**: NPS, Nota, Comentario Final

## Troubleshooting

### Common Issues

1. **App won't start**
   - Check `streamlit_app.py` is the entry point
   - Verify all dependencies in `requirements.txt`
   - Check logs for import errors

2. **API key issues**
   - Ensure OpenAI API key is valid and has credits
   - Check key format starts with `sk-`
   - Verify secrets configuration in Streamlit Cloud

3. **File upload fails**
   - Check file has required columns: NPS, Nota, Comentario Final
   - Ensure file size < 50MB
   - Verify file format is .xlsx, .xls, or .csv

4. **Performance issues**
   - Reduce batch size in secrets configuration
   - Check OpenAI API rate limits
   - Monitor token usage

### Debug Mode
Enable debug mode by setting `DEBUG_MODE = true` in secrets to see additional information.

### Mock Mode
The app automatically falls back to mock mode if:
- No OpenAI API key is provided
- API key is invalid or expired
- Rate limits are exceeded

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** in production
3. **Rotate API keys** regularly
4. **Monitor usage** and costs
5. **Enable rate limiting** if needed

## Support

- **Documentation**: [Project README](./README.md)
- **Issues**: [GitHub Issues](https://github.com/Ai-Whisperers/personal-analisis-ia/issues)
- **Repository**: [GitHub](https://github.com/Ai-Whisperers/personal-analisis-ia)

---

🎭 **Personal Comment Analyzer** - Ready for production deployment!