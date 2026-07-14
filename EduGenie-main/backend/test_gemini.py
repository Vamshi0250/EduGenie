"""
EduGenie -- Test Gemini Connection
Standalone script to verify your GEMINI_API_KEY is working.
Run:  python -m backend.test_gemini
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.gemini_service import (
    generate_response,
    GeminiConfigError,
    GeminiAPIError,
)


def main():
    print("=" * 50)
    print("EduGenie -- Gemini API Connection Test")
    print("=" * 50)
    print()

    test_prompt = "In one sentence, what is photosynthesis?"

    print(f'Sending test prompt: "{test_prompt}"')
    print()

    try:
        response = generate_response(test_prompt)
        print("[OK] SUCCESS -- Gemini responded:")
        print(f"  {response}")
        print()
        print("Your API key is working. You're ready to build!")
        return 0

    except GeminiConfigError as e:
        print(f"[FAIL] CONFIGURATION ERROR:")
        print(f"  {e}")
        print()
        print("Fix: Copy .env.example to .env and paste your Gemini API key.")
        return 1

    except GeminiAPIError as e:
        print(f"[FAIL] API ERROR:")
        print(f"  {e}")
        print()
        print("Your key loaded but the API call failed. Check your key and network.")
        return 1

    except Exception as e:
        print(f"[FAIL] UNEXPECTED ERROR:")
        print(f"  {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
