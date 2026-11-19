import gdown
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Google Drive folder URL (share the folder with "Anyone with the link")
FOLDER_URL = "https://drive.google.com/drive/folders/1Bv7nBKbiuujRZ6jVH3_rQMRWYoM1O31u?usp=sharing"

gdown.download_folder(FOLDER_URL, output=DATA_DIR, quiet=False)