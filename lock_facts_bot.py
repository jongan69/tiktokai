import os
import time
import schedule
from datetime import datetime
from tiktok_uploader import tiktok
from tiktok_uploader.Config import Config
from videogen.research import google_search
from videogen.utils import clean_dir
from videogen.gpt import generate_script, generate_metadata, get_search_terms, generate_video_subject
from videogen.video import *
from videogen.search import *
from videogen.tiktokvoice import tts
from moviepy.editor import concatenate_audioclips, AudioFileClip
from uuid import uuid4
from dotenv import load_dotenv
from videogen.addMusic import add_background_music
import random

# Load environment variables
load_dotenv()

# Initialize Config
_ = Config.load("./config.txt")

# Constants
AMOUNT_OF_STOCK_VIDEOS = 20
VOICE_OPTIONS = {
    "English": [
        "en_us_001", "en_us_002", "en_us_006", "en_us_007", "en_us_009", "en_us_010",
        "en_uk_001", "en_uk_003", "en_au_001", "en_au_002"
    ],
    "Character": [
        "en_us_ghostface", "en_us_chewbacca", "en_us_c3po", "en_us_stitch",
        "en_us_stormtrooper", "en_us_rocket"
    ],
    "Specialty": [
        "en_male_narration", "en_male_funny", "en_female_emotional", "en_male_cody",
        "en_female_madam_leota", "en_male_ghosthost", "en_male_pirate"
    ]
}

AI_MODEL = "g4f"  # or "gpt-3.5-turbo" if you prefer
TIKTOK_USERNAME = os.getenv('TIKTOK_USERNAME')  # Add this to your .env file

# At the start of the script, add environment variable checking
required_env_vars = [
    'TIKTOK_USERNAME',
    'PEXELS_API_KEY',
]

for var in required_env_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Missing required environment variable: {var}")

def get_random_voice():
    """
    Randomly select a voice from the available options.
    Returns a tuple of (voice_id, voice_category)
    """
    # Select a random category (weighted to prefer English voices)
    weights = [0.7, 0.15, 0.15]  # 70% English, 15% Character, 15% Specialty
    category = random.choices(list(VOICE_OPTIONS.keys()), weights=weights)[0]
    
    # Select a random voice from that category
    voice = random.choice(VOICE_OPTIONS[category])
    
    return voice, category

def generate_lock_fact_video():
    try:
        print(f"[+] Starting video generation at {datetime.now()}")
        
        # Select random voice
        selected_voice, voice_category = get_random_voice()
        print(f"[+] Selected voice: {selected_voice} from category: {voice_category}")
        
        # Create and verify directories
        for dir_path in ["./temp", "./subtitles", "./output"]:
            os.makedirs(dir_path, exist_ok=True)
            print(f"[+] Directory verified: {os.path.abspath(dir_path)}")
        
        # Clean temporary directories - use consistent paths
        clean_dir("./temp")
        clean_dir("./subtitles")
        clean_dir("./output")
        print("[+] Directories cleaned")

        # Generate a video subject
        print("[+] Generating video subject...")
        video_subject = generate_video_subject(AI_MODEL)  # or any other supported model    
        print(f"[+] Video subject generated: {video_subject}")
        
        # Generate search terms for visuals
        print("[+] Generating search terms...")
        search_terms = get_search_terms(
            video_subject=video_subject,
            amount=AMOUNT_OF_STOCK_VIDEOS,
            ai_model=AI_MODEL
        )
        print(f"[+] Search terms generated: {search_terms}")
        
        # Generate script about lock facts
        subject_search = ""
        for search_term in search_terms:
            subject_search += google_search(search_term)
            print(f"[+] Subject search: {subject_search}")

        # Generate script about lock facts
        print("[+] Generating script...")
        custom_prompt = f"""Generate a script for a video based on the subject of {video_subject} using the following research: {subject_search}. The script is to be returned as a string with the specified number of paragraphs. The script must stay on topic, delivering concise, engaging, and informative content directly related to the concept of {video_subject}. Avoid all unnecessary introductions, and get straight to the core of the subject matter using the research for factual context. Write the script entirely in English and return only the raw content. Do not include any type of formatting, markdown, or explanatory indicators like "Voiceover" or "Narrator." Never reference this prompt or any instructions within the script. End every script with "ITS TIME TO LOCKIN" """
        
        # Try to generate a valid script, with retries
        max_retries = 3
        retry_count = 0
        script = None
        
        while retry_count < max_retries:
            try:
                # Try primary model
                script = generate_script(
                    video_subject, 
                    paragraph_number=1, 
                    ai_model=AI_MODEL,
                    voice=selected_voice,
                    customPrompt=custom_prompt
                )
                
                # Check if script is valid
                if script and len(script) > 50 and not any(invalid in script.lower() for invalid in [
                    "I can't fulfill this request. If you have any feedback I can pass it on to my developers.", 
                    "i cannot fulfill",
                    "i am unable",
                    "error",
                    "feedback",
                    "developers"
                ]):
                    print(f"[+] Valid script generated: {script[:100]}...")
                    break
                
                print(f"[-] Invalid script generated, retrying... (Attempt {retry_count + 1}/{max_retries})")
                retry_count += 1
                
            except Exception as e:
                print(f"[-] Error with primary AI model: {e}")
                print("[+] Trying fallback model...")
                
                try:
                    script = generate_script(
                        video_subject, 
                        paragraph_number=1, 
                        ai_model="gpt-3.5-turbo",
                        voice=selected_voice,
                        customPrompt=custom_prompt
                    )
                    
                    # Check if fallback script is valid
                    if script and len(script) > 50 and not any(invalid in script.lower() for invalid in [
                        "I can't fulfill this request. If you have any feedback I can pass it on to my developers.", 
                        "I cannot fulfill",
                        "I am unable",
                        "error",
                        "feedback",
                        "developers"
                    ]):
                        print(f"[+] Valid script generated with fallback model: {script[:100]}...")
                        break
                        
                except Exception as e:
                    print(f"[-] Error with fallback model: {e}")
                
                retry_count += 1
        
        if not script or retry_count >= max_retries:
            raise Exception("Failed to generate a valid script after multiple attempts")

        # Search and download videos
        video_urls = []
        print("[+] Searching for stock videos...")
        for search_term in search_terms:
            found_urls = search_for_stock_videos(
                search_term,
                os.getenv("PEXELS_API_KEY"),
                it=10,
                min_dur=5
            )
            for url in found_urls:
                if url not in video_urls:
                    video_urls.append(url)
                    print(f"[+] Found video URL: {url}")
                    break

        # Download videos
        video_paths = []
        print("[+] Downloading videos...")
        for video_url in video_urls:
            try:
                saved_video_path = save_video(video_url, directory="./temp")
                video_paths.append(saved_video_path)
                print(f"[+] Video saved to: {os.path.abspath(saved_video_path)}")
            except Exception as e:
                print(f"[-] Error downloading video: {e}")

        # Generate TTS for every sentence
        print("[+] Generating TTS...")
        sentences = script.split(". ")
        sentences = list(filter(lambda x: x != "", sentences))
        paths = []

        # Generate TTS for every sentence
        for sentence in sentences:
            current_tts_path = f"./temp/{uuid4()}.mp3"
            try:
                tts(sentence, selected_voice, filename=current_tts_path)
                audio_clip = AudioFileClip(current_tts_path)
                paths.append(audio_clip)
                print(f"[+] Generated TTS for: {sentence[:50]}...")
            except Exception as e:
                print(f"[-] Error generating TTS for sentence: {e}")
                continue

        # Combine all TTS files using moviepy
        print("[+] Combining audio clips...")
        final_audio = concatenate_audioclips(paths)
        tts_path = f"./temp/{uuid4()}.mp3"
        final_audio.write_audiofile(tts_path)
        print(f"[+] Combined audio saved to: {os.path.abspath(tts_path)}")

        try:
            print("[+] Generating subtitles...")
            subtitles_path = generate_subtitles(
                audio_path=tts_path,
                sentences=sentences,
                audio_clips=paths,
                voice=selected_voice[:2],
                directory="./subtitles"
            )
            print(f"[+] Subtitles saved to: {os.path.abspath(subtitles_path)}")
        except Exception as e:
            print(f"[-] Error generating subtitles: {e}")
            subtitles_path = None

        # Combine videos
        print("[+] Combining videos...")
        print(f"[+] Video paths to combine: {video_paths}")
        temp_audio = AudioFileClip(tts_path)
        print(f"[+] Audio duration: {temp_audio.duration}")
        combined_video_path = combine_videos(video_paths, temp_audio.duration, 5, 2)
        print(f"[+] Combined video saved to: {os.path.abspath(combined_video_path)}")

        # Generate final video
        print("[+] Generating final video...")
        try:
            final_video_path = generate_video(
                combined_video_path, 
                tts_path, 
                subtitles_path, 
                2, 
                "center,center", 
                "#FFFFFF"
            )
            print(f"[+] Final video saved to: {os.path.abspath(final_video_path)}")
        except Exception as e:
            print(f"[-] Error generating final video: {e}")
            raise e

        # After generating final video
        try:
            print("[+] Adding background music...")
            final_video_path = add_background_music(
                video_path=final_video_path,
                output_path=f"./output/final_with_music_{uuid4()}.mp4",
                music_volume=0.1
            )
        except Exception as e:
            print(f"[-] Error adding background music: {e}")
            # Continue with original video if music addition fails

        # Generate metadata for TikTok
        print("[+] Generating metadata...")
        title, description, raw_keywords = generate_metadata(
            video_subject=video_subject,
            script=script,
            ai_model=AI_MODEL,
            num_keywords=6
        )
        # Convert keywords list to hashtag string
        keywords = ' '.join([f'#{keyword.strip()}' for keyword in raw_keywords])
        
        print(f"[+] Generated title: {title}")
        print(f"[+] Generated description: {description}")
        print(f"[+] Generated keywords: {keywords}")

        # Upload to TikTok
        print("[+] Uploading to TikTok...")
        print(f"[+] Using username: {TIKTOK_USERNAME}")
        print(f"[+] Video path: {os.path.abspath(final_video_path)}")
        success = tiktok.upload_video(
            TIKTOK_USERNAME,
            final_video_path,
            title,
            description,
            keywords,
            schedule_time=0,
            allow_comment=1,
            allow_duet=0,
            allow_stitch=0,
            visibility_type=0
        )

        if success:
            print(f"[+] Successfully uploaded video at {datetime.now()}")
        else:
            print(f"[-] Failed to upload video at {datetime.now()}")

        # Clean up
        print("[+] Cleaning up...")
        clean_dir("./temp")
        clean_dir("./subtitles")
        print("[+] Cleanup complete")

    except Exception as e:
        print(f"[-] Error in video generation/upload process: {e}")
        print(f"[-] Error type: {type(e)}")
        print(f"[-] Error traceback:")
        import traceback
        traceback.print_exc()

def main():
    print("[+] Starting Lock Facts TikTok Bot")
    
    # Schedule the job to run every hour
    schedule.every().hour.at(":00").do(generate_lock_fact_video)
    
    # Run immediately on start
    generate_lock_fact_video()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 