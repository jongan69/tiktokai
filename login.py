import argparse
import os
from tiktok_uploader import tiktok
from tiktok_uploader.Config import Config
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    _ = Config.load("./config.txt")
    
    parser = argparse.ArgumentParser(description="TikTok Login Script - Get session cookie")
    parser.add_argument("-n", "--name", help="Name to save cookie as (default: 'default')", default=os.getenv("TIKTOK_USERNAME"))

    args = parser.parse_args()
        
    # Perform login and save cookie
    print(f"Logging in... Cookie will be saved as '{args.name}'")
    tiktok.login(args.name)


