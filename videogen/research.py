import os
import requests
from dotenv import load_dotenv
import re

load_dotenv()   

def clean_text(text: str) -> str:
    """
    Cleans text and extracts factual statements.
    Returns only complete, verifiable fact-like sentences.
    """
    # Define sentence ending punctuation
    endings = ('.', '!', '?')
    
    # Remove common artifacts and normalize text
    text = text.replace('·', '')
    text = text.replace('...', '.')
    text = text.replace('such as.', '')
    text = text.replace('\n', ' ')
    
    # Remove marketing/promotional language and subjective phrases
    promotional_phrases = [
        r'contact us',
        r'learn more',
        r'find out',
        r'perfect for',
        r'best',
        r'worst',
    ]
    for phrase in promotional_phrases:
        text = re.sub(phrase, '', text, flags=re.IGNORECASE)
    
    # Clean up formatting
    text = re.sub(r'\d+\.\s*', '', text)
    text = re.sub(r'Benefit \d+:', '', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\.+', '.', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', text) if s.strip()]
    
    # Clean and filter sentences
    clean_sentences = []
    seen_sentences = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Basic filtering for incomplete sentences
        if (not sentence or 
            len(sentence) < 15 or                    # Reduced minimum length
            not re.search(r'^[A-Z]', sentence) or
            not any(sentence.endswith(end) for end in endings)
        ):
            continue
            
        # Skip obvious promotional or subjective content
        if re.search(r'\b(amazing|awesome|excellent|great|wonderful|terrible)\b', sentence, re.IGNORECASE):
            continue
            
        words = sentence.split()
        if (len(words) < 4 or                       # Reduced minimum words
            words[0].lower() in {'and', 'or', 'but', 'nor', 'yet', 'so'} or
            re.search(r'[:;]$', sentence)
        ):
            continue
            
        # Skip duplicate content
        sentence_lower = sentence.lower()
        if sentence_lower in seen_sentences:
            continue
            
        # Accept sentences with either numbers/units OR specific keywords
        if (re.search(r'\b(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|percent|kg|kw|watts?)\b', sentence, re.IGNORECASE) or
            re.search(r'\b(solar panels?|electricity|energy|power|carbon|emissions?|climate|environment|technology|efficiency)\b', sentence, re.IGNORECASE)):
            seen_sentences.add(sentence_lower)
            clean_sentences.append(sentence)
    
    return ' '.join(clean_sentences)

def google_search(topic: str, num_results: int = 10) -> str:
    """
    Searches Google for a topic using Custom Search API.
    Args:
        topic (str): The topic to search for.
        num_results (int): The number of results to extract (max 10 for free tier).
    Returns:
        str: A combined string of complete, well-formatted sentences about the topic.
    """
    def try_search(search_query: str) -> str:
        try:
            # Get API credentials from environment variables
            api_key = os.getenv("GOOGLE_API_KEY")
            cx = os.getenv("GOOGLE_CX")
            
            if not api_key or not cx:
                return "Error: GOOGLE_API_KEY or GOOGLE_CX not found in environment variables."

            # Construct the Google Custom Search API URL
            base_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": cx,
                "q": search_query,
                "num": min(num_results, 10)  # Free tier allows max 10 results
            }

            print(f"[DEBUG] Searching for: {search_query}")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get("items", [])
            
            # Combine all snippets and clean them
            all_snippets = []
            for result in search_results:
                snippet = result.get("snippet", "").strip()
                if snippet:
                    all_snippets.append(snippet)
            
            # Join all snippets and clean once
            combined_text = ' '.join(all_snippets)
            final_text = clean_text(combined_text)
            
            # Final cleanup to ensure good formatting
            final_text = re.sub(r'\s+', ' ', final_text)    # Remove extra spaces
            final_text = re.sub(r'\.+', '.', final_text)    # Remove multiple periods
            final_text = re.sub(r'\s+([.!?])', r'\1', final_text)  # Fix space before punctuation
            final_text = re.sub(r'([.!?])(?=[A-Z])', r'\1 ', final_text)  # Ensure space after punctuation
            
            return final_text

        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Network error: {str(e)}")
            return f"A network error occurred: {e}"
        except Exception as e:
            print(f"[DEBUG] Error occurred: {str(e)}")
            return f"An error occurred during the search: {e}"

    # Try the original search first
    result = try_search(topic)
    
    # If no meaningful results, try with key phrases
    if not result or result.startswith("No results found") or result.startswith("An error occurred"):
        # Extract key phrases (words of 4+ characters)
        key_phrases = [word for word in topic.split() if len(word) >= 4]
        if key_phrases:
            # Try searching with just the key phrases
            alternative_query = " ".join(key_phrases)
            result = try_search(alternative_query)
    
    return result if result else "No results found."

# Example usage
# if __name__ == "__main__":
#     topic = "Benefits of solar energy"
#     result_text = google_search(topic, num_results=5)
#     print(f"\nInformation about {topic}:\n{result_text}")
