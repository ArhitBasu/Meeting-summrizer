import os
import time
import json
import requests
import jiwer
import string

EVAL_DIR = "data/evaluation"
API_UPLOAD = "http://127.0.0.1:8000/api/meetings/upload"
API_GET = "http://127.0.0.1:8000/api/meetings/{}"
RESULTS_FILE = os.path.join(EVAL_DIR, "results.json")

def normalize_text(text):
    if not text:
        return ""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return " ".join(text.split())

def calculate_wer(reference, hypothesis):
    ref_norm = normalize_text(reference)
    hyp_norm = normalize_text(hypothesis)
    
    if not ref_norm:
        return None
        
    try:
        error = jiwer.wer(ref_norm, hyp_norm)
        return error
    except Exception as e:
        print(f"WER calc error: {e}")
        return None

def main():
    with open(os.path.join(EVAL_DIR, "metadata.json"), "r") as f:
        metadata = json.load(f)
        
    results = []
    
    for t in metadata:
        test_id = t["test_id"]
        audio_path = t["audio_path"]
        ref_path = t["ref_path"]
        
        print(f"--- Running {test_id} ({t['type']}) ---")
        
        if not os.path.exists(audio_path):
            print(f"Missing {audio_path}, skipping.")
            continue
            
        with open(ref_path, "r", encoding="utf-8") as f:
            reference = f.read()
            
        # Upload
        print(f"Uploading {audio_path}...")
        start_time = time.time()
        with open(audio_path, "rb") as f:
            files = {"file": (f"{test_id}.wav", f, "audio/wav")}
            try:
                resp = requests.post(API_UPLOAD, files=files)
                resp.raise_for_status()
                data = resp.json()
                meeting_id = data["id"]
                print(f"Uploaded successfully. Meeting ID: {meeting_id}")
            except Exception as e:
                print(f"Upload failed: {e}")
                t["status"] = "UPLOAD_FAILED"
                results.append(t)
                continue
                
        # Poll
        status = "UPLOADED"
        meeting_data = None
        while status not in ["COMPLETED", "TRANSCRIPTION_FAILED", "SUMMARIZATION_FAILED"]:
            time.sleep(10) # check every 10 seconds
            try:
                get_resp = requests.get(API_GET.format(meeting_id))
                get_resp.raise_for_status()
                meeting_data = get_resp.json()
                new_status = meeting_data["status"]
                if new_status != status:
                    print(f"Status changed: {new_status}")
                    status = new_status
            except Exception as e:
                print(f"Polling failed: {e}")
                time.sleep(5)
                
        end_time = time.time()
        
        t["final_status"] = status
        t["processing_time_sec"] = end_time - start_time
        
        if status == "COMPLETED":
            transcript = meeting_data.get("transcript", {}).get("text", "")
            summary = meeting_data.get("summary", {})
            decisions = meeting_data.get("decisions", [])
            action_items = meeting_data.get("action_items", [])
            
            t["generated_transcript"] = transcript
            t["generated_summary"] = summary
            t["generated_decisions"] = [d["text"] for d in decisions]
            t["generated_action_items"] = [a["task"] for a in action_items]
            
            wer = calculate_wer(reference, transcript)
            t["wer"] = wer
            print(f"Finished {test_id}. WER: {wer}")
        else:
            print(f"Failed {test_id} with status {status}")
            
        results.append(t)
        
        # Respect rate limits (Groq Whisper limit is typically 30/min or 14,400/day, LLM varies)
        time.sleep(10)
        
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("Evaluation complete.")

if __name__ == "__main__":
    main()
