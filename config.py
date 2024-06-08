import os
from dotenv import load_dotenv



def load_configuration():
    load_dotenv()
    config = {
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'NVIDIA_API_KEY': os.getenv('NVIDIA_API_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'COMMIT_DIFF_DIRECTORY': 'commit_diff'
    }

    if config['NVIDIA_API_KEY'] is None:
        raise ValueError("Please set the NVIDIA_API_KEY environment variable.")

    return config