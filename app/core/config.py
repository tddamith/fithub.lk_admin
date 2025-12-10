from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_DB_URL")
        self.MONGO_DB = os.getenv("MONGO_DB_NAME")
        # self.ADV_MONGO_DB = os.getenv("ADV_MONGO_DB_NAME")

        if not isinstance(self.MONGO_URI, str) or not self.MONGO_URI.strip():
            raise ValueError("Environment variable 'MONGO_DATABASE_URL' is missing or not set correctly.")

        if not isinstance(self.MONGO_DB, str) or not self.MONGO_DB.strip():
            raise ValueError("Environment variable 'MONGO_DB_NAME' is missing or not set correctly.")

    # mysql_host = os.getenv("MYSQL_HOST")
    # mysql_port = int(os.getenv("MYSQL_PORT"))
    # mysql_user = os.getenv("MYSQL_USER")
    # mysql_password = os.getenv("MYSQL_PASSWORD")
    # mysql_db = os.getenv("MYSQL_DB")
    # insight_api = os.getenv("INSIGHT_API_BASE_URL")

# Create a settings instance
settings = Settings()

# Simple test block
if __name__ == "__main__":
    # print("MONGO_DATABASE_URL =", settings.MONGO_URI)
    print("MONGO_DB_URL =", settings.MONGO_URI)
    print("MONGO_DB_NAME =", settings.MONGO_DB)
    # print("ADV_MONGO_DB_NAME =", settings.ADV_MONGO_DB)
