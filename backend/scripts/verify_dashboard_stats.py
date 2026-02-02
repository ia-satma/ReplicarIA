
import requests
import json
import sys

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

BASE_URL = "http://localhost:8000"

def test_stats():
    print(f"Testing stats endpoint: {BASE_URL}/api/durezza/estadisticas")
    try:
        response = requests.get(f"{BASE_URL}/api/durezza/estadisticas")
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Success (200){RESET}")
            
            # Check for new fields
            if "kpis" in data:
                 print(f"{GREEN}✅ Found 'kpis'{RESET}")
                 print(json.dumps(data["kpis"], indent=2))
            else:
                 print(f"{RED}❌ 'kpis' missing in response{RESET}")
                 
            if "distribucion_riesgo" in data:
                 print(f"{GREEN}✅ Found 'distribucion_riesgo'{RESET}")
                 print(json.dumps(data["distribucion_riesgo"], indent=2))
            else:
                 print(f"{RED}❌ 'distribucion_riesgo' missing{RESET}")
            
            if "proyectos" in data and "lista_dashboard" in data["proyectos"]:
                 print(f"{GREEN}✅ Found 'lista_dashboard'{RESET}")
                 print(f"Projects count: {len(data['proyectos']['lista_dashboard'])}")
            else:
                 print(f"{RED}❌ 'lista_dashboard' missing{RESET}")
                 
            return True
        else:
            print(f"{RED}❌ Failed: {response.status_code}{RESET}")
            print(response.text)
            return False
    except Exception as e:
        print(f"{RED}❌ Connection error: {e}{RESET}")
        return False

if __name__ == "__main__":
    if test_stats():
        sys.exit(0)
    else:
        sys.exit(1)
