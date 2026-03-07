from os import getenv

import yaml

OPTIMISER_FREQUENCY_IN_USER_MESSAGES = int(
    getenv("OPTIMISER_FREQUENCY_IN_USER_MESSAGES") or "5"
)
assert OPTIMISER_FREQUENCY_IN_USER_MESSAGES >= 3

POSTGRES_USER = str(getenv("POSTGRES_USER"))
POSTGRES_PASSWORD = str(getenv("POSTGRES_PASSWORD"))
POSTGRES_DB = str(getenv("POSTGRES_DB"))

POSTGRES_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5464/{POSTGRES_DB}"
)
POSTGRES_SQLACADEMY_URL = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5464/{POSTGRES_DB}"

with open("backends.yaml", "r") as f:
    backends_config = yaml.safe_load(f)
    LLM_CONFIG = backends_config["llm_backends"]
    VLM_CONFIG = backends_config["vlm_backends"]
