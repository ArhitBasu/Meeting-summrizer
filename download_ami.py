import os
import requests
import urllib.request
import urllib.error

MEETINGS = ['EN2001a', 'EN2002a', 'ES2002a', 'ES2008a']
SPEAKERS = ['A', 'B', 'C', 'D', 'E']

BASE_URL = "https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus"
RAW_DIR = "data/ami_raw"

def download_file(url, dest_path):
    if os.path.exists(dest_path):
        print(f"Already exists: {dest_path}")
        return True
    try:
        print(f"Downloading {url} ...")
        urllib.request.urlretrieve(url, dest_path)
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}")
        return False
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def main():
    if not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)

    for meeting in MEETINGS:
        meeting_dir = os.path.join(RAW_DIR, meeting)
        audio_dir = os.path.join(meeting_dir, 'audio')
        words_dir = os.path.join(meeting_dir, 'words')
        
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(words_dir, exist_ok=True)
        
        # Download Audio
        audio_url = f"{BASE_URL}/{meeting}/audio/{meeting}.Mix-Headset.wav"
        audio_dest = os.path.join(audio_dir, f"{meeting}.Mix-Headset.wav")
        download_file(audio_url, audio_dest)
        
        # Download Words (per speaker)
        for spk in SPEAKERS:
            xml_url = f"{BASE_URL}/{meeting}/words/{meeting}.{spk}.words.xml"
            xml_dest = os.path.join(words_dir, f"{meeting}.{spk}.words.xml")
            download_file(xml_url, xml_dest)

if __name__ == "__main__":
    main()
