import json
import requests
import os

API_GET = "http://127.0.0.1:8000/api/meetings/10"
RESULTS_FILE = "data/evaluation/results.json"

def main():
    resp = requests.get(API_GET)
    if resp.status_code == 200:
        data = resp.json()
        
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
            
        for test in results:
            if test["test_id"] == "test_08":
                test["final_status"] = data["status"]
                if data["status"] == "COMPLETED":
                    test["generated_summary"] = data.get("summary", {})
                    test["generated_decisions"] = [d["text"] for d in data.get("decisions", [])]
                    test["generated_action_items"] = [a["task"] for a in data.get("action_items", [])]
                break
                
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print("Updated results.json with test_08 (meeting 10)")
    else:
        print(f"Failed to fetch meeting 10: {resp.status_code}")

if __name__ == "__main__":
    main()
