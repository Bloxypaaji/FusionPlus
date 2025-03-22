from kivy.graphics import Color, Rectangle
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFloatingActionButton, MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.list import OneLineListItem, MDList
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
from kivy.uix.widget import Widget
import sqlite3
import pyttsx3  # ✅ Text-to-Speech Library
import nltk  # ✅ Natural Language Toolkit for processing questions
from kivy.uix.colorpicker import ColorPicker  # Import ColorPicker
from kivy.metrics import dp  # Ensure dp is imported
from kivy.uix.popup import Popup  # Import Popup for color selection
from kivy.uix.button import Button  # Import Button for the cancel button
from kivy.clock import Clock  # Import Clock for animation effects
from kivy.animation import Animation  # Import Animation for UI animations
from kivymd.uix.snackbar import Snackbar  # Import Snackbar for notifications

from kivymd.uix.screen import Screen
from database.database_manager import DatabaseManager
from utils.notai import EnhancedNotAI  # Import the EnhancedNotAI class


class NoteTaking(Screen):
    user_id = ObjectProperty(None)
    color_picker = ObjectProperty(None)  # Define the color_picker attribute

    def __init__(self, user_id, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        print(f"NoteTaking initialized with user_id: {self.user_id}")

        self.db = sqlite3.connect("Fusion.db")
        self.cursor = self.db.cursor()

        # Initialize the color picker
        self.color_picker = ColorPicker()  # Create a ColorPicker instance

        # Initialize the EnhancedNotAI instance
        self.not_ai = EnhancedNotAI()  # Create an instance of EnhancedNotAI

        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)  # ✅ Added Padding

        # Initialize the speech engine
        self.engine = pyttsx3.init()
        self.is_reading = False  # Flag to track if reading is in progress
        self.engine.connect('finished', self.on_reading_finished)  # Connect to the finished event

        # Create the cancel button with improved styling
        self.cancel_button = MDRaisedButton(
            text="Stop Reading",
            md_bg_color=(0.9, 0.1, 0.1, 1),  # Red background for emphasis
            size_hint=(None, None),
            size=(dp(120), dp(50)),  # Set size for the button
            pos_hint={"center_x": 0.5, "y": 0.05},  # Position above the bottom bar
            on_release=self.cancel_reading,  # Bind the cancel function
            opacity=0,  # Start hidden
            disabled=True,  # Start disabled
            elevation=8,  # Higher elevation for emphasis
            _radius=dp(25),  # Rounded corners
        )
        self.add_widget(self.cancel_button)  # Add the button to the layout

        # 🔹 **Top Bar with Menu Button**
        self.top_bar = MDTopAppBar(
            title="Notes",
            md_bg_color=(0.1, 0.5, 1, 1),
            left_action_items=[["menu", lambda x: self.toggle_menu()]],
            elevation=4,  # Increased elevation for depth
        )

        # 🔹 **Navigation Drawer (Sidebar)**
        self.nav_drawer = MDNavigationDrawer()
        self.nav_drawer.md_bg_color = (1, 1, 1, 1)  # Light background color
        
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

        # 🔹 **Search Box with Cancel Button**
        search_layout = BoxLayout(
            orientation="horizontal", 
            size_hint_y=None, 
            height=dp(60), 
            spacing=dp(8),
            padding=[dp(16), dp(5), dp(16), dp(5)]
        )
        
        self.search_bar = MDTextField(
            hint_text="Search notes...",
            size_hint_x=0.9,
            on_text_validate=self.search_notes,
            mode="rectangle",  # Rectangular input field
            line_color_normal=(0.1, 0.5, 1, 1),  # Blue border color
            hint_text_color_normal=(0.1, 0.5, 1, 0.7),  # Light blue hint text
        )
        
        self.cancel_search_btn = MDIconButton(
            icon="refresh",  # Keep the same icon for refresh
            on_release=self.refresh_notes,  # Change the action to refresh notes
            size_hint_x=0.1,
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),  # Gray icon
        )
        
        search_layout.add_widget(self.search_bar)
        search_layout.add_widget(self.cancel_search_btn)

        # 🔹 **Scrollable Notes Grid** - Enhanced with better spacing and animations
        self.scroll_view = ScrollView(do_scroll_x=False, effect_cls='ScrollEffect')
        self.notes_grid = GridLayout(
            cols=5, 
            spacing=dp(18),  # Increased spacing
            size_hint_y=None, 
            padding=dp(18),  # Increased padding
        )
        self.notes_grid.bind(minimum_height=self.notes_grid.setter("height"))
        self.scroll_view.add_widget(self.notes_grid)

        # 🔹 **Floating Add Button (+)**
        self.add_button = MDFloatingActionButton(
            icon="plus",
            md_bg_color=(0.1, 0.5, 1, 1),  # Blue background
            text_color=(1, 1, 1, 1),  # White icon
            pos_hint={"right": 0.95, "bottom": 0.1},
            on_release=lambda x: self.add_note(),
        )

        # 🔹 **Adding Components to Layout**
        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(search_layout)
        self.layout.add_widget(self.scroll_view)

        self.add_widget(self.layout)
        self.add_widget(self.nav_drawer)
        self.add_widget(self.add_button)

        # Load notes with a slight delay for animation effect
        Clock.schedule_once(lambda dt: self.load_notes(), 0.2)


        
    def focus_search(self):
        """Focus on the search field."""
        self.search_bar.focus = True

    def clear_search(self):
        """Clears the search field and reloads all notes."""
        self.search_bar.text = ""
        self.load_notes()
        # Show confirmation with a snackbar
        Snackbar(text="Search cleared", duration=1).open()

    def load_notes(self):
        """Fetches and displays notes from the database with Google Keep style cards."""
        self.notes_grid.clear_widgets()
        self.cursor.execute("SELECT id, title, content, Color FROM notes WHERE user_id=?", (self.user_id,))
        notes = self.cursor.fetchall()

        if not notes:
            # Show empty state message
            empty_layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
            empty_icon = MDIconButton(
                icon="notebook-outline",
                size_hint=(None, None),
                size=(dp(64), dp(64)),
                pos_hint={"center_x": 0.5},
                theme_text_color="Custom",
                text_color=(0.1, 0.5, 1, 0.5),
            )
            empty_label = MDLabel(
                text="No notes yet. Tap the + button to create one.",
                halign="center",
                theme_text_color="Secondary",
            )
            empty_layout.add_widget(empty_icon)
            empty_layout.add_widget(empty_label)
            self.notes_grid.add_widget(empty_layout)
            return

        # Calculate the number of columns based on screen width
        screen_width = self.width  # Get the current screen width
        card_width = dp(170)  # Desired width of each note card
        padding = dp(18)  # Padding between cards
        num_columns = max(1, int((screen_width - padding) / (card_width + padding)))  # Calculate number of columns

        # Set the number of columns in the GridLayout
        self.notes_grid.cols = num_columns

        # Add notes with animation effects
        for i, (note_id, title, content, color) in enumerate(notes):
            # Ensure color is a string before using eval
            if isinstance(color, str):
                try:
                    note_bg_color = eval(color)  # Convert string to tuple
                except Exception as e:
                    print(f"Error evaluating color: {e}")
                    note_bg_color = (1, 1, 1, 1)  # Default to white if there's an error
            else:
                note_bg_color = (1, 1, 1, 1)  # Default to white if color is not a string

            note_card = MDCard(
                size_hint=(None, None),
                width=card_width,  # Set the width of the card
                height=dp(180) if len(content) < 100 else dp(220),
                elevation=1,  # Slightly increased elevation
                padding=dp(12),
                radius=[dp(8)],
                md_bg_color=note_bg_color,  # Set the background color from the database
                on_release=lambda x, n_id=note_id: self.open_note(n_id),  # Open Note on Click
                ripple_behavior=True,  # Add ripple effect on tap
                opacity=0,  # Start with zero opacity for animation
            )

            card_content = BoxLayout(orientation="vertical", spacing=dp(8))

            # Title with ellipsis if too long
            title_label = MDLabel(
                text=title[:40] + ("..." if len(title) > 40 else ""),
                font_style="Subtitle1",
                bold=True,
                size_hint_y=None,
                height=dp(30),
            )

            # Content preview with ellipsis
            content_preview = content[:120] + ("..." if len(content) > 120 else "")
            content_label = MDLabel(
                text=content_preview,
                size_hint_y=None,
                height=dp(120) if len(content) < 100 else dp(160),
                theme_text_color="Secondary",
            )

            card_content.add_widget(title_label)
            card_content.add_widget(content_label)
            note_card.add_widget(card_content)
            self.notes_grid.add_widget(note_card)
            
            # Animate the card appearance with a slight delay based on index
            anim = Animation(opacity=1, d=0.3)
            Clock.schedule_once(lambda dt, card=note_card: anim.start(card), 0.05 * i)

    def open_note(self, note_id):
        """Opens a full-screen note view with color display."""
        self.cursor.execute("SELECT title, content, Color FROM notes WHERE id=?", (note_id,))
        note = self.cursor.fetchone()

        if note:
            self.clear_widgets()
            self.layout = BoxLayout(orientation="vertical", padding=dp(0), spacing=dp(0))

            # Top Bar with Back Button and Color Picker Button
            top_bar = MDTopAppBar(
                title="Edit Note",
                md_bg_color=(0.1, 0.5, 1, 1),  # Theme color for the top bar
                left_action_items=[["arrow-left", lambda x: self.go_back()]],  # Back button
                right_action_items=[
                    ["palette", lambda x: self.show_color_picker(note_id)],  # Color picker button
                    ["refresh", lambda x: self.refresh_notes()],  # Refresh button
                ],
                elevation=2,
            )

            # Note Fields
            content_layout = BoxLayout(
                orientation="vertical", 
                spacing=dp(12), 
                size_hint_y=0.9,
                padding=[dp(16), dp(8), dp(16), dp(8)],
            )
            
            self.edit_note_title = MDTextField(
                text=note[0],
                hint_text="Title",
                size_hint_y=None,
                height=dp(60),
                multiline=False,
                background_color=(1, 1, 1, 1),  # White background
                foreground_color=(0, 0, 0, 1),  # Black text
            )
            
            self.edit_note_content = MDTextField(
                text=note[1],
                hint_text="Note",
                multiline=True,
                size_hint_y=1,
                background_color=(1, 1, 1, 1),  # White background
                foreground_color=(0, 0, 0, 1),  # Black text
            )

            # Set the background color of the note based on the saved color
            note_color = note[2]  # Get the color value from the database

            # Check if note_color is a string and convert it to a tuple
            if isinstance(note_color, str):
                try:
                    note_color = eval(note_color)  # Convert string back to tuple
                except Exception as e:
                    print(f"Error evaluating color: {e}")
                    note_color = (1, 1, 1, 1)  # Default to white if there's an error
            else:
                note_color = (1, 1, 1, 1)  # Default to white if not a string

            # Add a canvas to set the background color
            with content_layout.canvas.before:
                Color(*note_color)  # Unpack the color tuple
                self.rect = Rectangle(size=content_layout.size, pos=content_layout.pos)

            content_layout.bind(size=self._update_rect, pos=self._update_rect)

            content_layout.add_widget(self.edit_note_title)
            content_layout.add_widget(self.edit_note_content)

            # Bottom Toolbar
            buttons_layout = MDBoxLayout(
                orientation="horizontal",
                spacing=dp(10),
                size_hint_y=None,
                height=dp(64),
                padding=[dp(16), dp(8), dp(16), dp(8)],
                md_bg_color=(0.97, 0.97, 0.97, 1),  # Light gray
            )

            update_button = MDFlatButton(
                text="Save",
                on_release=lambda x: self.update_note(note_id),
                theme_text_color="Custom",
                text_color=(0.1, 0.5, 1, 1),
            )

            read_aloud_button = MDFlatButton(
                text="Read Aloud",
                on_release=lambda x: self.read_aloud(),
                theme_text_color="Custom",
                text_color=(0.1, 0.5, 1, 1),
            )

            ask_ai_button = MDFlatButton(
                text="Ask AI",
                on_release=lambda x: self.ask_question(),
                theme_text_color="Custom",
                text_color=(0.1, 0.5, 1, 1),
            )

            buttons_layout.add_widget(update_button)
            buttons_layout.add_widget(read_aloud_button)
            buttons_layout.add_widget(ask_ai_button)  # Add Ask AI button

            self.layout.add_widget(top_bar)
            self.layout.add_widget(content_layout)
            self.layout.add_widget(buttons_layout)

            self.add_widget(self.layout)

    def _update_rect(self, instance, value):
        """Update the rectangle size and position."""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def go_back(self):
        """Returns to the main notes list."""
        self.clear_widgets()
        self.__init__(self.user_id)

    def read_aloud(self):
        """Reads the note content aloud."""
        text = self.edit_note_content.text
        if not text:
            Snackbar(text="No text to read", duration=1.5).open()
            return
        
        # Configure speech engine
        self.engine.setProperty('rate', 150)  # Set speech rate
        self.engine.setProperty('volume', 1)  # Set volume level
        
        # Start reading
        self.engine.say(text)
        self.engine.runAndWait()  # Block until the speech is finished

    def cancel_reading(self, instance):
        """Cancels the reading in progress."""
        if self.is_reading:
            try:
                self.engine.stop()  # Stop the speech engine
            except Exception as e:
                print(f"Error stopping speech engine: {e}")
            finally:
                self.is_reading = False  # Reset reading flag
                self.cancel_button.opacity = 0  # Hide the cancel button
                self.cancel_button.disabled = True  # Disable the cancel button
                Snackbar(text="Reading stopped", duration=1.5).open()  # Show confirmation

    def ask_question(self):
        """Opens a dialog to ask a question about the note with improved UI."""
        content_layout = MDBoxLayout(
            orientation="vertical", 
            spacing=dp(15), 
            size_hint_y=None, 
            height=dp(350),  # Increased height for answer display
            padding=[dp(15), dp(10), dp(15), dp(10)],
        )
        
        # Question input field with better styling
        question_input = MDTextField(
            hint_text="Ask a question about this note...",
            multiline=False,
            mode="rectangle",  # Rectangular style
            size_hint_y=None,
            height=dp(50),
            line_color_normal=(0.1, 0.5, 1, 1),  # Blue focus color
        )
        
        # Create a scrollable answer area
        answer_scroll = ScrollView(
            size_hint_y=None,
            height=dp(250),  # Fixed height
        )
        
        # Answer label with better styling and scrollable container
        answer_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[dp(10), dp(10), dp(10), dp(10)],
            md_bg_color=(0.95, 0.95, 0.98, 1),  # Light blue-gray background
            radius=[dp(5)]
        )
        
        answer_label = MDLabel(
            text="Your answer will appear here...",
            size_hint_y=None,
            theme_text_color="Secondary",
            markup=True
        )
        answer_label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
        answer_box.bind(minimum_height=answer_box.setter('height'))
        
        answer_box.add_widget(answer_label)
        answer_scroll.add_widget(answer_box)
        
        # Loading indicator (initially hidden)
        loading_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30),
            padding=[dp(10), dp(5), dp(10), dp(5)],
        )
        
        loading_label = MDLabel(
            text="Processing your question...",
            size_hint_x=1,
            halign="center",
            theme_text_color="Secondary",
            opacity=0
        )
        
        loading_layout.add_widget(loading_label)
        
        # Add components to layout
        content_layout.add_widget(question_input)
        content_layout.add_widget(loading_layout)
        content_layout.add_widget(answer_scroll)
        
        # Create dialog for asking a question
        self.question_dialog = MDDialog(
            title="Ask AI About This Note",
            type="custom",
            content_cls=content_layout,
            buttons=[
                MDFlatButton(
                    text="Close",
                    theme_text_color="Custom",
                    text_color=(0.1, 0.5, 1, 1),
                    on_release=lambda x: self.question_dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Ask",
                    md_bg_color=(0.1, 0.5, 1, 1),
                    on_release=lambda x: self.process_question(question_input.text, answer_label, loading_label),
                ),
            ],
            size_hint=(0.9, None),
        )
        self.question_dialog.open()

    def process_question(self, question, answer_label, loading_label):
        """Processes the question and provides an answer based on the note content."""
        if not question or question.strip() == "":
            answer_label.text = "Please enter a question first."
            return
        
        # Show loading indicator
        loading_label.opacity = 1
        
        # Get current note content
        current_note_content = self.edit_note_content.text
        
        # Use a Clock to prevent UI freezing during processing
        def get_answer(dt):
            try:
                # Use the EnhancedNotAI instance to get the answer
                answer = self.not_ai.answer_question(question, current_note_content)
                
                # Format the answer with the question for context
                formatted_answer = f"[b]Q: {question}[/b]\n\n[color=3f51b5]{answer}[/color]"
                
                # Update the label with the answer
                answer_label.text = formatted_answer
            except Exception as e:
                answer_label.text = f"I encountered an error processing your question: {str(e)}"
            finally:
                # Hide loading indicator
                loading_label.opacity = 0
        
        # Schedule the answer generation
        Clock.schedule_once(get_answer, 0.5)

    def on_reading_finished(self, name, completed):
        """Callback for when reading is finished."""
        if self.is_reading:
            self.is_reading = False
            self.cancel_button.opacity = 0  # Hide the cancel button
            self.cancel_button.disabled = True  # Disable the cancel button

    def delete_note(self, note_id):
        """Prompts for confirmation before deleting a note."""
        self.confirm_dialog = MDDialog(
            title="Confirm Deletion",
            text="Are you sure you want to delete this note?",
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda x: self.confirm_dialog.dismiss(),
                ),
                MDFlatButton(
                    text="Delete",
                    on_release=lambda x: self.confirm_delete(note_id),
                ),
            ],
        )
        self.confirm_dialog.open()

    def confirm_delete(self, note_id):
        """Actually deletes the note after confirmation."""
        try:
            self.cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
            self.db.commit()
            print(f"Note {note_id} deleted successfully")
            self.confirm_dialog.dismiss()
            self.go_back()
        except sqlite3.Error as e:
            print(f"Error deleting note: {e}")

    def add_note(self):
        """Opens a dialog to add a new note (Google Keep style)."""
        content_layout = MDBoxLayout(
            orientation="vertical", 
            spacing=dp(10), 
            size_hint_y=None,
            height=dp(250),
            padding=[dp(10), dp(5), dp(10), dp(5)],
        )
        
        self.title_input = MDTextField(
            hint_text="Title",
        )
        
        self.content_input = MDTextField(
            hint_text="Note",
            multiline=True,
            size_hint_y=None,
            height=dp(180),
        )
        
        content_layout.add_widget(self.title_input)
        content_layout.add_widget(self.content_input)

        self.add_note_dialog = MDDialog(
            title="New Note",
            type="custom",
            content_cls=content_layout,
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda x: self.add_note_dialog.dismiss(),
                ),
                MDFlatButton(
                    text="Save",
                    on_release=lambda x: self.save_note(self.title_input.text, self.content_input.text, self.color_picker.color),
                ),
            ],
            size_hint=(0.8, None),
        )

        self.add_note_dialog.open()

    def save_note(self, title, content, color):
        """Saves a new note to the database with color."""
        if not title or not content:
            print("Title and content cannot be empty!")
            return

        try:
            self.cursor.execute(
                "INSERT INTO notes (user_id, title, content, Color) VALUES (?, ?, ?, ?)",
                (self.user_id, title, content, str(color))  # Save color as a string
            )
            self.db.commit()
            print("Note saved successfully!")
            self.load_notes()
            self.add_note_dialog.dismiss()
        except sqlite3.Error as e:
            print(f"Error saving note: {e}")

    def update_note(self, note_id):
        """Updates an existing note in the database with color."""
        try:
            new_title = self.edit_note_title.text
            new_content = self.edit_note_content.text
            # Get the current color from the color picker
            color = self.color_picker.color  # Ensure color_picker is defined
            
            self.cursor.execute(
                "UPDATE notes SET title=?, content=?, Color=? WHERE id=?",
                (new_title, new_content, str(color), note_id)  # Save color as a string
            )
            self.db.commit()
            print(f"Note {note_id} updated successfully")
            self.go_back()
        except sqlite3.Error as e:
            print(f"Error updating note: {e}")

    def search_notes(self, instance):
        """Filters notes based on search input."""
        keyword = self.search_bar.text.lower()
        self.notes_grid.clear_widgets()
        
        try:
            self.cursor.execute(
                "SELECT id, title, content FROM notes WHERE user_id=? AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ?)",
                (self.user_id, f"%{keyword}%", f"%{keyword}%")
            )
            notes = self.cursor.fetchall()

            for note_id, title, content in notes:
                note_card = MDCard(
                    size_hint=(0.45, None),
                    height=150,
                    elevation=1,
                    padding=15,
                    radius=[5],
                    line_width=1.5,
                    line_color=(0, 0, 0, 1),
                    on_release=lambda x, n_id=note_id: self.open_note(n_id),
                )
                note_label = MDLabel(
                    text=f"[b]{title}[/b]\n{content[:100]}...",
                    markup=True,
                    size_hint_y=None,
                )
                note_card.add_widget(note_label)
                self.notes_grid.add_widget(note_card)
        except sqlite3.Error as e:
            print(f"Error searching notes: {e}")

    def toggle_menu(self):
        """Opens or closes the navigation drawer."""
        self.nav_drawer.set_state("toggle")

    def open_tool(self, tool_name):
        """Navigates to the selected tool."""
        self.manager.current = tool_name
        self.nav_drawer.set_state("close")

    def show_color_picker(self, note_id):
        """Displays a color picker popup to change the note's background color."""
        color_picker_layout = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        
        for color in note_colors:
            color_button = MDRaisedButton(
                md_bg_color=color,
                size_hint_y=None,  # Set to None to specify height directly
                height=dp(50),  # Adjust height as needed
                on_release=lambda btn, c=color: self.change_note_color(c, note_id)
            )
            color_picker_layout.add_widget(color_button)

        # Create the popup with adjusted size and position
        color_picker_popup = Popup(
            content=color_picker_layout,
            size_hint=(None, None),  # Set size_hint to None for custom width and height
            size=(dp(100), dp(300)),  # Set a specific width and height
            pos_hint={"center_x": 0.9, "y": 0.4}  # Center horizontally and position it lower
        )
        color_picker_popup.open()

    def change_note_color(self, color, note_id):
        """Change the background color of the note and update the database."""
        # Change the background color of the note content and title
        self.edit_note_content.background_color = color  # Change the background color of the note content
        self.edit_note_title.background_color = color  # Change the background color of the title

        # Update the color in the database
        self.cursor.execute("UPDATE notes SET Color=? WHERE id=?", (str(color), note_id))
        self.db.commit()

        # Refresh the note card in the grid to reflect the new color
        self.load_notes()  # Reload notes to refresh the display

    def update_border(self, instance, value):
        """Update the rectangle size and position for the border."""
        self.border_rect.pos = instance.pos
        self.border_rect.size = instance.size

    def refresh_notes(self, *args):
        """Refresh the notes displayed in the UI."""
        self.load_notes()  # Call the method to load notes from the database

note_colors = [
    (1, 0.92, 0.8, 1),      # Light peach
    (0.94, 0.92, 0.8, 1),   # Light yellow
    (0.85, 0.92, 0.8, 1),   # Light green
    (0.8, 0.92, 0.94, 1),   # Light blue
    (0.94, 0.8, 0.9, 1),    # Light pink
    (1, 1, 1, 1),           # White
]
