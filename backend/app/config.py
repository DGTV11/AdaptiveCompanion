from os import getenv, path

import yaml

SECRET_KEY = str(getenv("SECRET_KEY"))
ALGORITHM = str(getenv("ALGORITHM") or "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "75")
MAX_USERS = int(getenv("MAX_USERS") or "1")

OPTIMISER_FREQUENCY_IN_USER_MESSAGES = int(
    getenv("OPTIMISER_FREQUENCY_IN_USER_MESSAGES") or "5"
)
assert OPTIMISER_FREQUENCY_IN_USER_MESSAGES >= 3

POSTGRES_USER = str(getenv("POSTGRES_USER"))
POSTGRES_PASSWORD = str(getenv("POSTGRES_PASSWORD"))
POSTGRES_DB = str(getenv("POSTGRES_DB"))

POSTGRES_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5554/{POSTGRES_DB}"
)
POSTGRES_SQLACADEMY_URL = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5554/{POSTGRES_DB}"

# backends_config_path = path.join(path.dirname(path.dirname(__file__)), "backends.yaml")
# with open(backends_config_path, "r") as f:
with open("backends.yaml", "r") as f:
    backends_config = yaml.safe_load(f)
    LLM_CONFIG = backends_config["llm_backends"]
    VLM_CONFIG = backends_config["vlm_backends"]
