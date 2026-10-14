import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_effective_config(sets):
    # Layer 1: defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    # Layer 2: YAML file
    base_dir = Path(__file__).parent
    with open(base_dir / "config.development.yaml", encoding="utf-8") as f:
        config.update(yaml.safe_load(f) or {})

    # Layer 3: .env file, read separately
    env_file = dotenv_values(base_dir / ".env")

    if env_file.get("APP_PORT") is not None:
        config["port"] = env_file["APP_PORT"]

    if env_file.get("NUM_WORKERS") is not None:
        config["workers"] = env_file["NUM_WORKERS"]

    if env_file.get("APP_API_KEY") is not None:
        config["api_key"] = env_file["APP_API_KEY"]

    # Layer 4: actual OS environment variables
    if os.environ.get("APP_PORT") is not None:
        config["port"] = os.environ["APP_PORT"]

    if os.environ.get("APP_WORKERS") is not None:
        config["workers"] = os.environ["APP_WORKERS"]

    if os.environ.get("APP_API_KEY") is not None:
        config["api_key"] = os.environ["APP_API_KEY"]

    # Layer 5: CLI overrides supplied in the URL
    for item in sets:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        key = key.strip().lower()

        if key in config:
            config[key] = value

    # Convert to the required types
    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])

    config["debug"] = str(config["debug"]).strip().lower() in {
        "true", "1", "yes", "on"
    }

    config["log_level"] = str(config["log_level"])
    config["api_key"] = "****"

    return config


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    return get_effective_config(set)


@app.get("/")
def home():
    return {"message": "Configuration API is running"}
