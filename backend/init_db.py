import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app.database.session import engine
from app.models.meeting import Base

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created.")
