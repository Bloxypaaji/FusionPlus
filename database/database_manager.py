import sqlite3
import os
import threading
from datetime import datetime


class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    _connection = None
    
    def __new__(cls, db_name="Fusion.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._db_name = db_name
                    cls._instance._init_connection()
        return cls._instance
    
    def _init_connection(self):
        """Initialize the database connection."""
        db_exists = os.path.exists(self._db_name)
        try:
            self._connection = sqlite3.connect(self._db_name, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            if not db_exists:
                self.create_tables()
            else:
                self.update_schema()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise
    
    def _ensure_connection(self):
        """Ensure database connection is active."""
        try:
            # Test the connection
            self._connection.execute("SELECT 1")
        except (sqlite3.Error, AttributeError):
            # Reconnect if the connection is dead
            self._init_connection()
    
    def _execute(self, query, params=(), commit=False):
        """Execute a query with proper locking and connection management."""
        with self._lock:
            try:
                self._ensure_connection()
                cursor = self._connection.cursor()
                cursor.execute(query, params)
                if commit:
                    self._connection.commit()
                return cursor
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                self._connection.rollback()
                raise

    def execute_query(self, query, params=(), fetch_one=False, fetch_all=False, commit=False):
        """Execute a query and return results based on parameters.
        
        Args:
            query (str): SQL query to execute
            params (tuple): Query parameters
            fetch_one (bool): If True, return one result
            fetch_all (bool): If True, return all results
            commit (bool): If True, commit the transaction
            
        Returns:
            Cursor results based on fetch parameters
        """
        try:
            cursor = self._execute(query, params, commit)
            
            if commit:
                self._connection.commit()
                return True
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            
            return cursor
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            if commit:
                self._connection.rollback()
            return None

    def update_schema(self):
        """Check and update database schema if necessary."""
        try:
            # Check if chapter column exists in flashcards table
            self._connection.execute("SELECT chapter FROM flashcards LIMIT 1")
        except sqlite3.OperationalError:
            # Add chapter column if it doesn't exist
            try:
                self._connection.execute("ALTER TABLE flashcards ADD COLUMN chapter TEXT NOT NULL DEFAULT 'General'")
                self._connection.commit()
                print("Added chapter column to flashcards table")
            except sqlite3.OperationalError as e:
                print(f"Error updating schema: {e}")
                # If table doesn't exist, create all tables
                self.create_tables()

    def create_tables(self):
        """Creates necessary tables for users, notes, tasks, and flashcards."""
        # Create users table
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # Create notes table with Color column
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Color TEXT DEFAULT (1, 1, 1, 1),  -- Default white color
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # Create tasks table
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                status TEXT CHECK(status IN ('Pending', 'Completed')) DEFAULT 'Pending',
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # Create flashcards table
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cards_name TEXT NOT NULL,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # Create expenses table with user_id foreign key
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exp_name TEXT NOT NULL,
                exp_type TEXT NOT NULL,
                exp_amount REAL NOT NULL,
                exp_date TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
            )
        """)
        self._connection.commit()
        
        # Ensure default user exists
        self.ensure_default_user()

    def ensure_default_user(self):
        """Ensure that a default user exists in the database."""
        try:
            cursor = self._connection.cursor()
            # Check if default user exists
            cursor.execute("SELECT id FROM users WHERE id = 1")
            if not cursor.fetchone():
                # Create default user
                cursor.execute(
                    "INSERT INTO users (id, username, password) VALUES (1, 'default_user', 'default_password')"
                )
                self._connection.commit()
                print("Created default user")
        except sqlite3.Error as e:
            print(f"Error ensuring default user: {e}")
            self._connection.rollback()

    # 🔹 **User Authentication**
    def register_user(self, username, password):
        """Registers a new user."""
        try:
            self._connection.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self._connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Username already exists

    def verify_user(self, username, password):
        """Checks if username & password match."""
        cursor = self._connection.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        return result[0] if result else None  # Return user_id if found

    # 🔹 **Notes Management**
    def add_note(self, user_id, title, content):
        """Adds a new note to the database."""
        self._connection.execute("""
            INSERT INTO notes (user_id, title, content) 
            VALUES (?, ?, ?)
        """, (user_id, title, content))
        self._connection.commit()

    def get_notes(self, user_id):
        """Retrieves all notes for a specific user."""
        cursor = self._connection.execute("""
            SELECT id, title, content 
            FROM notes 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        return cursor.fetchall()

    def delete_note(self, note_id):
        """Deletes a note from the database."""
        self._connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._connection.commit()

    def update_note(self, note_id, title, content):
        """Updates an existing note."""
        self._connection.execute("""
            UPDATE notes 
            SET title=?, content=? 
            WHERE id=?
        """, (title, content, note_id))
        self._connection.commit()

    def search_notes(self, user_id, keyword):
        """Searches notes containing the keyword."""
        cursor = self._connection.execute("""
            SELECT id, title, content 
            FROM notes 
            WHERE user_id = ? AND (title LIKE ? OR content LIKE ?) 
            ORDER BY created_at DESC
        """, (user_id, f"%{keyword}%", f"%{keyword}%"))
        return cursor.fetchall()

    # 🔹 **Task Management**
    def add_task(self, user_id, task):
        """Adds a new task and returns the task ID."""
        cursor = self._connection.execute("""
            INSERT INTO tasks (user_id, task) 
            VALUES (?, ?)
        """, (user_id, task))
        self._connection.commit()
        return cursor.lastrowid  # Return the ID of the newly created task

    def update_task_status(self, task_id, status):
        """Updates the status of a task ('Pending' or 'Completed')."""
        self._connection.execute("""
            UPDATE tasks 
            SET status=? 
            WHERE id=?
        """, (status, task_id))
        self._connection.commit()

    def delete_task(self, task_id):
        """Deletes a task by its ID."""
        self._connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._connection.commit()

    def get_tasks(self, user_id):
        """Fetch tasks for a specific user from the database."""
        cursor = self._connection.cursor()
        cursor.execute("SELECT id, task, status FROM tasks WHERE user_id=?", (user_id,))
        tasks = cursor.fetchall()
        return [{'id': task[0], 'task': task[1], 'status': task[2]} for task in tasks]

    # 🔹 **Flashcard Management**
    def add_flashcard(self, user_id, cards_name, front, back):
        """Add a new flashcard."""
        try:
            print(f"Adding flashcard: User ID={user_id}, Name={cards_name}, Front={front}, Back={back}")  # Debugging print
            self._execute("""
                INSERT INTO flashcards (user_id, cards_name, front, back)
                VALUES (?, ?, ?, ?)
            """, (user_id, cards_name, front, back), commit=True)
            print("Flashcard added successfully")  # Debugging print
            return True
        except sqlite3.Error as e:
            print(f"Error adding flashcard: {e}")
            return False

    def get_flashcards(self, user_id):
        """Get all flashcards grouped by cards_name."""
        try:
            cursor = self._execute("""
                SELECT cards_name, 
                       GROUP_CONCAT(id) as ids,
                       GROUP_CONCAT(front) as fronts,
                       GROUP_CONCAT(back) as backs
                FROM flashcards 
                WHERE user_id = ?
                GROUP BY cards_name
                ORDER BY cards_name
            """, (user_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting flashcards: {e}")
            return []

    def search_flashcards(self, user_id, keyword):
        """Search flashcards containing the keyword."""
        try:
            cursor = self._execute("""
                SELECT id, cards_name, front, back, created_at
                FROM flashcards 
                WHERE user_id = ? 
                AND (cards_name LIKE ? OR front LIKE ? OR back LIKE ?) 
                ORDER BY created_at DESC
            """, (user_id, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error searching flashcards: {e}")
            return []
        
    def get_all_cards_names(self):
        """Retrieve all unique card names from the flashcards."""
        try:
            cursor = self._execute("""
                SELECT DISTINCT cards_name 
                FROM flashcards
            """)
            return [row['cards_name'] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error retrieving card names: {e}")
            return []
    
    def delete_flashcard(self, flashcard_id):
        """Delete a flashcard by its ID."""
        try:
            self._execute("DELETE FROM flashcards WHERE id = ?", (flashcard_id,), commit=True)
            return True
        except sqlite3.Error as e:
            print(f"Error deleting flashcard: {e}")
            return False

    def update_flashcard(self, flashcard_id, cards_name, front, back):
        """Update an existing flashcard."""
        try:
            self._execute("""
                UPDATE flashcards 
                SET cards_name = ?, front = ?, back = ? 
                WHERE id = ?
            """, (cards_name, front, back, flashcard_id), commit=True)
            return True
        except sqlite3.Error as e:
            print(f"Error updating flashcard: {e}")
            return False

    def get_flashcard(self, flashcard_id):
        """Get a specific flashcard by ID."""
        try:
            cursor = self._execute("""
                SELECT id, cards_name, front, back 
                FROM flashcards 
                WHERE id = ?
            """, (flashcard_id,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error getting flashcard: {e}")
            return None

    def get_all_flashcards(self):
        """Get all flashcards from the database"""
        query = """
            SELECT id, cards_name, front, back 
            FROM flashcards 
            ORDER BY id DESC
        """
        return self.execute_query(query).fetchall()

    def get_flashcards_by_name(self, cards_name):
        """Get all flashcards with a specific cards_name."""
        try:
            cursor = self._execute(
                """
                SELECT id, cards_name, front, back 
                FROM flashcards 
                WHERE cards_name = ?
                ORDER BY id DESC
                """,
                (cards_name,)
            )
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error getting flashcards by name: {e}")
            return []

    def update_flashcard_by_name(self, cards_name, front, back):
        """Update flashcards by cards_name."""
        try:
            self._execute(
                """
                UPDATE flashcards 
                SET front = ?, back = ?
                WHERE cards_name = ?
                """,
                (front, back, cards_name),
                commit=True
            )
            return True
        except sqlite3.Error as e:
            print(f"Error updating flashcards by name: {e}")
            return False

    def delete_flashcards_by_name(self, cards_name):
        """Delete all flashcards with a specific cards_name."""
        try:
            self._execute(
                """
                DELETE FROM flashcards 
                WHERE cards_name = ?
                """,
                (cards_name,),
                commit=True
            )
            return True
        except sqlite3.Error as e:
            print(f"Error deleting flashcards by name: {e}")
            return False

    def close_connection(self):
        """Closes the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def add_expense(self, user_id, name, type_exp, amount, date):
        """Add a new expense to the database."""
        with self._connection:
            cursor = self._connection.cursor()
            cursor.execute("INSERT INTO expenses (user_id, exp_name, exp_type, exp_amount, exp_date) VALUES (?, ?, ?, ?, ?)",
                           (user_id, name, type_exp, amount, date))

    def show_expense(self):
        """Retrieves all expenses from the database."""
        cursor = self._execute("SELECT * FROM expenses")
        return cursor.fetchall()

    def delete_expense(self, expense_id):
        """Delete an expense from the database by its ID."""
        with self._connection:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

    def save_note(self, title, content):
        """Saves a new note to the database."""
        self._connection.execute(
            "INSERT INTO notes (title, content) VALUES (?, ?)",
            (title, content)
        )
        self._connection.commit()

    def __init__(self):
        self.current_user_id = None  # Set this when the user logs in

    def get_flashcards_by_user_id(self, user_id):
        """Fetch flashcards for a specific user."""
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT * FROM flashcards WHERE user_id=?", (user_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching flashcards: {e}")
            return []

    def get_expenses_by_user_id(self, user_id):
        """Fetch expenses for a specific user."""
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT * FROM expenses WHERE user_id=?", (user_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching expenses: {e}")
            return []

    def get_total_spending_by_user_id(self, user_id, current_month):
        """Fetch total spending for a specific user for the current month."""
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                SELECT SUM(exp_amount) 
                FROM expenses 
                WHERE user_id = ? AND exp_date LIKE ?
            """, (user_id, f"{current_month}%"))
            total = cursor.fetchone()[0]
            return total if total is not None else 0.0
        except sqlite3.Error as e:
            print(f"Error fetching total spending: {e}")
            return 0.0

  