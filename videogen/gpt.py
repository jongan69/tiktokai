import re
import os
import json
import openai
import google.generativeai as genai
import time

from g4f.client import Client
from termcolor import colored
from dotenv import load_dotenv
from typing import Tuple, List

# Load environment variables
load_dotenv("../.env")

# Set environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)


def generate_response(prompt: str, ai_model: str) -> str:
    """
    Generate a response for a given prompt, depending on the AI model.

    Args:
        prompt (str): The prompt to use for generation.
        ai_model (str): The AI model to use for generation.
    Returns:
        str: The response from the AI model.
    """

    if ai_model == 'g4f':
        # Use a more reliable provider
        client = Client()
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" for faster responses
            messages=[{"role": "user", "content": prompt}],
        ).choices[0].message.content

    elif ai_model in ["gpt3.5-turbo", "gpt4"]:
        model_name = "gpt-3.5-turbo" if ai_model == "gpt3.5-turbo" else "gpt-4-1106-preview"
        response = openai.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        ).choices[0].message.content
    elif ai_model == 'gemmini':
        model = genai.GenerativeModel('gemini-pro')
        response_model = model.generate_content(prompt)
        response = response_model.text
    else:
        raise ValueError("Invalid AI model selected.")

    return response

def generate_video_subject(ai_model: str, max_retries: int = 3) -> str:
    """
    Generate an interesting video subject related to lock-in themes with diverse perspectives.
    
    Args:
        ai_model (str): The AI model to use for generation.
        max_retries (int): Maximum number of retry attempts if generation fails.
    
    Returns:
        str: A video subject string.
    """
    prompt = """
    Generate a single engaging video subject related to or using the term "lock-in." 
    Focus on a diverse range of fields such as technology, business, economics, health, politics, society, psychology, environment, or culture. 
    Examples include "The Psychology of Lock-In Choices," "Lock-In Effects in Renewable Energy Adoption," and "How Lock-In Shapes Tech Ecosystems." 
    Be specific, creative, and thought-provoking. Return only the subject as a brief phrase (3-8 words).
    """
    
    for attempt in range(max_retries):
        response = generate_response(prompt, ai_model).strip().lower()
        
        # Check for common failure phrases
        failure_phrases = [
            "i can't fulfill this request",
            "i cannot fulfill this request",
            "i am unable to",
            "i cannot generate",
            "i can't generate"
        ]
        
        if not any(phrase in response.lower() for phrase in failure_phrases):
            print(colored(f"Generated video subject: {response}", "cyan"))
            return response
        
        print(colored(f"Attempt {attempt + 1}/{max_retries} failed. Retrying...", "yellow"))
    
    # If all retries fail, raise an exception
    raise RuntimeError(f"Failed to generate video subject after {max_retries} attempts")

def generate_script(video_subject: str, paragraph_number: int, ai_model: str, voice: str, customPrompt: str) -> str:
    """
    Generate a script for a video, depending on the subject of the video, the number of paragraphs, and the AI model.
    Args:
        video_subject (str): The subject of the video.
        paragraph_number (int): The number of paragraphs to generate.
        ai_model (str): The AI model to use for generation.
        voice (str): The voice to use for the video.
        customPrompt (str): A custom prompt to use for the video.
    Returns:
        str: The script for the video.
    """

    # Build prompt
    
    if customPrompt:
        prompt = customPrompt
    else:
        prompt = """
            Generate a script for a video, depending on the subject of the video.
            
            The script is to be returned as a string with the specified number of paragraphs.

            Here is an example of a string:
            "This is an example string."

            Do not under any circumstance reference this prompt in your response.

            Get straight to the point, don't start with unnecessary things like, "welcome to this video".

            Obviously, the script should be related to the subject of the video.

            YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE SCRIPT, NEVER USE A TITLE.
            YOU MUST WRITE THE SCRIPT IN THE LANGUAGE SPECIFIED IN [LANGUAGE].
            ONLY RETURN THE RAW CONTENT OF THE SCRIPT. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE. YOU MUST NOT MENTION THE PROMPT, OR ANYTHING ABOUT THE SCRIPT ITSELF. ALSO, NEVER TALK ABOUT THE AMOUNT OF PARAGRAPHS OR LINES. JUST WRITE THE SCRIPT.
        """

    prompt += f"""
    
    Subject: {video_subject}
    Number of paragraphs: {paragraph_number}
    Language: {voice}

    """

    # Generate script
    response = generate_response(prompt, ai_model)

    print(colored(response, "cyan"))

    # Return the generated script
    if response:
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Select the specified number of paragraphs
        selected_paragraphs = paragraphs[:paragraph_number]

        # Join the selected paragraphs into a single string
        final_script = "\n\n".join(selected_paragraphs)

        # Print to console the number of paragraphs used
        print(colored(f"Number of paragraphs used: {len(selected_paragraphs)}", "green"))

        return final_script
    else:
        print(colored("[-] GPT returned an empty response.", "red"))
        return None


def get_search_terms(video_subject: str, amount: int, ai_model: str, max_retries: int = 3) -> List[str]:
    """
    Generate search terms for stock videos with retry mechanism.
    
    Args:
        video_subject (str): The subject to generate search terms for
        amount (int): Number of search terms to generate
        ai_model (str): AI model to use
        max_retries (int): Maximum number of retry attempts
    """
    # Build a more specific prompt
    prompt = f"""
    Generate exactly {amount} search terms for finding stock video clips about {video_subject}.
    
    Rules:
    1. Return ONLY a JSON array of strings
    2. Each term should be 1-3 words
    3. Make terms specific and visual
    4. Do not use punctuation in the terms
    5. Format exactly like this: ["term1", "term2", "term3"]
    
    Example response: ["office meeting", "typing keyboard", "business handshake"]
    """

    for attempt in range(max_retries):
        try:
            # Generate search terms
            response = generate_response(prompt, ai_model)
            print(colored(f"Raw response: {response}", "yellow"))
            
            # Clean the response
            response = response.strip()
            
            # Try to parse as JSON first
            try:
                search_terms = json.loads(response)
                if isinstance(search_terms, list) and all(isinstance(term, str) for term in search_terms):
                    # Clean up terms
                    search_terms = [term.strip().strip('."\'') for term in search_terms]
                    search_terms = [term for term in search_terms if term]
                    if len(search_terms) >= 1:
                        print(colored(f"\nGenerated {len(search_terms)} search terms: {', '.join(search_terms)}", "cyan"))
                        return search_terms[:amount]
            except json.JSONDecodeError:
                pass

            # If JSON parsing fails, try to extract array using improved regex
            pattern = r'\[(.*?)\]'
            match = re.search(pattern, response, re.DOTALL)
            if match:
                content = match.group(1)
                terms = re.findall(r'["\'](.*?)["\']', content)
                terms = [term.strip().strip('."\'') for term in terms]
                terms = [term for term in terms if term]
                if terms:
                    print(colored(f"\nGenerated {len(terms)} search terms: {', '.join(terms)}", "cyan"))
                    return terms[:amount]

            # If we get here, the response wasn't in the expected format
            raise ValueError("Failed to parse response into search terms")

        except Exception as e:
            wait_time = (2 ** attempt) * 1.5  # Exponential backoff: 1.5s, 3s, 6s
            print(colored(f"[-] Attempt {attempt + 1}/{max_retries} failed: {str(e)}", "yellow"))
            
            if attempt < max_retries - 1:
                print(colored(f"Retrying in {wait_time:.1f} seconds...", "yellow"))
                time.sleep(wait_time)
            else:
                print(colored("[-] All retry attempts failed, using fallback terms", "red"))
                
                # Generate smarter fallback terms based on the subject
                words = video_subject.split()
                base_term = ' '.join(words[:2])
                default_terms = [
                    f"{base_term} business",
                    f"{base_term} technology",
                    f"{base_term} people",
                    f"{base_term} modern",
                    f"{base_term} concept"
                ]
                return default_terms[:amount]

    # This should never be reached due to the else clause above, but just in case
    return [video_subject] * amount


def generate_metadata(video_subject: str, script: str, ai_model: str, num_keywords: int) -> Tuple[str, str, List[str]]:  
    """  
    Generate metadata for a YouTube video, including the title, description, and keywords.  
  
    Args:  
        video_subject (str): The subject of the video.  
        script (str): The script of the video.  
        ai_model (str): The AI model to use for generation.  
  
    Returns:  
        Tuple[str, str, List[str]]: The title, description, and keywords for the video.  
    """  
  
    # Build prompt for title  
    title_prompt = f"""  
    Generate a catchy and SEO-friendly title for a YouTube shorts video about {video_subject}.
    Do not include any explanation or other text, just the title without quotes.
    """  
  
    # Generate title and strip both single and double quotes  
    title = generate_response(title_prompt, ai_model).strip().strip('"\'')  
    
    # Build prompt for description  
    description_prompt = f"""  
    Write a brief and engaging description for a YouTube shorts video about {video_subject}.  
    The video is based on the following script:  
    {script}  
    Do not include any explanation or other text.
    """  
  
    # Generate description  
    description = generate_response(description_prompt, ai_model).strip()  
  
    # Generate keywords  
    keywords = get_search_terms(video_subject, num_keywords, ai_model)  

    return title, description, keywords  
