import os
import sys
import logging
import requests

from termcolor import colored

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_dir(path: str) -> None:
    """
    Removes every file in a directory.

    Args:
        path (str): Path to directory.

    Returns:
        None
    """
    try:
        if not os.path.exists(path):
            os.mkdir(path)
            logger.info(f"Created directory: {path}")

        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            os.remove(file_path)
            logger.info(f"Removed file: {file_path}")

        logger.info(colored(f"Cleaned {path} directory", "green"))
    except Exception as e:
        logger.error(f"Error occurred while cleaning directory {path}: {str(e)}")

def check_env_vars() -> None:
    """
    Checks if the necessary environment variables are set.

    Returns:
        None

    Raises:
        SystemExit: If any required environment variables are missing.
    """
    try:
        required_vars = ["PEXELS_API_KEY", "TIKTOK_SESSION_ID"]
        missing_vars = [var + os.getenv(var)  for var in required_vars if os.getenv(var) is None or (len(os.getenv(var)) == 0)]  

        if missing_vars:
            missing_vars_str = ", ".join(missing_vars)
            logger.error(colored(f"The following environment variables are missing: {missing_vars_str}", "red"))
            logger.error(colored("Please consult 'EnvironmentVariables.md' for instructions on how to set them.", "yellow"))
            sys.exit(1)  # Aborts the program
    except Exception as e:
        logger.error(f"Error occurred while checking environment variables: {str(e)}")
        sys.exit(1)  # Aborts the program if an unexpected error occurs

# This function is used to download trending music from the Scraptik API
# https://rapidapi.com/scraptik-api-scraptik-api-default/api/scraptik

# Function to fetch music list
def fetch_music_list(api_url, headers):
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        return data.get("music_list", [])
    except Exception as e:
        print(f"Error fetching music list: {e}")
        return []

# Function to download a song
def download_songs(play_url, song_title, output_dir="downloads"):
    try:
        response = requests.get(play_url, stream=True)
        response.raise_for_status()
        os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist
        file_path = os.path.join(output_dir, f"{song_title}.mp3")
        
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Downloaded: {file_path}")
    except Exception as e:
        print(f"Error downloading {song_title}: {e}")