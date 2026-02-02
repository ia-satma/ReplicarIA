
import requests
import os

BASE_URL = "http://localhost:8000"
UPLOAD_URL = f"{BASE_URL}/api/projects/upload-file"

def verify_upload():
    print(f"Testing upload to {UPLOAD_URL}...")
    
    # Create a dummy file
    filename = "test_upload.txt"
    with open(filename, "w") as f:
        f.write("This is a test file for upload verification.")
        
    try:
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "text/plain")}
            response = requests.post(UPLOAD_URL, files=files)
            
        print(f"Upload Response Status: {response.status_code}")
        print(f"Upload Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                file_url = data.get("file_url")
                print(f"File URL received: {file_url}")
                
                # Verify retrieval
                if file_url.startswith("/"):
                    retrieve_url = f"{BASE_URL}{file_url}"
                else:
                    retrieve_url = file_url
                    
                print(f"Attempting to retrieve from: {retrieve_url}")
                r_response = requests.get(retrieve_url)
                print(f"Retrieval Status: {r_response.status_code}")
                
                if r_response.status_code == 200:
                    print("✅ VERIFICATION SUCCESS: File uploaded and retrieved.")
                else:
                    print("❌ VERIFICATION FAILED: Could not retrieve file.")
            else:
                print("❌ VERIFICATION FAILED: Upload response successful but success=False.")
        else:
            print("❌ VERIFICATION FAILED: Upload failed.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    verify_upload()
