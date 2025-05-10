import os
import json
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    config_path = os.getenv('CONFIG_PATH', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config