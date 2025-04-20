import os
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()  # Esto carga las variables del archivo .env

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'dbname': os.getenv('DB_NAME', 'ecommerce'),
    'cursor_factory': psycopg2.extras.RealDictCursor
}
