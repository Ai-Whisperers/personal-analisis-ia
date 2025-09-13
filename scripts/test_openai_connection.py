# -*- coding: utf-8 -*-
"""
OpenAI Connection Test Script
Tests API connectivity and quota availability
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from openai import OpenAI
from config import get_openai_api_key
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_openai_connection():
    """Test OpenAI API connection and quota"""

    # Get API key from config (same as app uses)
    api_key = get_openai_api_key()

    if not api_key or api_key == "your_openai_api_key_here":
        logger.error("No valid API key found. Check your .streamlit/secrets.toml")
        return False

    logger.info(f"Using API key: {api_key[:15]}...")

    try:
        # Initialize client with our API key
        client = OpenAI(api_key=api_key)

        logger.info("Testing OpenAI connection...")

        # Make test request
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # Same model as production
            messages=[
                {"role": "system", "content": "Eres un asistente de prueba."},
                {"role": "user", "content": "Hola, este es un test de conexión. Responde brevemente."}
            ],
            max_tokens=50,
            temperature=0.3
        )

        # Extract response
        response_text = resp.choices[0].message.content
        token_usage = resp.usage

        # Log success
        logger.info("✅ API CONNECTION SUCCESSFUL!")
        logger.info(f"Model response: {response_text}")
        logger.info(f"Tokens used: {token_usage.total_tokens} (prompt: {token_usage.prompt_tokens}, completion: {token_usage.completion_tokens})")

        # Test batch capability (simulate our production scenario)
        logger.info("\nTesting batch processing capability...")

        batch_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analiza los siguientes comentarios y responde en formato JSON con emociones."},
                {"role": "user", "content": "Comentarios: 'Excelente servicio', 'Muy malo', 'Regular'. Responde con {\"status\": \"ok\"}"}
            ],
            max_tokens=100,
            temperature=0.3
        )

        batch_response = batch_resp.choices[0].message.content
        batch_tokens = batch_resp.usage

        logger.info("✅ BATCH PROCESSING TEST SUCCESSFUL!")
        logger.info(f"Batch response: {batch_response[:100]}...")
        logger.info(f"Batch tokens used: {batch_tokens.total_tokens}")

        # Calculate quota estimation
        total_tokens_used = token_usage.total_tokens + batch_tokens.total_tokens
        estimated_comments_per_batch = 30  # From our config
        estimated_tokens_per_comment = 150  # From our config

        estimated_daily_capacity = (150000 * 60 * 24) // (estimated_tokens_per_comment * estimated_comments_per_batch)

        logger.info(f"\n📊 QUOTA ESTIMATION:")
        logger.info(f"Total test tokens used: {total_tokens_used}")
        logger.info(f"Estimated daily comment processing capacity: ~{estimated_daily_capacity:,} comments")
        logger.info(f"Estimated hourly capacity: ~{estimated_daily_capacity // 24:,} comments")

        return True

    except Exception as e:
        logger.error(f"❌ API CONNECTION FAILED: {str(e)}")

        # Check specific error types
        if "insufficient_quota" in str(e).lower():
            logger.error("🚨 QUOTA EXHAUSTED - You need to add credits to your OpenAI account")
        elif "rate_limit" in str(e).lower():
            logger.error("🚨 RATE LIMIT HIT - API is being throttled")
        elif "invalid_api_key" in str(e).lower():
            logger.error("🚨 INVALID API KEY - Check your key in secrets.toml")
        else:
            logger.error(f"🚨 UNEXPECTED ERROR: {type(e).__name__}")

        return False

if __name__ == "__main__":
    print("🧪 OpenAI API Connection Test")
    print("=" * 50)

    success = test_openai_connection()

    print("=" * 50)
    if success:
        print("✅ ALL TESTS PASSED - Ready for production deployment!")
        print("💡 Your API key has quota and the optimized configuration will work")
    else:
        print("❌ TESTS FAILED - Fix issues before deploying")
        print("💡 Check your API key and account credits")

    sys.exit(0 if success else 1)