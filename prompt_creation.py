import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process_prompt(user_prompt):
    # Read the content of system_prompt.md
    with open("system_prompt.md", "r") as f:
        system_prompt = f.read()

    user_prompt=f"Here's the current system prompt:\n\n{system_prompt}\n\nUser's new prompt: {user_prompt}\n\nPlease create a new system prompt that incorporates the user's request while maintaining the essential structure and purpose of the original prompt. Keep the json keys as they are."
    
    print(user_prompt)
    #Prepare the messages for the OpenAI API call
    messages = [
        {"role": "system", "content": "You are an AI assistant that helps create system prompts for image analysis tasks."},
        {"role": "user", "content": user_prompt}
    ]

    # Make the API call
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=3000
    )

    # Extract the new system prompt from the response
    new_system_prompt = response.choices[0].message.content

    # Create a new folder for storing timestamped prompts
    prompts_folder = "timestamped_prompts"
    os.makedirs(prompts_folder, exist_ok=True)

    # Generate a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save the new system prompt with a timestamp
    timestamped_filename = f"system_prompt_{timestamp}.md"
    timestamped_filepath = os.path.join(prompts_folder, timestamped_filename)
    with open(timestamped_filepath, "w") as f:
        f.write(new_system_prompt)

    return timestamped_filepath
