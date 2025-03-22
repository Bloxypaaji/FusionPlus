from kivymd.uix.screen import Screen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import BoxLayout
from database.database_manager import DatabaseManager
from kivy.metrics import dp  # Ensure dp is imported

class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseManager()  # Connect to the database

        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Logo Section
        logo_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), padding=[0, 20, 0, 20])
        logo_label = MDLabel(
            text="Fusion Plus",
            font_style="H4",
            theme_text_color="Custom",
            text_color=(0.1, 0.5, 1, 1),  # Dynamic blue color
            halign="center",
            bold=True
        )
        logo_sub_label = MDLabel(
            text="Your Study Companion",
            theme_text_color="Custom",
            text_color=(0.1, 0.5, 1, 0.7),  # Light blue color
            halign="center"
        )
        logo_layout.add_widget(logo_label)
        logo_layout.add_widget(logo_sub_label)

        layout.add_widget(logo_layout)  # Add logo section to layout

        # Username input
        self.username_input = MDTextField(hint_text="Choose a Username", size_hint=(1, None), height="40dp")
        layout.add_widget(self.username_input)

        # Password input
        self.password_input = MDTextField(hint_text="Choose a Password", password=True, size_hint=(1, None), height="40dp")
        layout.add_widget(self.password_input)

        # Confirm Password input
        self.confirm_password_input = MDTextField(hint_text="Confirm Password", password=True, size_hint=(1, None), height="40dp")
        layout.add_widget(self.confirm_password_input)

        # Signup button
        signup_button = MDRaisedButton(text="Sign Up", size_hint=(1, None), height="50dp", on_press=self.signup_action)
        layout.add_widget(signup_button)

        # Switch to Login Label Button
        login_label = MDLabel(text="[ref=login]Already have an account? Login[/ref]", markup=True, halign="center")
        login_label.bind(on_ref_press=lambda *args: self.switch_to_login())
        layout.add_widget(login_label)

        self.add_widget(layout)

    def signup_action(self, instance):
        """Handles user signup."""
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        confirm_password = self.confirm_password_input.text.strip()

        if not username or not password:
            print("❌ Username & password cannot be empty.")
            return

        if password != confirm_password:
            print("❌ Passwords do not match.")
            return

        success = self.db.register_user(username, password)
        if success:
            print(f" Account created successfully! Welcome, {username}.")
            self.manager.current = "login"  # Redirect to login
        else:
            print(" Username already exists. Please choose a different one.")

    def switch_to_login(self):
        """Switch to the Login screen."""
        self.manager.current = "login"
