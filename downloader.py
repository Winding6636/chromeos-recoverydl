import requests
import os
import zipfile
import re

RECOVERY_JSON_URL = "https://dl.google.com/dl/edgedl/chromeos/recovery/recovery.json"

def fetch_recovery_list():
    return requests.get(RECOVERY_JSON_URL).json()

def find_model(data, keyword):
    pattern = re.compile(keyword, re.IGNORECASE)
    for item in data:
        if pattern.search(item.get("hwidmatch", "")):
            return item
    return None

def download_with_progress(url, path, progress_callback=None):
    r = requests.get(url, stream=True)
    total = int(r.headers.get("content-length", 0))

    if os.path.exists(path):
        if os.path.getsize(path) == total:
            return "skip"

    downloaded = 0
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
            downloaded += len(chunk)
            if progress_callback and total:
                progress_callback(int(downloaded / total * 100))

    return "done"

def extract(zip_path, out_dir):
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(out_dir)
