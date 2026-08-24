import json
import requests
import os

API_GET = "http://127.0.0.1:8000/api/meetings/"
RESULTS_FILE = "data/evaluation/results.json"
METADATA_FILE = "data/evaluation/metadata.json"

def main():
    # 8 evaluation tests + 1 manual test = 9 meetings in the DB
    meetings = []
    
    # Load metadata
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)
        
    results = []
    for test in metadata:
        test_id = test["test_id"]
        # Meeting ID mapping: test_01 -> 2, test_02 -> 3, ..., test_08 -> 9
        # Assuming they were uploaded in order
        meeting_id = int(test_id.split("_")[1]) + 1
        
        try:
            resp = requests.get(f"{API_GET}{meeting_id}")
            if resp.status_code == 200:
                data = resp.json()
                test["final_status"] = data["status"]
                
                if data["status"] == "COMPLETED":
                    test["generated_summary"] = data.get("summary", {})
                    test["generated_decisions"] = [d["text"] for d in data.get("decisions", [])]
                    test["generated_action_items"] = [a["task"] for a in data.get("action_items", [])]
                results.append(test)
            else:
                test["final_status"] = f"HTTP {resp.status_code}"
                results.append(test)
        except Exception as e:
            test["final_status"] = f"ERROR {e}"
            results.append(test)
            
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
