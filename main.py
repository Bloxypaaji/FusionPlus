import sqlite3  # 🔹 Import missing library
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
import os
import nltk
from kivy.utils import platform

from kivymd.uix.list import IconLeftWidget, TwoLineIconListItem, OneLineListItem
from kivy.app import App
from kivy.logger import Logger

# Import necessary components
from database.database_manager import DatabaseManager
#from components.equation_solver import EquationSolver
from components.flashcards import FlashcardScreen
from components.unit_converter import UnitConverter
from ui.main_window import MainWindow
from components.task_list import TaskList
from components.note_taking import NoteTaking  # Add this for future updates
from ui.login import LoginScreen
from components.calculator import Calculator  # Import the calculator class
from ui.signup import SignupScreen
from components.expense_tracker import ExpenseTrackerScreen  # Import the Expense Tracker Screen
#from components.image_text import ImageToText  # Import the ImageToText class

# Ensure the static directory exists
base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the base directory
static_dir = os.path.join(base_dir, 'static')  # Define the static directory path
os.makedirs(static_dir, exist_ok=True)  # Create the static directory if it doesn't exist

# Set logging level to INFO
Logger.setLevel('INFO')

def setup_nltk():
    """Set up NLTK data path for different platforms."""
    if platform == 'android':
        # Point to the packaged data
        nltk_data_path = os.path.join(os.getcwd(), 'nltk_data')
        nltk.data.path.append(nltk_data_path)
        print(f"NLTK data path set to: {nltk_data_path}")

    # Download necessary NLTK resources if not already downloaded
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('maxent_ne_chunker', quiet=True)
        nltk.download('words', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        print(f"Error downloading NLTK resources: {e}")

# Call the setup function at the start of your application
setup_nltk()

class FusionApp(MDApp):
    def build(self):
        self.screen_manager = ScreenManager()
        self.current_user_id = None  # 🔹 Initialize `current_user_id`
        self.db = DatabaseManager()  # 🔹 Initialize DatabaseManager

        # Adding screens to the ScreenManager
        self.screen_manager.add_widget(SignupScreen(name="signup"))
        self.screen_manager.add_widget(LoginScreen(app=self, name="login"))  # Pass `app` to set `user_id`
        self.screen_manager.add_widget(MainWindow(name="main"))
        self.screen_manager.add_widget(Calculator(app=self, name="calculator"))
        #self.screen_manager.add_widget(EquationSolver(name="equation_solver"))
        self.screen_manager.add_widget(UnitConverter(app=self, name="unit_converter"))
        #self.screen_manager.add_widget(ImageToText(name="image_text"))  # Register the ImageToText screen

        self.screen_manager.current = "login"
        return self.screen_manager

    def set_user(self, user_id):
        """Sets the user ID after login."""
        self.current_user_id = user_id
        print(f"User Logged In: {user_id}")  # Debugging

        # Add NoteTaking screen **AFTER** login
        note_screen = NoteTaking(user_id=self.current_user_id, name="note_taking")
        self.screen_manager.add_widget(note_screen)

        # Add TaskList screen with the current user ID
        task_list_screen = TaskList(user_id=self.current_user_id, name="task_list")
        self.screen_manager.add_widget(task_list_screen)

        # Add Flashcard screen with the current user ID
        flashcard_screen = FlashcardScreen(user_id=self.current_user_id, name="flashcards")
        self.screen_manager.add_widget(flashcard_screen)

        # Add Expense Tracker screen with the current user ID
        expense_tracker = ExpenseTrackerScreen(user_id=self.current_user_id, name="expense_tracker")
        print(f"Adding ExpenseTrackerScreen with User ID: {self.current_user_id}")  # Debugging
        self.screen_manager.add_widget(expense_tracker)

    def switch_screen(self, screen_name):
        """Switch to the specified screen."""
        self.screen_manager.current = screen_name

    def refresh_expenses_list(self):
        """Update the recent expenses list display"""
        self.expenses_list.clear_widgets()
        user_id = getattr(self.manager, 'current_user_id')  # Get the current user ID
        expenses = self.db.get_expenses_by_user_id(user_id)  # Fetch expenses for the current user

        if not expenses:
            self.expenses_list.add_widget(OneLineListItem(
                text="No recent expenses found",
                divider="Full"
            ))
            return

        for exp in expenses[:5]:  # Show only the 5 most recent
            icon = IconLeftWidget(
                icon=self.get_icon_for_expense_type(exp['exp_type'])
            )
            item = TwoLineIconListItem(
                text=f"{exp['exp_name']} - ₹{exp['exp_amount']}",
                secondary_text=f"{exp['exp_type']} | {exp['exp_date']}",
                on_release=lambda x, e=exp: self.show_expense_details(e)
            )
            item.add_widget(icon)
            self.expenses_list.add_widget(item)

if __name__ == "__main__":
    FusionApp().run()
