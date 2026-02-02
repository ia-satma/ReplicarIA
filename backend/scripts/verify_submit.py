import requests
import json
import time

BASE_URL = "http://localhost:8000"
SUBMIT_URL = f"{BASE_URL}/api/projects/submit"

print(f"Testing submission to {SUBMIT_URL}...")

payload = {
    "project_name": "Proyecto de Prueba Automática",
    "sponsor_name": "Test User",
    "sponsor_email": "test@satma.mx",
    "company_name": "Empresa Test SA de CV",
    "department": "IT",
    "description": "Un proyecto de prueba para verificar el endpoint de submit.",
    "strategic_alignment": "Eficiencia",
    "expected_economic_benefit": 100000,
    "budget_estimate": 50000,
    "duration_months": 6,
    "urgency_level": "Alta",
    "requires_human": "No",
    "attachments": [],
    "is_modification": False
}

headers = {
    "Content-Type": "application/json",
    "X-Empresa-ID": "test-empresa"
}

try:
    response = requests.post(SUBMIT_URL, json=payload, headers=headers)
    print(f"Submit Status: {response.status_code}")
    print(f"Submit Body: {response.text}")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            project_id = data.get("project_id")
            print(f"✅ Submission SUCCESS. Project ID: {project_id}")
            
            # Poll status
            poll_url = f"{BASE_URL}/api/projects/processing-status/{project_id}"
            print(f"Polling status at {poll_url}...")
            
            for i in range(5):
                time.sleep(1)
                poll_res = requests.get(poll_url)
                if poll_res.status_code == 200:
                    status_data = poll_res.json()
                    print(f"Poll {i+1}: {status_data}")
                    if status_data.get("data", {}).get("status") in ["initializing", "processing", "completed"]:
                         print("✅ Status Check SUCCESS: Project is processing.")
                         break
                else:
                    print(f"Poll Failed: {poll_res.status_code}")
        else:
            print("❌ Submission Failed (Success=False)")
    else:
        print("❌ Submission Failed (HTTP Error)")

except Exception as e:
    print(f"❌ Verification Failed with Exception: {e}")
