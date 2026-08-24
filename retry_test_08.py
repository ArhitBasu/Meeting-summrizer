import time
import requests

API_UPLOAD = "http://127.0.0.1:8000/api/meetings/upload"
API_GET = "http://127.0.0.1:8000/api/meetings/{}"
AUDIO_PATH = "data/evaluation/test_08/audio.mp3"

def main():
    print(f"Uploading {AUDIO_PATH}...")
    start_time = time.time()
    with open(AUDIO_PATH, "rb") as f:
        files = {"file": ("test_08.mp3", f, "audio/mpeg")}
        try:
            resp = requests.post(API_UPLOAD, files=files)
            resp.raise_for_status()
            data = resp.json()
            meeting_id = data["id"]
            print(f"Uploaded successfully. Meeting ID: {meeting_id}")
        except Exception as e:
            print(f"Upload failed: {e}")
            return
            
    # Poll
    status = "UPLOADED"
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
    print(f"Final status: {status} in {end_time - start_time:.2f} seconds.")
    if status == "COMPLETED":
        print("Success! Summary:")
        print(meeting_data.get("summary", {}).get("overview", ""))

if __name__ == "__main__":
    main()
