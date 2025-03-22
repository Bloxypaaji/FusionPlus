from kivymd.uix.screen import Screen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import BoxLayout
from database.database_manager import DatabaseManager
from kivy.metrics import dp  # Ensure dp is imported

class LoginScreen(Screen):
    def __init__(self, app, **kwargs):  # 🔹 Accept `app` as a parameter
        super().__init__(**kwargs)
        self.app = app  # 🔹 Store reference to ToolyApp
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
        self.username_input = MDTextField(hint_text="Username", size_hint=(1, None), height="40dp")
        layout.add_widget(self.username_input)

        # Password input
        self.password_input = MDTextField(hint_text="Password", password=True, size_hint=(1, None), height="40dp")
        layout.add_widget(self.password_input)

        # Login button
        login_button = MDRaisedButton(text="Login", size_hint=(1, None), height="50dp", on_press=self.login_action)
        layout.add_widget(login_button)

        # Switch to Signup Label Button
        signup_label = MDLabel(text="[ref=signup]Don't have an account? Sign up[/ref]", markup=True, halign="center")
        signup_label.bind(on_ref_press=lambda *args: self.switch_to_signup())
        layout.add_widget(signup_label)

        self.add_widget(layout)

    def login_action(self, instance):
        """Handles user login."""
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        user_id = self.db.verify_user(username, password)
        if user_id:
            print(f"Login Successful! Welcome, {username}.")
            self.app.set_user(user_id)  # 🔹 Set user ID after login
            self.manager.current = "main"
        else:
            print("Invalid credentials. Please try again.")

    def switch_to_signup(self):
        """Switch to the Signup screen."""
        self.manager.current = "signup"
