from database_manager import DatabaseManager
import os

def init_database():
    """Initialize the database with tables and default data."""
    # Remove existing database if it exists
    if os.path.exists("Fusion.db"):
        try:
            os.remove("Fusion.db")
            print("Removed existing database")
        except Exception as e:
            print(f"Error removing database: {e}")
            return False
    
    try:
        # Create new database
        db = DatabaseManager()
        
        # Create default chapter
        db.execute_query(
            "INSERT INTO chapters_flashcards (chap_name) VALUES (?)",
            ("General",),
            commit=True
        )
        
        print("Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    init_database() 