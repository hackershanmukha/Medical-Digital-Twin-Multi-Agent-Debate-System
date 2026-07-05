import requests
import sys

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_debate_api():
    # 1. Login to get token
    print("Logging in...")
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "clinician@medicalai.com", "password": "ClinicianPass123!"}
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get a patient
    print("Fetching patients...")
    resp = requests.get(f"{BASE_URL}/patients/", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch patients: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    patients = resp.json()
    if not patients:
        print("No patients found.")
        sys.exit(1)
        
    patient_id = patients[0]["id"]
    print(f"Using patient {patient_id}")
    
    # 3. Trigger debate
    print("Triggering debate...")
    try:
        resp = requests.post(
            f"{BASE_URL}/debate/run",
            json={"patient_id": patient_id, "max_rounds": 3},
            headers=headers
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_debate_api()
