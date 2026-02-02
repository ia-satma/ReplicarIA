import requests
import json

BASE_URL = "http://localhost:8000"
SUBMIT_URL = f"{BASE_URL}/api/projects/submit"

print(f"Testing UNAUTHENTICATED submission to {SUBMIT_URL}...")

payload = {
    "project_name": "HACKED PROJECT",
    "sponsor_name": "Hacker",
    "sponsor_email": "hacker@evil.com",
    "budget_estimate": 100000,
    "description": "This should be blocked."
}

# No Headers (except Content-Type)
headers = {
    "Content-Type": "application/json"
    # No Authorization
    # No X-Empresa-ID (or maybe we need one to pass validation inside, but lets try without first to see middleware behavior)
}

try:
    response = requests.post(SUBMIT_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

    if response.status_code == 200:
        print("❌ SECURITY VULNERABILITY CONFIRMED: Allowed unauthenticated submission.")
    elif response.status_code in [401, 403]:
        print("✅ Security Check PASSED: Request blocked.")
    elif response.status_code == 400:
        # Might be missing Empresa ID, which is a form of check
        print("⚠️  Partial Security: Blocked likely due to missing headers, but need to verify if bypassing auth works with fake headers.")
        
        # Try again with Fake Empresa ID but no Auth
        headers["X-Empresa-ID"] = "fake-empresa"
        response = requests.post(SUBMIT_URL, json=payload, headers=headers)
        print(f"Retry with Fake Empresa ID - Status: {response.status_code}")
        if response.status_code == 200:
             print("❌ SECURITY VULNERABILITY CONFIRMED: Allowed unauthenticated submission with just Empresa ID.")

except Exception as e:
    print(f"Error: {e}")
