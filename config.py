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


COMMIT_MESSAGES_LOG_FILE = "commit_messages.log"
GENERATED_MESSAGES_LOG_FILE = "generated_messages.log"
MAX_CONCURRENT_REQUESTS = 4  # Adjust this value based on Ollama's capacity
IGNORED_SECTION_PATTERNS = {
    r'venv.*',  # Ignore any path containing 'venv'
    r'.idea.*'  # Ignore any path containing '.idea'
    r'node_modules.*',  # Ignore any path containing 'node_modules'
    r'__pycache__.*',  # Ignore any path containing '__pycache__
}
IGNORED_LINE_PATTERNS = {
    r'.*\.(png|jpg|jpeg|gif|bmp|tiff|svg|ico|raw|psd|ai)$',
    r'.*\.(xlsx|xls|docx|pptx|pdf)$', r'.*\.(pack|idx|DS_Store|sys|ini|bat|plist)$',
    r'.*\.(exe|dll|so|bin)$', r'.*\.(zip|rar|7z|tar|gz|bz2)$',
    r'.*\.(mp3|wav|aac|flac)$', r'.*\.(mp4|avi|mov|wmv|flv)$',
    r'.*\.(db|sqlitedb|mdb)$', r'.*\.(ttf|otf|woff|woff2)$',
    r'.*\.(tmp|temp|swp|swo)$', r'.*\.(o|obj|pyc|class)$',
    r'.*\.(cer|pem|crt|key)$', r'.*\.(conf|cfg|config)$',
    r'.*\.(env)$', r'node_modules', r'.*\.(pyo)$',
    r'(package-lock\.json|poetry\.lock|yarn\.lock|Gemfile\.lock)',
    r'.*\.(err|stderr|stdout|log)$', r'.*\.(cache|cached)$'
}
