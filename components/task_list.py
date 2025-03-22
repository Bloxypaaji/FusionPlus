from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import OneLineListItem, MDList
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from database.database_manager import DatabaseManager


class TodoItem(MDCard):
    """Custom widget for a todo item with checkbox and delete button."""
    task_text = StringProperty("")
    completed = BooleanProperty(False)

    def __init__(self, task_id, task_text, completed=False, delete_callback=None, status_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task_id
        self.task_text = task_text
        self.completed = completed
        self.delete_callback = delete_callback
        self.status_callback = status_callback

        # Set card styling
        self.orientation = "horizontal"
        self.padding = [dp(8), dp(8), dp(8), dp(8)]
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(60)
        self.ripple_behavior = True
        self.elevation = 1
        self.radius = [dp(8)]
        self.md_bg_color = [0.95, 0.95, 0.95, 1] if not completed else [0.9, 0.9, 0.9, 1]

        # Create checkbox for completion status
        self.checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            active=completed,
            pos_hint={"center_y": 0.5}
        )
        self.checkbox.bind(active=self.on_checkbox_active)
        self.add_widget(self.checkbox)

        # Create label for task text
        self.label = MDLabel(
            text=task_text,
            size_hint_x=0.8,
            theme_text_color="Primary" if not completed else "Secondary",
            strikethrough=completed
        )
        self.add_widget(self.label)

        # Create delete button
        self.delete_btn = MDIconButton(
            icon="close",
            pos_hint={"center_y": 0.5},
            theme_icon_color="Error",
            icon_size=dp(24)
        )
        self.delete_btn.bind(on_release=self.on_delete)
        self.add_widget(self.delete_btn)

    def on_checkbox_active(self, checkbox, value):
        """Handle checkbox state changes."""
        self.completed = value
        self.label.strikethrough = value
        self.label.theme_text_color = "Secondary" if value else "Primary"
        self.md_bg_color = [0.9, 0.9, 0.9, 1] if value else [0.95, 0.95, 0.95, 1]

        if self.status_callback:
            self.status_callback(self.task_id, value)

    def on_delete(self, instance):
        """Handle delete button press."""
        if self.delete_callback:
            self.delete_callback(self.task_id, self)


class AddTaskDialog(MDBoxLayout):
    """Custom content for the add task dialog."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(100)

        # Create text input for task name
        self.task_input = Builder.load_string('''
TextInput:
    id: task_input
    hint_text: "Add a task..."
    multiline: False
    size_hint_y: None
    height: dp(50)
    font_size: '16sp'
''')
        self.add_widget(self.task_input)


class TaskList(Screen):
    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id  # Store the user ID for later use

        # Initialize database manager
        self.db_manager = DatabaseManager()

        # Main layout
        self.layout = MDBoxLayout(orientation="vertical")

        # Top Navigation Bar
        self.top_bar = MDTopAppBar(
            title="Todo List",
            left_action_items=[["menu", lambda x: self.toggle_menu()]],
            right_action_items=[["plus", lambda x: self.show_add_task_dialog()]],
            elevation=4,
            pos_hint={"top": 1}
        )

        # Navigation Drawer
        self.nav_drawer = MDNavigationDrawer()
        self.nav_list = MDList()
        self.populate_nav_drawer()
        self.nav_drawer.add_widget(self.nav_list)

        # Create containers for pending and completed tasks
        self.pending_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(16), dp(16), dp(16), dp(8)],
            size_hint_y=None
        )
        self.pending_container.bind(minimum_height=self.pending_container.setter('height'))

        self.completed_container = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(16), dp(8), dp(16), dp(16)],
            size_hint_y=None
        )
        self.completed_container.bind(minimum_height=self.completed_container.setter('height'))

        # Title for completed tasks section
        self.completed_title = MDLabel(
            text="Completed",
            theme_text_color="Secondary",
            font_style="H6",
            size_hint_y=None,
            height=dp(40),
            opacity=0  # Initially hidden until there are completed tasks
        )

        # Empty state message
        self.empty_label = MDLabel(
            text="No tasks yet! Add one by clicking the + button.",
            halign="center",
            theme_text_color="Hint",
            font_style="Body1",
            size_hint_y=None,
            height=dp(80)
        )

        # Scrollable area containing both pending and completed tasks
        self.scroll_content = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(16)
        )
        self.scroll_content.bind(minimum_height=self.scroll_content.setter('height'))
        self.scroll_content.add_widget(self.empty_label)
        self.scroll_content.add_widget(self.pending_container)
        self.scroll_content.add_widget(self.completed_title)
        self.scroll_content.add_widget(self.completed_container)

        self.scroll_view = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False
        )
        self.scroll_view.add_widget(self.scroll_content)

        # Add widgets to main layout
        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.scroll_view)

        # Add main layout to screen
        self.add_widget(self.layout)
        self.add_widget(self.nav_drawer)

        # Add task dialog
        self.dialog = None

        # Load existing tasks
        Clock.schedule_once(lambda dt: self.load_tasks(), 0.5)

    def populate_nav_drawer(self):
        """Populate the navigation drawer with items."""
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

    def toggle_menu(self):
        """Opens or closes the navigation drawer."""
        self.nav_drawer.set_state("toggle")

    def open_tool(self, tool_name):
        """Navigates to the selected tool."""
        if self.manager:
            self.manager.current = tool_name
            self.nav_drawer.set_state("close")

    def show_add_task_dialog(self):
        """Show dialog to add a new task."""
        content = AddTaskDialog()  # Create a new instance of AddTaskDialog each time
        self.dialog = MDDialog(
            title="Add a new task",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=self.dismiss_dialog
                ),
                MDRaisedButton(
                    text="ADD",
                    on_release=lambda x: self.add_task(content.task_input.text)
                ),
            ],
        )
        self.dialog.open()

    def dismiss_dialog(self, *args):
        """Dismiss the dialog."""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None  # Reset the dialog to None after dismissal

    def add_task(self, task_text):
        """Add a new task to the database and UI."""
        if task_text.strip():
            # Add to database
            task_id = self.db_manager.add_task(self.user_id, task_text.strip())

            # Add to UI
            task_item = TodoItem(
                task_id=task_id,
                task_text=task_text.strip(),
                delete_callback=self.delete_task,
                status_callback=self.update_task_status
            )
            self.pending_container.add_widget(task_item)

            # Update empty state
            self.update_empty_state()

            # Clear input and dismiss dialog
            if self.dialog:
                self.dialog.content_cls.task_input.text = ""  # Clear the input field
            self.dismiss_dialog()  # Dismiss the dialog

    def update_task_status(self, task_id, is_completed):
        """Update task status in database and reorder in UI."""
        # Update in database
        status = 'Completed' if is_completed else 'Pending'
        self.db_manager.update_task_status(task_id, status)

        # Find the task item
        task_item = None
        container = self.pending_container if not is_completed else self.completed_container
        opposite_container = self.completed_container if not is_completed else self.pending_container

        for child in container.children:
            if isinstance(child, TodoItem) and child.task_id == task_id:
                task_item = child
                break

        if not task_item:
            for child in opposite_container.children:
                if isinstance(child, TodoItem) and child.task_id == task_id:
                    task_item = child
                    break

        if task_item:
            # Remove from current container
            if task_item in container.children:
                container.remove_widget(task_item)
            else:
                opposite_container.remove_widget(task_item)

            # Add to the appropriate container
            if is_completed:
                self.completed_container.add_widget(task_item)
            else:
                self.pending_container.add_widget(task_item)

        # Update visibility of completed section
        self.update_completed_section_visibility()

    def delete_task(self, task_id, task_item):
        """Delete a task from database and UI."""
        # Delete from database
        self.db_manager.delete_task(task_id)

        # Delete from UI
        if task_item in self.pending_container.children:
            self.pending_container.remove_widget(task_item)
        elif task_item in self.completed_container.children:
            self.completed_container.remove_widget(task_item)

        # Update empty state and completed section visibility
        self.update_empty_state()
        self.update_completed_section_visibility()

    def load_tasks(self):
        """Load tasks from database."""
        tasks = self.db_manager.get_tasks(self.user_id)

        # Clear existing task containers before loading new tasks
        self.pending_container.clear_widgets()
        self.completed_container.clear_widgets()

        for task in tasks:
            task_item = TodoItem(
                task_id=task['id'],
                task_text=task['task'],
                completed=task['status'] == 'Completed',
                delete_callback=self.delete_task,
                status_callback=self.update_task_status
            )

            if task['status'] == 'Completed':
                self.completed_container.add_widget(task_item)
        else:
                self.pending_container.add_widget(task_item)

        self.update_empty_state()
        self.update_completed_section_visibility()

    def update_empty_state(self):
        """Update visibility of empty state message."""
        has_pending_tasks = len(self.pending_container.children) > 0
        has_completed_tasks = len(self.completed_container.children) > 0
        self.empty_label.opacity = 0 if has_pending_tasks or has_completed_tasks else 1

    def update_completed_section_visibility(self):
        """Update visibility of completed tasks section."""
        has_completed = len(self.completed_container.children) > 0
        self.completed_title.opacity = 1 if has_completed else 0


"""
In your DatabaseManager class, you should have the following methods:

1. add_task(user_id, task_text) -> task_id
   - Adds a new task and returns the task ID

2. update_task_status(task_id, status)
   - Updates the status of a task ('Pending' or 'Completed')

3. delete_task(task_id)
   - Deletes a task by ID

4. get_tasks(user_id)
   - Returns a list of task dictionaries with keys: 'id', 'task', 'status'
"""