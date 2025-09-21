import os

DATABASE_URL =  os.getenv("DATABASE_URL", "sqlite:///./bugtracker.db")
API_URL = os.getenv("API_URL")  # if set later, CLI can call the API by HTTP