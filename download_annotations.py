import os
import requests
import zipfile
import io

URL = "https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip"
DEST_DIR = "data/ami_raw/words"

def download_and_extract():
    os.makedirs(DEST_DIR, exist_ok=True)
    print("Downloading annotations zip...")
    resp = requests.get(URL)
    if resp.status_code == 200:
        print("Extracting...")
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            # Only extract words folder
            for info in z.infolist():
                if info.filename.startswith("words/"):
                    z.extract(info, DEST_DIR)
        print("Annotations downloaded and extracted.")
    else:
        print(f"Failed to download annotations. Status: {resp.status_code}")

if __name__ == "__main__":
    download_and_extract()
