from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import MDList, TwoLineListItem, IconLeftWidget, IconRightWidget, TwoLineIconListItem, OneLineIconListItem, OneLineListItem
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.animation import Animation
from kivy.clock import Clock
from database.database_manager import DatabaseManager
from utils.qa_generator import  EnhancedQAGenerator
import datetime
import importlib.util
import sys
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, NumericProperty, ListProperty
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.carousel import Carousel
from kivymd.app import MDApp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar
import sqlite3
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line
from kivymd.uix.navigationdrawer import MDNavigationDrawer

class Tab(MDFloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    tab_label_text = StringProperty()  # Use tab_label_text instead of text
    chapter_id = NumericProperty(0)

    def __init__(self, **kwargs):
        # Extract text from kwargs and set it as tab_label_text
        if 'text' in kwargs:
            kwargs['tab_label_text'] = kwargs.pop('text')
        super().__init__(**kwargs)

class FlashcardItem(MDCard):
    """A simple card to display a flashcard"""
    def __init__(self, flashcard_id, cards_name, front, back, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.flashcard_id = flashcard_id
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(15)
        self.spacing = dp(10)
        self.elevation = 1
        self.radius = [10]
        self.md_bg_color = [1, 1, 1, 1]

        # Add the content
        name_label = MDLabel(
            text=cards_name,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        )
        front_label = MDLabel(
            text=front,
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(30)
        )
        back_label = MDLabel(
            text=back,
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30)
        )

        self.add_widget(name_label)
        self.add_widget(front_label)
        self.add_widget(back_label)

        if on_press:
            self.bind(on_release=lambda x: on_press(self.flashcard_id))

class AddFlashcardDialog(MDBoxLayout):
    def __init__(self, db, on_save=None, existing_flashcard_name=None, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.on_save = on_save
        self.existing_flashcard_name = existing_flashcard_name  # Store existing flashcard name
        self.orientation = 'vertical'
        self.spacing = dp(20)
        self.padding = dp(20)
        self.size_hint_y = None
        self.height = dp(400)

        # Create tabs
        self.tabs = MDTabs()

        # AI Generation Tab (default)
        ai_tab = Tab(text='AI Generation')
        ai_layout = MDBoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        self.ai_name_field = MDTextField(
            hint_text="AI Flashcard Name",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48)
        )
        self.ai_text = MDTextField(
            hint_text="Enter text for AI generation",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(150)
        )
        self.num_questions_field = MDTextField(
            hint_text="Number of Questions (max 50)",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48),
            input_filter='int'  # Ensure only integers are entered
        )
        generate_button = MDRaisedButton(
            text="Generate",
            on_release=self.generate_flashcards
        )
        ai_layout.add_widget(self.ai_name_field)
        ai_layout.add_widget(self.ai_text)
        ai_layout.add_widget(self.num_questions_field)
        ai_layout.add_widget(generate_button)
        ai_tab.add_widget(ai_layout)
        self.tabs.add_widget(ai_tab)

        # Manual Entry Tab
        manual_tab = Tab(text='Manual Entry')
        manual_layout = MDBoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        self.name_field = MDTextField(
            hint_text="Flashcard Name",
            mode="rectangle",
            size_hint_y=None,
            height=dp(48)
        )
        self.front_field = MDTextField(
            hint_text="Question",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(96)
        )
        self.back_field = MDTextField(
            hint_text="Answer",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(96)
        )
        manual_layout.add_widget(self.name_field)
        manual_layout.add_widget(self.front_field)
        manual_layout.add_widget(self.back_field)
        manual_tab.add_widget(manual_layout)
        self.tabs.add_widget(manual_tab)

        self.add_widget(self.tabs)

        # Automatically set the flashcard name if provided
        if self.existing_flashcard_name:
            print(f"Setting AI Flashcard Name to: {self.existing_flashcard_name}")  # Debugging line
            self.ai_name_field.text = self.existing_flashcard_name
            self.name_field.text = self.existing_flashcard_name
        else:
            print("No existing flashcard name provided.")  # Debugging line

    def generate_flashcards(self, *args):
        """Generate flashcards using NLTK"""
        text = self.ai_text.text.strip()
        if not text:
            show_message("Please enter some text")
            return

        try:
            num_questions = int(self.num_questions_field.text.strip() or 0)
            if num_questions <= 0 or num_questions > 50:
                show_message("Please enter a valid number of questions (1-50)")
                return

            qa_generator = EnhancedQAGenerator()
            qa_pairs = qa_generator.generate_qa_pairs(text, num_pairs=num_questions)

            if not qa_pairs:
                show_message("Couldn't generate questions. Try more detailed content.")
                return

            cards_name = self.ai_name_field.text.strip() or self.name_field.text.strip()  # Automatically set cards_name

            for pair in qa_pairs:
                print(f"Generated pair: Question={pair['question']}, Answer={pair['answer']}")  # Debugging print
                # Attempt to add the flashcard to the database
                success = self.db.add_flashcard(1, cards_name, pair['question'], pair['answer'])
                if not success:
                    print(f"Failed to add flashcard: {pair['question']} - {pair['answer']}")  # Debugging print
                    show_message("Failed to save one or more flashcards.")
                    return

            show_message(f"Generated {len(qa_pairs)} flashcards with name '{cards_name}'!")
            self.on_save()

        except Exception as e:
            print(f"Error generating flashcards: {str(e)}")
            show_message("Error generating flashcards")

class EditFlashcardDialog(MDBoxLayout):
    def __init__(self, flashcard_id, front_text, back_text, db, on_save=None, dialog=None, **kwargs):
        super().__init__(**kwargs)
        self.flashcard_id = flashcard_id
        self.db = db
        self.on_save = on_save
        self.dialog = dialog
        self.orientation = 'vertical'
        self.spacing = dp(20)
        self.padding = dp(20)
        self.size_hint_y = None
        self.height = dp(300)

        # Create text fields
        self.front_field = MDTextField(
            hint_text="Question",
            text=front_text,
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(96)
        )
        self.back_field = MDTextField(
            hint_text="Answer",
            text=back_text,
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(96)
        )

        self.add_widget(self.front_field)
        self.add_widget(self.back_field)
        self.add_widget(MDRaisedButton(
            text="SAVE",
            on_release=self.save_flashcard
        ))

    def save_flashcard(self, *args):
        front = self.front_field.text.strip()
        back = self.back_field.text.strip()

        if not all([front, back]):
            show_message("Please fill in all fields")
            return

        if self.db.update_flashcard(self.flashcard_id, self.db.get_flashcard(self.flashcard_id)[1], front, back):
            show_message("Flashcard updated successfully!")
            if self.on_save:
                self.on_save()
            if self.dialog:
                self.dialog.dismiss()
        else:
            show_message("Failed to update flashcard.")

class FlashcardScreen(MDScreen):
    user_id = NumericProperty()  # Change to NumericProperty to hold the user ID

    def __init__(self, user_id, **kwargs):  # Accept user_id in the constructor
        super().__init__(**kwargs)
        self.user_id = user_id  # Set the user_id
        self.name = "flashcards"
        self.db = DatabaseManager()
        self.dialog = None
        
        # Create the navigation drawer
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
        self.add_widget(self.nav_drawer)

    def toggle_menu(self):
        """Opens or closes the navigation drawer."""
        self.nav_drawer.set_state("toggle")

    def open_tool(self, tool_name):
        """Navigates to the selected tool."""
        app = MDApp.get_running_app()
        app.root.current = tool_name
        self.nav_drawer.set_state("close")

    def on_enter(self):
        """Load flashcards when screen is entered"""
        self.load_flashcards()

    def load_flashcards(self):
        """Load and display all flashcards grouped by cards_name for the current user."""
        try:
            container = self.ids.flashcard_list
            container.clear_widgets()

            flashcards = self.db.get_flashcards_by_user_id(self.user_id)  # Use the user_id
            print(f"Fetched flashcards for user ID {self.user_id}: {flashcards}")  # Debugging print
            if not flashcards:
                # Show empty state
                empty_label = MDLabel(
                    text="No flashcards yet. Click + to add some!",
                    halign="center",
                    theme_text_color="Secondary"
                )
                container.add_widget(empty_label)
                return

            # Group flashcards by cards_name
            groups = {}
            for card in flashcards:
                cards_name = card['cards_name']  # Ensure this is a string
                if cards_name not in groups:
                    groups[cards_name] = []
                groups[cards_name].append(card)

            # Add each group to the list
            for group_name, cards in groups.items():
                group_widget = FlashcardGroup(
                    group_name=group_name,  # Ensure group_name is a string
                    flashcards=cards,
                    on_edit=self.edit_group,
                    on_view=self.view_group
                )
                container.add_widget(group_widget)

        except Exception as e:
            print(f"Error loading flashcards: {e}")

    def edit_group(self, group_name):
        """Edit all flashcards in a group"""
        try:
            flashcards = self.db.get_flashcards_by_name(group_name)
            if not flashcards:
                return

            content = MDBoxLayout(
                orientation='vertical',
                spacing=dp(20),
                padding=dp(20),
                size_hint_y=None,
                height=dp(400)
            )

            for index, card in enumerate(flashcards, start=1):
                card_box = MDBoxLayout(
                    orientation='vertical',
                    spacing=dp(10),
                    size_hint_y=None,
                    height=dp(150)
                )

                front_field = MDTextField(
                    text=card[2],
                    hint_text=f"Question {index}",
                    multiline=True
                )
                back_field = MDTextField(
                    text=card[3],
                    hint_text=f"Answer {index}",
                    multiline=True
                )

                card_box.add_widget(front_field)
                card_box.add_widget(back_field)
                content.add_widget(card_box)

            edit_dialog = MDDialog(
                title=f"Edit Group: {group_name}",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda x: edit_dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="SAVE",
                        on_release=lambda x: self.save_group_edits(group_name, content, edit_dialog)
                    )
                ]
            )
            edit_dialog.open()
        except Exception as e:
            print(f"Error editing group: {e}")

    def save_group_edits(self, group_name, content, dialog):
        """Save edits made to a group of flashcards"""
        try:
            for card_box in content.children:
                front = card_box.children[1].text.strip()
                back = card_box.children[0].text.strip()
                # Update each flashcard in the database
                self.db.update_flashcard_by_name(group_name, front, back)
            dialog.dismiss()
            self.load_flashcards()
        except Exception as e:
            print(f"Error saving group edits: {e}")

    def view_group(self, group_name):
        """View all flashcards in a group in full screen"""
        try:
            flashcards = self.db.get_flashcards_by_name(group_name)
            if not flashcards:
                return

            # Create a new screen for viewing flashcards
            flashcard_view = FlashcardView(
                group_name=group_name,
                flashcards=flashcards,
                db=self.db,
                on_flashcards_updated=self.load_flashcards  # Pass the callback
            )
            app = MDApp.get_running_app()
            app.root.add_widget(flashcard_view)
            app.root.current = flashcard_view.name

        except Exception as e:
            print(f"Error viewing group: {e}")

    def delete_group(self, group_name, dialog):
        """Delete all flashcards in a group"""
        try:
            self.db.delete_flashcards_by_name(group_name)
            dialog.dismiss()
            self.load_flashcards()
        except Exception as e:
            print(f"Error deleting group: {e}")

    def show_add_dialog(self):
        """Show dialog to add a new flashcard"""
        if not self.dialog:
            content = AddFlashcardDialog(db=self.db, on_save=self.load_flashcards)
            self.dialog = MDDialog(
                title="Add New Flashcard",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="SAVE",
                        on_release=lambda x: self.save_flashcard(content)
                    )
                ]
            )
        self.dialog.open()

    def save_flashcard(self, content):
        """Save a new flashcard"""
        name = content.name_field.text.strip()
        front = content.front_field.text.strip()
        back = content.back_field.text.strip()

        if not all([name, front, back]):
            show_message("Please fill in all fields")
            return

        if self.db.add_flashcard(1, name, front, back):
            show_message("Flashcard added successfully!")
            self.dialog.dismiss()
            self.dialog = None
            self.load_flashcards()

    def view_flashcard(self, flashcard_id):
        """View a flashcard's details"""
        try:
            card = self.db.get_flashcard(flashcard_id)
            if not card:
                return

            content = MDBoxLayout(
                orientation='vertical',
                spacing=dp(20),
                padding=dp(20),
                size_hint_y=None,
                height=dp(300)
            )

            # Add labels
            content.add_widget(MDLabel(
                text=f"Group: {card[1]}",
                theme_text_color="Primary",
                font_style="H6"
            ))
            content.add_widget(MDLabel(
                text=f"Question: {card[2]}",
                theme_text_color="Primary"
            ))
            content.add_widget(MDLabel(
                text=f"Answer: {card[3]}",
                theme_text_color="Secondary"
            ))

            view_dialog = MDDialog(
                title="View Flashcard",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="CLOSE",
                        on_release=lambda x: view_dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="DELETE",
                        on_release=lambda x: self.delete_flashcard(flashcard_id, view_dialog)
                    )
                ]
            )
            view_dialog.open()

        except Exception as e:
            print(f"Error viewing flashcard: {e}")

    def delete_flashcard(self, flashcard_id, dialog):
        """Delete a flashcard"""
        if self.db.delete_flashcard(flashcard_id):
            dialog.dismiss()
            self.load_flashcards()

class FlashcardView(MDScreen):
    """Screen for viewing flashcards in a group"""
    group_name = StringProperty()
    current_index = NumericProperty(0)
    flashcards = ListProperty()
    on_flashcards_updated = ObjectProperty()  # Callback for refreshing flashcards

    def __init__(self, group_name, flashcards, db, on_flashcards_updated=None, **kwargs):
        super().__init__(**kwargs)
        self.group_name = group_name
        self.flashcards = flashcards
        self.db = db
        self.on_flashcards_updated = on_flashcards_updated  # Store the callback
        self.name = f"view_{group_name}"

        # Build the UI
        self.build_ui()

    def build_ui(self):
        # Use FloatLayout as root to allow for better positioning
        layout = FloatLayout()
        
        # Fixed top app bar that stays at the top
        nav_bar = MDTopAppBar(
            title=f"{self.group_name} - Flashcards",
            elevation=4,
            pos_hint={"top": 1},
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[
                ["delete", lambda x: self.delete_group()],
                ["plus", lambda x: self.show_add_flashcard_dialog()]
            ]
        )
        
        # Add carousel for flashcards with proper positioning below the app bar
        # The carousel will take up the remaining space
        self.carousel = Carousel(
            direction='right',
            pos_hint={"top": 0.9, "center_x": 0.5},  # Position it below the app bar
            size_hint=(1, 0.9)  # Take 90% of the height, leaving space for the app bar
        )
        
        for card in self.flashcards:
            flashcard = Flashcard(
                front_text=card[2],
                back_text=card[3],
                flashcard_id=card[0],
                db=self.db,
                on_flashcard_updated=self.on_flashcards_updated
            )
            self.carousel.add_widget(flashcard)

        layout.add_widget(nav_bar)
        layout.add_widget(self.carousel)
        self.add_widget(layout)

    def show_add_flashcard_dialog(self):
        """Show dialog to add a new flashcard linked to the current group."""
        content = AddFlashcardDialog(db=self.db, on_save=self.on_flashcards_updated)
        content.name_field.text = self.group_name  # Automatically set the cards_name
        content.name_field.disabled = True  # Disable the field to prevent user editing
        dialog = MDDialog(
            title="Add New Flashcard",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="SAVE",
                    on_release=lambda x: self.save_flashcard(content, dialog)
                )
            ]
        )
        dialog.open()

    def save_flashcard(self, content, dialog):
        """Save a new flashcard linked to the current group."""
        name = self.group_name  # Use the group name as the cards_name
        front = content.front_field.text.strip()
        back = content.back_field.text.strip()

        if not all([front, back]):
            show_message("Please fill in all fields")
            return

        if self.db.add_flashcard(1, name, front, back):
            show_message("Flashcard added successfully!")
            dialog.dismiss()
            if self.on_flashcards_updated:
                self.on_flashcards_updated()  # Call the callback to refresh flashcards
            
            # Update the current view with the new flashcard
            flashcards = self.db.get_flashcards_by_name(self.group_name)
            newest_card = flashcards[-1]  # Assume the newest card is the last one
            new_flashcard = Flashcard(
                front_text=newest_card[2],
                back_text=newest_card[3],
                flashcard_id=newest_card[0],
                db=self.db,
                on_flashcard_updated=self.on_flashcards_updated
            )
            self.carousel.add_widget(new_flashcard)
            # Optionally switch to the new card
            self.carousel.index = len(self.carousel.slides) - 1
        else:
            show_message("Failed to add flashcard.")

    def previous_card(self, *args):
        """Show previous flashcard"""
        self.carousel.load_previous()

    def next_card(self, *args):
        """Show next flashcard"""
        self.carousel.load_next()

    def go_back(self, *args):
        """Return to flashcard list"""
        app = MDApp.get_running_app()
        app.root.current = "flashcards"
        app.root.remove_widget(self)

    def delete_group(self, *args):
        """Delete the entire flashcard group"""
        dialog = MDDialog(
            title="Delete Group",
            text="Are you sure you want to delete the entire group?",
            buttons=[
                MDRaisedButton(
                    text="CANCEL",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="DELETE",
                    on_release=lambda x: (
                        self._perform_delete_group(),
                        dialog.dismiss()
                    )
                ),
            ],
        )
        dialog.open()

    def _perform_delete_group(self):
        """Helper method to delete the entire group"""
        try:
            self.db.delete_flashcards_by_name(self.group_name)
            self.go_back()
            show_message("Group deleted successfully!")
        except Exception as e:
            show_message(f"Error deleting group: {str(e)}")

class Flashcard(MDCard):
    """Interactive flashcard widget with enhanced flip animation"""
    current_text = StringProperty()
    header_text = StringProperty("Question")
    is_flipped = BooleanProperty(False)
    rotation = NumericProperty(0)
    
    def __init__(self, front_text, back_text, flashcard_id, db, on_flashcard_updated, **kwargs):
        super().__init__(**kwargs)
        self.front_text = front_text
        self.back_text = back_text
        self.flashcard_id = flashcard_id
        self.db = db
        self.on_flashcard_updated = on_flashcard_updated
        
        # Set card properties
        self.orientation = 'vertical'
        self.size_hint = (0.9, None)  # Use 90% of the screen width for better responsiveness
        self.height = dp(400)  # Increased height for a larger card
        self.padding = dp(20)
        self.md_bg_color = [1, 1, 1, 1]
        self.radius = [20]  # Set rounded corners
        self.elevation = 3  # Add slight elevation for depth
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        
        # Build the card content
        self.build_card()
    
    def build_card(self):
        layout = FloatLayout()
        
        # Card content (question/answer)
        self.content_layout = MDBoxLayout(
            orientation='vertical', 
            spacing=dp(15), 
            size_hint=(0.9, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.55}
        )
        
        # Header with card label
        self.header = MDLabel(
            text=self.header_text,
            theme_text_color="Primary",
            halign="center",
            font_style="H5",
            bold=True
        )
        
        # Content with question/answer
        self.content = MDLabel(
            text=self.front_text,
            theme_text_color="Secondary",
            halign="center",
            font_style="H6"
        )
        
        # Instruction label at the bottom
        tap_instruction = MDLabel(
            text="Tap card to flip",
            theme_text_color="Hint",
            halign="center",
            font_style="Caption",
            pos_hint={'center_x': 0.5, 'y': 0.05},
            size_hint=(1, 0.1)
        )
        
        self.content_layout.add_widget(self.header)
        self.content_layout.add_widget(self.content)
        
        # Navigation arrows
        left_arrow = MDIconButton(
            icon="arrow-left",
            on_release=self.previous_card,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 1],
            md_bg_color=[0.9, 0.9, 0.9, 1],
            pos_hint={'center_y': 0.5, 'x': 0},
            size_hint=(None, None),
            size=(dp(60), dp(60))
        )
        
        right_arrow = MDIconButton(
            icon="arrow-right",
            on_release=self.next_card,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 1],
            md_bg_color=[0.9, 0.9, 0.9, 1],
            pos_hint={'center_y': 0.5, 'right': 1},
            size_hint=(None, None),
            size=(dp(60), dp(60))
        )
        
        # Action buttons at the bottom
        edit_button = MDIconButton(
            icon="pencil",
            on_release=self.edit_flashcard,
            theme_text_color="Custom",
            text_color=[0, 0, 0, 1],
            md_bg_color=[0.9, 0.9, 0.9, 1],
            pos_hint={'center_y': 0.1, 'right': 0.9}, 
            size_hint=(None, None),
            size=(dp(40), dp(40))
        )
        
        delete_button = MDIconButton(
            icon="delete",
            on_release=self.delete_flashcard,
            theme_text_color="Custom",
            text_color=[1, 0, 0, 1],
            md_bg_color=[0.9, 0.9, 0.9, 1],
            pos_hint={'center_y': 0.1, 'right': 0.2},
            size_hint=(None, None),
            size=(dp(40), dp(40))
        )
        
        # Add everything to layout
        layout.add_widget(self.content_layout)
        layout.add_widget(left_arrow)
        layout.add_widget(right_arrow)
        layout.add_widget(edit_button)
        layout.add_widget(delete_button)
        layout.add_widget(tap_instruction)
        
        self.add_widget(layout)
        
        # Bind touch for flipping
        self.bind(on_touch_down=self.flip_card)

    def flip_card(self, instance, touch):
        """Flip the card to show the answer."""
        if self.collide_point(*touch.pos):
            self.is_flipped = not self.is_flipped  # Toggle the flip state
            self.animate_flip()

    def animate_flip(self):
        """Animate the flip effect."""
        if self.is_flipped:
            # Animate to show the back (answer)
            Animation(rotation=180, duration=0.5).start(self)
            self.header.text = "Answer"  # Change header to "Answer"
            self.content.text = self.back_text  # Change to back text
        else:
            # Animate to show the front (question)
            Animation(rotation=0, duration=0.5).start(self)
            self.header.text = "Question"  # Change header back to "Question"
            self.content.text = self.front_text  # Change to front text

    def previous_card(self, *args):
        """Navigate to the previous card in the carousel."""
        self.parent.parent.load_previous()  # Navigate to the previous card in the parent carousel

    def next_card(self, *args):
        """Navigate to the next card in the carousel."""
        self.parent.parent.load_next()  # Navigate to the next card in the parent carousel

    def edit_flashcard(self, *args):
        """Edit the flashcard's question and answer."""
        edit_dialog_content = EditFlashcardDialog(
            flashcard_id=self.flashcard_id,
            front_text=self.front_text,
            back_text=self.back_text,
            db=self.db,
            on_save=self.on_flashcard_updated,  # Pass the callback for refreshing
            dialog=None  # Placeholder for the dialog reference
        )
        dialog = MDDialog(
            title="Edit Flashcard",
            type="custom",
            content_cls=edit_dialog_content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        edit_dialog_content.dialog = dialog  # Set the dialog reference
        dialog.open()

    def delete_flashcard(self, *args):
        """Delete the flashcard."""
        if self.db.delete_flashcard(self.flashcard_id):
            show_message("Flashcard deleted successfully!")
            self.parent.remove_widget(self)  # Remove the flashcard from the parent layout
        else:
            show_message("Failed to delete flashcard.")

class FlashcardGroup(MDBoxLayout):
    group_name = StringProperty()

    def __init__(self, group_name, flashcards, on_edit=None, on_view=None, **kwargs):
        super().__init__(**kwargs)
        self.group_name = group_name
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = dp(10)
        self.spacing = dp(10)
        self.elevation = 1
        self.radius = [10]
        self.md_bg_color = [1, 1, 1, 1]
        self.on_view = on_view  # Store the on_view callback

        # Add the content
        name_label = MDLabel(
            text=group_name,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        )

        # Make the entire group clickable
        self.add_widget(name_label)
        self.bind(on_touch_down=lambda instance, touch: self.on_view(group_name) if self.collide_point(*touch.pos) else None)

        view_button = MDIconButton(
            icon="cards-outline",
            on_release=lambda x: on_view(group_name)
        )

        self.add_widget(view_button)

# Load KV Design
KV = '''
<FlashcardScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(10)
        
        MDTopAppBar:
            title: "Fusion+ - Flashcards"
            elevation: 1
            pos_hint: {"top": 1}
            left_action_items: [["menu", lambda x: root.toggle_menu()]]
        
        ScrollView:
            MDBoxLayout:
                id: flashcard_list
                orientation: 'vertical'
                adaptive_height: True
                spacing: dp(10)
                padding: [dp(10), dp(10), dp(10), dp(80)]  # Extra bottom padding for FAB
        
        MDRaisedButton:
            text: "+"
            font_size: "24sp"
            size_hint: None, None
            size: dp(56), dp(56)
            pos_hint: {"center_x": .5}
            elevation: 2
            on_release: root.show_add_dialog()
'''

Builder.load_string(KV)
def check_numpy():
    """Check if numpy is installed and accessible."""
    try:
        spec = importlib.util.find_spec("numpy")
        if spec is None:
            return False
        import numpy
        return True
    except ImportError:
        return False

# Create a simple toast-like message system
class Toast:
    """Simple toast-like message system"""
    _instance = None

    @classmethod
    def show(cls, text, duration=2):
        if cls._instance:
            cls._instance.dismiss()

        content = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            padding="16dp",
            size_hint_y=None,
            height="60dp"
        )

        label = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign="center",
            valign="center"
        )
        content.add_widget(label)

        dialog = MDDialog(
            type="custom",
            content_cls=content,
            md_bg_color=(0.2, 0.2, 0.2, 0.9),
            size_hint=(None, None),
            size=(dp(280), dp(80)),
            radius=[20, 20, 20, 20],
            pos_hint={"center_x": 0.5, "center_y": 0.1},
        )

        cls._instance = dialog
        dialog.open()
        Clock.schedule_once(lambda dt: dialog.dismiss(), duration)

def show_message(text, duration=2):
    """Show a toast message"""
    Toast.show(text, duration)

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

