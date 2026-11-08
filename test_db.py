from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("PostgreSQL connection successful!")
        print(result.fetchone()[0])

except Exception as error:
    print("Database connection failed:")
    print(error)