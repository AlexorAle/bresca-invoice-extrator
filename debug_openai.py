#!/usr/bin/env python3

"""
Debug script para OpenAI client
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_client():
    try:
        import openai
        print(f"OpenAI version: {openai.__version__}")

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return

        print(f"API key loaded: {api_key[:20]}...")

        print("Setting OpenAI API key...")
        openai.api_key = api_key
        print("✅ OpenAI API key set successfully")

        # Test a simple API call
        print("Testing API call...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ API call successful")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_openai_client()
