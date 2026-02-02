import requests
import time
import json

BASE_URL = "http://localhost:8000/api"

def test_demo_deliberation():
    print("Testing /api/deliberation/demo...")
    
    # Payload for demo
    payload = {
        "case_id": "test_script",
        "title": "Verificación de Integración Backend",
        "description": "Prueba de integración scriptada para verificar que el endpoint demo responde y el orchestrator inicia.",
        "amount": 12345.67,
        "client_name": "Cliente de Prueba"
    }
    
    try:
        # Check Health
        print("Checking /api/health...")
        health = requests.get(f"{BASE_URL}/health")
        print(f"Health Status: {health.status_code}")
        
        # Check Stages (public endpoint)
        print("Checking /api/deliberation/stages...")
        stages = requests.get(f"{BASE_URL}/deliberation/stages")
        print(f"Stages Status: {stages.status_code}")

        # 1. Start Demo
        res = requests.post(f"{BASE_URL}/deliberation/demo", json=payload)
        res.raise_for_status()
        data = res.json()
        print(f"✅ Demo started! Response: {json.dumps(data, indent=2)}")
        
        project_id = data.get("project_id")
        if not project_id:
            print("❌ No project_id returned")
            return
            
        print(f"Tracking project: {project_id}")
        
        # 2. Poll Status a few times
        for i in range(5):
            time.sleep(2)
            status_res = requests.get(f"{BASE_URL}/projects/processing-status/{project_id}")
            status_data = status_res.json()
            print(f"Status Poll #{i+1}: {json.dumps(status_data, indent=2)}")
            
            # 3. Poll Trail
            trail_res = requests.get(f"{BASE_URL}/deliberation/trail/{project_id}")
            if trail_res.ok:
                trail = trail_res.json()
                print(f"Trail Items: {len(trail)}")
            
            if status_data.get("data", {}).get("status") == "completed":
                print("✅ Deliberation Completed!")
                break
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_demo_deliberation()
