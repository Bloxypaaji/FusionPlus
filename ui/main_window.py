from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from database.database_manager import DatabaseManager  # Import your DatabaseManager
from kivy.metrics import dp

class MainWindow(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize database manager
        self.db_manager = DatabaseManager()

        # Main Layout (Vertical)
        self.layout = MDBoxLayout(orientation="vertical")

        # Top App Bar (Now correctly positioned at the top)
        self.top_bar = MDTopAppBar(
            title="Fusion+",
            left_action_items=[["menu", lambda x: self.toggle_menu()]],
            elevation=10,
            pos_hint={"top": 1}  # Ensures it stays at the top
        )

        # Navigation Drawer (Hamburger Menu)
        self.nav_drawer = MDNavigationDrawer()
        self.nav_list = MDList()
        tools = {
            "Todo List": "task_list",
            "Note-Taking": "note_taking",
            "Calculator": "calculator",
            "Unit Converter": "unit_converter",
            "Flashcards": "flashcards",
            "Expense Tracker": "expense_tracker",
        }
        for tool_name, tool_screen in tools.items():
            item = OneLineListItem(text=tool_name, on_release=lambda x, t=tool_screen: self.open_tool(t))
            self.nav_list.add_widget(item)

        self.nav_drawer.add_widget(self.nav_list)

        # Welcome Section (Centered)
        self.welcome_container = AnchorLayout()
        self.welcome_label = MDLabel(
            text="Welcome to Fusion+!\nSelect a tool from the menu.",
            halign="center",
            font_style="H5",
            size_hint=(1, 0.3)  # Ensures proper placement
        )
        self.welcome_container.add_widget(self.welcome_label)

        # Pending Tasks Section
        self.pending_tasks_container = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(60),  # Smaller height for the pending tasks section
            padding=dp(10),
            spacing=dp(5),
            md_bg_color=(0.95, 0.95, 0.95, 1)  # Light gray background
        )

        self.pending_tasks_label = MDLabel(
            text="Pending Tasks: 0",  # Initial text
            halign="center",
            theme_text_color="Primary",
            font_style="Subtitle1",
            on_release=self.show_pending_tasks  # Bind click event
        )
        self.pending_tasks_container.add_widget(self.pending_tasks_label)

        # Scrollable Main Area (To prevent overlapping issues)
        self.scroll_view = ScrollView()
        
        # Create a container for the scroll view
        self.scroll_content = MDBoxLayout(orientation='vertical', size_hint_y=None)
        self.scroll_content.bind(minimum_height=self.scroll_content.setter('height'))
        self.scroll_content.add_widget(self.welcome_container)
        self.scroll_content.add_widget(self.pending_tasks_container)

        self.scroll_view.add_widget(self.scroll_content)

        # Add Widgets in Correct Order
        self.layout.add_widget(self.top_bar)  # Ensures Top Bar stays on top
        self.layout.add_widget(self.scroll_view)

        self.add_widget(self.layout)
        self.add_widget(self.nav_drawer)

        # Load pending tasks count
        self.update_pending_tasks_count()

    def toggle_menu(self):
        """Opens or closes the navigation drawer."""
        self.nav_drawer.set_state("toggle")

    def open_tool(self, tool_name):
        """Navigates to the selected tool."""
        self.manager.current = tool_name
        self.nav_drawer.set_state("close")

    def update_pending_tasks_count(self):
        """Updates the count of pending tasks displayed in the main window."""
        user_id = 1  # Replace with actual user ID
        pending_tasks = self.db_manager.get_tasks(user_id)
        pending_count = sum(1 for task in pending_tasks if task['status'] == 'Pending')
        self.pending_tasks_label.text = f"Pending Tasks: {pending_count}"

        # Update the UI to reflect no pending tasks
        if pending_count == 0:
            self.pending_tasks_label.text = "No Pending Tasks"

    def show_pending_tasks(self, instance):
        """Show a popup with the list of pending tasks."""
        user_id = 1  # Replace with actual user ID
        pending_tasks = self.db_manager.get_tasks(user_id)
        pending_tasks_list = [task['task'] for task in pending_tasks if task['status'] == 'Pending']

        if not pending_tasks_list:
            content = MDLabel(text="No pending tasks.", halign="center")
        else:
            content = MDLabel(text="\n".join(pending_tasks_list), halign="center")

        popup = Popup(title="Pending Tasks", content=content, size_hint=(0.8, 0.8))
        content.bind(on_touch_down=lambda instance, touch: popup.dismiss() if popup.collide_point(*touch.pos) else None)
        popup.open()
