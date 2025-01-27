from openai import OpenAI
import google.generativeai as genai
from PIL import Image
import logging
import time
import socket
from contextlib import closing
filename_perp="/home/nav/Projects/Perp_API_key.txt"
filename_gemini="/home/nav/Projects/Gem_API_key.txt"

# Configure logging before any other initialization
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_api_key(filename: str) -> str:
    """Load API key from a file"""
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"API key file {filename} not found")
        raise
    except Exception as e:
        logger.error(f"Error reading API key: {str(e)}")
        raise

 # Load API key from file
PERP_API_KEY = load_api_key(filename_perp)
GEM_API_KEY = load_api_key(filename_gemini)

def check_network():
    """Check if we can connect to Google's servers"""
    try:
        with closing(socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=5)):
            return True
    except:
        return False

def init_genai():
    """Initialize Gemini API with proper error handling"""
    try:
        if not check_network():
            raise ConnectionError("No network connectivity to Google API servers")
        
        genai.configure(api_key=GEM_API_KEY)
        # Test connection with a simple request
        genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {str(e)}")
        return False

    
def web_search(prompt) -> str:
    """Search the web using Perplexity's sonar-pro model"""
    try:
        client = OpenAI(api_key=PERP_API_KEY, base_url="https://api.perplexity.ai")
        
      
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        if response and response.choices:
            return response.choices[0].message.content
        return "No search results found"
        
    except Exception as e:
        logger.error(f"Web search failed: {str(e)}")
        return f"Error performing web search: {str(e)}"
        
def describe_image(image_path: str, max_retries: int = 3) -> str:
    """Generate image description using Gemini 1.5 Flash."""
    if not init_genai():
        return "Failed to initialize API connection"
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to process image")
            
            # Load and prepare image
            image = Image.open(image_path)
            
            # Initialize model with safety settings
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
            )
            
            # Initial analysis
            response = model.generate_content(
                contents=[image, "Analyse the object in the image. Ignore the background and focus on the object. Display the brand of the object along with its model name in the following format: 'Brand Model'"],
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 250,
                    "top_p": 0.8,
                    "top_k": 40
                }
            )
            
            if not response:
                raise ValueError("No response received from model")
                
            response.resolve()
            initial_description = response.text if response.text else "No description generated"
            print("\nItem in the photo:")
            print(initial_description)
            
            # Get user confirmation of object identification
            print("\nIs this identification correct? (yes/no)")
            user_confirmation = input().lower()

            if user_confirmation == 'yes':
                current_description = initial_description
            else:
                print("Please provide the correct item description:")
                current_description = input().strip()

            prompt = f"""
                Based on this item description: {current_description}
                1. Do an internet search and find its current price.
                2. Summarize user reviews and ratings
                3. Then continue to be a friendly AI agent that accesses the web as required.
                """
            # Search the web for more details
            perplexity_result = web_search(prompt)
            print("\nItem details:")
            print(perplexity_result)

            while True:
                # Get user feedback
                user_prompt = input("\nEnter feedback (or type 'exit' to finish): ")
                
                if user_prompt.lower() == 'exit':
                    return perplexity_result
                
                if user_prompt.strip():
                    # Search web again with updated information
                    updated_result = web_search(f"{current_description} {user_prompt}")
                    print("\nUpdated Item Details:")
                    print(updated_result)
                    perplexity_result = updated_result
                    
        except Exception as e:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                return f"Error processing image after {max_retries} attempts: {str(e)}"