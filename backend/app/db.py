from os import path
from typing import Any, List, Optional, Tuple, Union

# import chromadb
import orjson
import psycopg
from config import POSTGRES_URL
from psycopg.types.json import set_json_dumps, set_json_loads
from psycopg_pool import ConnectionPool

pool = ConnectionPool(POSTGRES_URL)


# *Helper functions
def write(query: str, values: Optional[Tuple[Any, ...]] = None) -> None:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
        conn.commit()


def read(
    query: str, values: Optional[Tuple[Any, ...]] = None
) -> List[Tuple[Any, ...]]:  # values can be tuple
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, values)
            return cur.fetchall()


# create_chromadb_client = lambda: chromadb.HttpClient(
#     # host="localhost",
#     host="chroma",
#     port=8000,
#     settings=chromadb.config.Settings(anonymized_telemetry=False),
# )

# *Init DB


def orjson_dumps_str(*args) -> str:
    return orjson.dumps(*args).decode("utf-8")


set_json_dumps(orjson_dumps_str)
set_json_loads(orjson.loads)

write(
    # "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
    'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
)

## *Users
write(
    """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_v4(),
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        username TEXT NOT NULL,
        hashed_password TEXT NOT NULL
    );
    """,
)

## *Agents
write(
    """
    CREATE TABLE IF NOT EXISTS agents (
        id UUID PRIMARY KEY NOT NULL,
        user_id UUID NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_user_message_time TIMESTAMP DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """,
)

## *Core Personality
write(
    """
    CREATE TABLE IF NOT EXISTS core_personality (
        id UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_v4(),
        agent_id UUID NOT NULL,
        name TEXT NOT NULL,
        likes TEXT NOT NULL,
        dislikes TEXT NOT NULL,
        desires TEXT NOT NULL,
        mode_of_communication TEXT NOT NULL,
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
    );
    """
)

## *Mutable Personality
write(
    """
    CREATE TABLE IF NOT EXISTS previous_mutable_personality (
        id UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_v4(),
        agent_id UUID NOT NULL,
        humanlikeness SMALLINT DEFAULT NULL,
        affection SMALLINT DEFAULT NULL,
        warmth SMALLINT DEFAULT NULL,
        enthusiasm SMALLINT DEFAULT NULL,
        impulsiveness SMALLINT DEFAULT NULL,
        curiosity SMALLINT DEFAULT NULL,
        quirkiness SMALLINT DEFAULT NULL,
        shyness SMALLINT DEFAULT NULL,
        nerdiness SMALLINT DEFAULT NULL,
        cuteness SMALLINT DEFAULT NULL,
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
    );
    """
)

write(
    """
    CREATE TABLE IF NOT EXISTS current_mutable_personality (
        id UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_v4(),
        agent_id UUID NOT NULL,
        humanlikeness SMALLINT NOT NULL,
        affection SMALLINT NOT NULL,
        warmth SMALLINT NOT NULL,
        enthusiasm SMALLINT NOT NULL,
        impulsiveness SMALLINT NOT NULL,
        curiosity SMALLINT NOT NULL,
        quirkiness SMALLINT NOT NULL,
        shyness SMALLINT NOT NULL,
        nerdiness SMALLINT NOT NULL,
        cuteness SMALLINT NOT NULL,
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
    );
    """
)

## *Auxiliary Memory
write(
    """
    CREATE TABLE IF NOT EXISTS auxiliary_memory (
        id UUID PRIMARY KEY NOT NULL DEFAULT uuid_generate_v4(),
        agent_id UUID NOT NULL,
        user_memory TEXT NOT NULL,
        scratchpad TEXT NOT NULL,
        interaction_summary TEXT NOT NULL,
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
    );
    """
)
