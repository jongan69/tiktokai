import os
import random
import logging

from typing import Optional
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from videogen.utils import download_songs, fetch_music_list  # Import the trendingMusic module
from termcolor import colored
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def choose_random_song(downloads_directory: str = "./downloads") -> Optional[str]:
    """
    Selects a random song from the downloads directory.
    If no songs exist, attempts to download trending songs.
    
    Args:
        downloads_directory (str): Path to the downloaded trending songs directory
        
    Returns:
        str: Path to the selected song file, or None if no songs found
    """
    try:
        # Create downloads directory if it doesn't exist
        os.makedirs(downloads_directory, exist_ok=True)
        
        # Get all audio files from downloads directory
        songs = [os.path.join(downloads_directory, f) for f in os.listdir(downloads_directory)
                if f.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg'))]
            
        # If no songs found, download trending songs
        if not songs:
            logger.info(colored("No songs found. Downloading trending songs...", "yellow"))
            api_url = "https://scraptik.p.rapidapi.com/discover-music?count=100"
            headers = {
                "x-rapidapi-host": "scraptik.p.rapidapi.com",
                "x-rapidapi-key": os.getenv("RAPID_API_KEY")
            }
            
            music_list = fetch_music_list(api_url, headers)
            for music in music_list:
                title = music.get("title", "Unknown_Title").replace(" ", "_")
                play_url = music.get("play_url", {}).get("uri")
                if play_url:
                    download_songs(play_url, title, downloads_directory)
            
            # Get updated list of songs
            songs = [os.path.join(downloads_directory, f) for f in os.listdir(downloads_directory)
                    if f.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg'))]
        
        if not songs:
            logger.warning(colored("No audio files found or downloaded", "yellow"))
            return None
            
        chosen_song = random.choice(songs)
        logger.info(colored(f"Chose song: {os.path.basename(chosen_song)}", "green"))
        return chosen_song
        
    except Exception as e:
        logger.error(colored(f"Error occurred while choosing random song: {str(e)}", "red"))
        return None

def add_background_music(
    video_path: str,
    output_path: str,
    song_path: Optional[str] = None,
    music_volume: float = 0.1,
    threads: int = 2
) -> str:
    """
    Adds background music to a video file.
    
    Args:
        video_path (str): Path to the input video file
        output_path (str): Path where the output video will be saved
        song_path (str, optional): Path to the music file. If None, will try to choose random song
        music_volume (float): Volume level for the background music (0.0 to 1.0)
        threads (int): Number of threads to use for processing
        
    Returns:
        str: Path to the output video file
    """
    try:
        logger.info(colored("Adding background music to video...", "magenta"))
        print(f"[+] Video path: {video_path}")
        print(f"[+] Output path: {output_path}")
        print(f"[+] Song path: {song_path}")
        print(f"[+] Music volume: {music_volume}")
        print(f"[+] Threads: {threads}")
        # Load the video
        video_clip = VideoFileClip(video_path)
        original_duration = video_clip.duration
        original_audio = video_clip.audio

        # If no song path provided, try to choose a random one
        if not song_path:
            song_path = choose_random_song()
            if not song_path:
                logger.warning(colored("No music available, returning original video", "yellow"))
                return video_path

        # Load and adjust the music
        song_clip = AudioFileClip(song_path)
        
        # Create a looped version of the audio if needed
        if song_clip.duration < original_duration:
            repeats = int(original_duration / song_clip.duration) + 1
            # Create a new concatenated audio clip
            repeated_segments = [song_clip] * repeats
            song_clip = CompositeAudioClip(repeated_segments)
        
        # Trim the music to match video duration
        song_clip = song_clip.subclip(0, original_duration)
        
        # Adjust volume and set audio properties
        song_clip = song_clip.volumex(music_volume).set_fps(44100)

        # Combine audio tracks
        if original_audio is not None:
            comp_audio = CompositeAudioClip([original_audio, song_clip])
        else:
            comp_audio = song_clip
        
        # Create final video
        final_video = video_clip.set_audio(comp_audio)
        final_video = final_video.set_fps(30)
        final_video = final_video.set_duration(original_duration)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the output file
        final_video.write_videofile(
            output_path,
            threads=threads,
            codec='libx264',
            audio_codec='aac'
        )
        
        logger.info(colored(f"Successfully added background music to: {output_path}", "green"))
        
        # Clean up
        video_clip.close()
        if original_audio is not None:
            original_audio.close()
        song_clip.close()
        final_video.close()
        
        return output_path
        
    except Exception as e:
        logger.error(colored(f"Error adding background music: {str(e)}", "red"))
        return video_path