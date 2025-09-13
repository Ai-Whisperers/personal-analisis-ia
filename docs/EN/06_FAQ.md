# Frequently Asked Questions (FAQ) v2.0

## General Questions

### Q: What's new in version 2.0?
**A:** Version 2.0 includes major improvements:
- **Intelligent Rate Limiting**: Proactive prevention of 429 errors
- **Usage Monitoring**: Detailed API cost tracking and optimization
- **Controller Architecture**: Better separation of concerns with background processing
- **Dynamic Batching**: Automatic optimization based on token usage
- **Production-Ready Configuration**: Robust secrets management and error handling

### Q: What is the SLA target for processing?
**A:** ≤10 seconds for processing 800-1200 comments, including rate limiting overhead and usage monitoring.

### Q: Does it work without an OpenAI API key?
**A:** Yes, the system has a built-in mock mode for testing and demonstration purposes. Set `ENABLE_MOCK_MODE = true` in your configuration.

### Q: What file formats are supported?
**A:** Excel (.xlsx, .xls) and CSV (.csv) files with columns: `NPS`, `Nota`, `Comentario Final`.

## API and Rate Limiting

### Q: How does the new rate limiting work?
**A:** v2.0 includes intelligent rate limiting:
- **Token counting** using tiktoken for precise estimation
- **API tier awareness** (automatically adjusts to your OpenAI tier)
- **Dynamic backoff** with jitter to avoid thundering herd
- **Proactive 429 prevention** with real-time monitoring

### Q: What OpenAI API tiers are supported?
**A:** All OpenAI API tiers (tier_1 through tier_5) and Azure OpenAI:
- **Tier 1**: 500 RPM, 200K TPM (default for new accounts)
- **Tier 2**: 5,000 RPM, 2M TPM (after $50 spent)
- **Tier 3**: 5,000 RPM, 4M TPM (after $100 spent)
- **Tier 4**: 10,000 RPM, 10M TPM (after $1,000 spent)
- **Tier 5**: 30,000 RPM, 150M TPM (after $5,000 spent)
- **Azure Standard**: 2,700 RPM, 450K TPM

### Q: How do I configure my API tier?
**A:** Set the `API_TIER` in your secrets configuration:
```toml
[API_CONFIG]
OPENAI_API_KEY = "sk-your-key"
API_TIER = "tier_2"  # or tier_1, tier_3, etc.
```

### Q: What happens if I hit rate limits?
**A:** The system handles rate limits gracefully:
1. **Intelligent backoff** with jitter (0.5s to 2s max)
2. **Automatic retry** with exponential backoff
3. **Usage monitoring** alerts when approaching limits
4. **Fallback to mock mode** if configured

### Q: How can I monitor API usage and costs?
**A:** v2.0 includes comprehensive usage monitoring:
- **Real-time dashboard** showing token and request usage
- **Cost estimation** based on current OpenAI pricing
- **Usage trends** and efficiency metrics
- **Automated recommendations** for optimization
- **Export functionality** for usage reports

## Performance and Optimization

### Q: Why is my processing slow?
**A:** Check these factors:
1. **API tier**: Higher tiers allow more concurrent requests
2. **Batch size**: Optimize based on your token limits
3. **Rate limiting**: May introduce delays to prevent 429 errors
4. **File size**: Very large files may take longer
5. **Network latency**: Distance to OpenAI servers affects speed

Run the usage monitor to get specific optimization recommendations.

### Q: How can I optimize performance for my API tier?
**A:** The system auto-optimizes, but you can:
- **Upgrade your OpenAI tier** for higher limits
- **Use dynamic batching** (enabled by default in v2.0)
- **Monitor usage patterns** and adjust based on recommendations
- **Configure optimal batch sizes** for your tier

### Q: What is dynamic batching?
**A:** v2.0 automatically adjusts batch sizes based on:
- **Current API usage** (remaining tokens/requests)
- **Your API tier limits**
- **Historical performance** data
- **Token estimation** for comments

## Technical Issues

### Q: I'm getting "Rate limit exceeded" errors
**A:** v2.0 should prevent these, but if you see them:
1. **Check your API tier** configuration
2. **Review usage dashboard** for utilization
3. **Enable conservative mode** by reducing max_concurrent_requests
4. **Check for other applications** using the same API key

### Q: The application is using too much memory
**A:** Try these solutions:
1. **Reduce batch size** in configuration
2. **Process smaller files** (split large files)
3. **Clear browser cache** and restart application
4. **Check for memory leaks** in logs

### Q: Charts are not displaying correctly
**A:** Common fixes:
1. **Refresh the page** and try again
2. **Check browser console** for JavaScript errors
3. **Ensure data was processed** successfully
4. **Try a different browser**

### Q: Export functionality is not working
**A:** Check:
1. **File permissions** in local-reports directory
2. **Available disk space**
3. **Browser download settings**
4. **Pop-up blockers** may prevent downloads

## Configuration Issues

### Q: How do I set up secrets properly?
**A:** For different environments:

**Local Development:**
```toml
# .streamlit/secrets.toml
[API_CONFIG]
OPENAI_API_KEY = "sk-your-dev-key"
API_TIER = "tier_1"
```

**Streamlit Cloud:**
- Configure through the Streamlit Cloud UI under App Settings > Secrets

**Self-hosted/Docker:**
```bash
export OPENAI_API_KEY="sk-your-prod-key"
export API_TIER="tier_2"
```

### Q: Which configuration should I use for production?
**A:** Production configuration template:
```toml
[API_CONFIG]
OPENAI_API_KEY = "sk-your-production-key"
API_PROVIDER = "openai"
API_TIER = "tier_2"  # Adjust based on your actual tier
MODEL_NAME = "gpt-4o-mini"

[PRODUCTION]
LOG_LEVEL = "INFO"
ENABLE_MOCK_MODE = false
ENABLE_DEBUG_MODE = false
ENABLE_PERFORMANCE_MONITORING = true

[SECURITY]
ENABLE_AUDIT_LOGGING = true
MAX_DAILY_COST = 100.0
```

### Q: How do I check if my configuration is correct?
**A:** The application performs automatic validation:
1. **System Status** section shows configuration health
2. **Logs** contain validation errors
3. **Usage monitor** shows if API calls are working
4. **Test with small file** to verify functionality

## Data and Analysis

### Q: What does each emotion score mean?
**A:** Emotion scores range from 0.0 to 1.0:
- **0.0**: Emotion not detected
- **0.1-0.3**: Low intensity
- **0.4-0.6**: Moderate intensity
- **0.7-0.9**: High intensity
- **1.0**: Maximum intensity

### Q: How accurate is the churn risk prediction?
**A:** Churn risk combines multiple factors:
- **Sentiment analysis** from 16 emotions
- **Keyword detection** for high-risk phrases
- **NPS correlation** with satisfaction scores
- **Contextual analysis** of complaint patterns

Accuracy depends on data quality and comment completeness.

### Q: Can I customize the analysis parameters?
**A:** Currently, the 16-emotion system is fixed for consistency, but you can:
- **Filter results** by emotion thresholds
- **Export raw data** for custom analysis
- **Adjust batch sizes** for performance
- **Configure rate limits** for your needs

### Q: What languages are supported?
**A:** The system primarily works with Spanish comments but can handle:
- **Spanish** (primary)
- **English** (secondary)
- **Mixed language** content (with reduced accuracy)

## Deployment and Scaling

### Q: Can I deploy this for multiple users?
**A:** Yes, but consider:
- **Rate limits** are shared across all users
- **Cost monitoring** tracks total usage
- **Session isolation** keeps user data separate
- **Scaling options** available with Docker/cloud platforms

### Q: How do I scale for high volume?
**A:** Scaling strategies:
1. **Upgrade OpenAI tier** for higher limits
2. **Use horizontal scaling** with Docker Compose
3. **Implement load balancing** with Nginx
4. **Monitor usage patterns** and optimize batch sizes

### Q: Is this suitable for enterprise use?
**A:** v2.0 includes enterprise features:
- **Usage monitoring** and cost control
- **Audit logging** for compliance
- **Security hardening** options
- **Background processing** for better UX
- **Configuration management** for different environments

## Troubleshooting

### Q: Application won't start
**A:** Check:
1. **Python version** (3.8+ required)
2. **Dependencies installed** (`pip install -r requirements.txt`)
3. **Configuration files** present and valid
4. **Port conflicts** (default 8501)

### Q: Getting import errors
**A:** Common solutions:
1. **Reinstall requirements**: `pip install -r requirements.txt --force-reinstall`
2. **Check Python path**: Ensure project root is in PYTHONPATH
3. **Virtual environment**: Use isolated environment
4. **Clear cache**: Delete `__pycache__` directories

### Q: Usage monitor shows no data
**A:** Verify:
1. **API calls are working** (not in mock mode)
2. **Processing completed** successfully
3. **Configuration includes monitoring** settings
4. **Browser refresh** may be needed

## Migration from v1.0

### Q: How do I upgrade from v1.0 to v2.0?
**A:** Upgrade steps:
1. **Update code**: Pull latest version
2. **Update requirements**: `pip install -r requirements.txt`
3. **Update configuration**: Add new v2.0 settings
4. **Test functionality**: Verify rate limiting works
5. **Deploy**: Follow deployment guide

### Q: Are there breaking changes in v2.0?
**A:** Minimal breaking changes:
- **Configuration structure** expanded (backward compatible)
- **New dependencies** (tiktoken, enhanced monitoring)
- **Optional new features** (can be disabled)
- **Enhanced error handling** (more informative)

### Q: Can I roll back to v1.0 if needed?
**A:** Yes, but you'll lose v2.0 features:
- **Rate limiting protection**
- **Usage monitoring**
- **Background processing**
- **Enhanced error handling**

## Support and Contributing

### Q: Where can I report bugs?
**A:** Report issues on GitHub:
- **Repository**: https://github.com/Ai-Whisperers/personal-analisis-ia
- **Include**: Error logs, configuration, and steps to reproduce
- **Check**: Existing issues first

### Q: How can I contribute?
**A:** Contributions welcome:
1. **Fork repository** on GitHub
2. **Follow development guide** (docs/EN/03_Dev_Guide.md)
3. **Create feature branch** for changes
4. **Submit pull request** with description
5. **Follow code review** process

### Q: Is commercial use allowed?
**A:** Check the license in the repository. Generally:
- **Open source** for educational/personal use
- **Commercial licensing** may require separate agreement
- **API costs** are your responsibility

### Q: How do I get professional support?
**A:** Professional support options:
- **GitHub Issues**: Community support
- **Documentation**: Comprehensive guides
- **Custom development**: Contact repository maintainers
- **Enterprise support**: Available for business deployments

## Cost and Billing

### Q: How much does it cost to run?
**A:** Costs include:
- **OpenAI API usage**: Based on tokens consumed
- **Infrastructure**: Hosting/cloud costs (if applicable)
- **No licensing fees** for the application itself

### Q: How can I estimate costs?
**A:** Use the built-in cost estimation:
- **Usage monitor** shows real-time costs
- **Batch estimation** before processing
- **Historical analysis** for budgeting
- **Tier recommendations** for optimization

### Q: Can I set spending limits?
**A:** Yes, through:
- **OpenAI dashboard**: Set hard limits on your account
- **Application config**: Set `MAX_DAILY_COST` in settings
- **Usage monitoring**: Automated alerts when approaching limits

For additional questions, please check the other documentation files or create an issue on the GitHub repository.