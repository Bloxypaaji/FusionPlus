from kivy.graphics import Rectangle, Color
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import OneLineListItem, MDList, TwoLineIconListItem, IconLeftWidget
from kivymd.uix.menu import MDDropdownMenu
from database.database_manager import DatabaseManager
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from datetime import datetime
import calendar
from kivymd.uix.card import MDCard
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.clipboard import Clipboard  # Import Clipboard


class ExpenseTrackerScreen(Screen):
    def __init__(self, user_id=None, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.db = DatabaseManager()
        print(f"Initialized ExpenseTrackerScreen with User ID: {self.user_id}")  # Debugging
        self.selected_date = datetime.now()

        # Main layout with ScrollView for dynamic content
        self.main_layout = BoxLayout(orientation='vertical')

        # **Fixed Top Navigation Bar**
        self.top_bar = MDTopAppBar(
            title="Expense Tracker",
            left_action_items=[["menu", lambda x: self.toggle_menu()]],
            elevation=0,
            pos_hint={"top": 1}
        )
        self.main_layout.add_widget(self.top_bar)

        # ScrollView for the content
        self.scroll_view = ScrollView()
        self.content_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10), size_hint_y=None)
        self.content_layout.bind(minimum_height=self.content_layout.setter('height'))

        # **Expense Name Input**
        self.name_input = MDTextField(
            hint_text='Expense Name',
            helper_text="Enter the name of your expense",
            helper_text_mode="on_focus",
            size_hint_y=None,
            height=dp(48)
        )

        # **Dropdown for Expense Type**
        self.type_button = MDRaisedButton(
            text='Select Expense Type',
            size_hint_y=None,
            height=dp(48)
        )
        self.expense_types = [
            'Education', 'Travel', 'Groceries', 'Rent', 'Utilities', 'Investments',
            'Medical', 'Pharmaceutical', 'Maintenance', 'Taxes', 'Loan EMIs',
            'Hygiene', 'Entertainment', 'Food', 'Vacation (holiday)', 'Fashion',
            'Shopping', 'Self care', 'Misc'
        ]
        self.type_button.bind(on_release=self.show_expense_type_dropdown)

        # **Amount Input**
        self.amount_input = MDTextField(
            hint_text='Amount',
            helper_text="Enter the expense amount",
            helper_text_mode="on_focus",
            input_filter="float",
            size_hint_y=None,
            height=dp(48)
        )

        # **Improved Date Picker Button**
        self.date_button = MDRaisedButton(
            text=f'Date: {self.selected_date.strftime("%Y-%m-%d")}',
            size_hint=(1, None),
            height=dp(50)
        )
        self.date_button.bind(on_release=self.show_date_picker)

        # Add input widgets to content layout
        self.content_layout.add_widget(MDLabel(
            text="Add New Expense",
            font_style="H5",
            size_hint_y=None,
            height=dp(40)
        ))
        self.content_layout.add_widget(self.name_input)
        self.content_layout.add_widget(self.type_button)
        self.content_layout.add_widget(self.amount_input)
        self.content_layout.add_widget(self.date_button)

        # **Action Buttons**
        buttons_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))

        # Log Expense Button
        log_button = MDRaisedButton(
            text='Log Expense',
            size_hint_x=0.33
        )
        log_button.bind(on_press=self.log_expense)

        # Show Expenses Button
        display_button = MDRaisedButton(
            text='Show Expenses',
            size_hint_x=0.33
        )
        display_button.bind(on_press=self.show_expenses)
        
        # Stats Button (NEW)
        stats_button = MDRaisedButton(
            text='Stats',
            size_hint_x=0.33
        )
        stats_button.bind(on_press=self.show_expense_stats)

        buttons_layout.add_widget(log_button)
        buttons_layout.add_widget(display_button)
        buttons_layout.add_widget(stats_button)  # Add the new stats button
        self.content_layout.add_widget(buttons_layout)

        # Recent Expenses Section
        self.content_layout.add_widget(MDLabel(
            text="Recent Expenses",
            font_style="H5",
            size_hint_y=None,
            height=dp(40)
        ))

        # Add the expenses list (initially empty, will be populated in on_enter)
        self.expenses_list = MDList(size_hint_y=None)
        self.expenses_list.bind(minimum_height=self.expenses_list.setter('height'))
        self.content_layout.add_widget(self.expenses_list)

        # Add content layout to scroll view
        self.scroll_view.add_widget(self.content_layout)
        self.main_layout.add_widget(self.scroll_view)

        # **Navigation Drawer**
        self.nav_drawer = MDNavigationDrawer(elevation=4)
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

        self.add_widget(self.main_layout)
        self.add_widget(self.nav_drawer)

    def on_enter(self):
        """Called when the screen is entered - refresh the expenses list"""
        self.refresh_expenses_list()

    def refresh_expenses_list(self):
        """Update the recent expenses list display"""
        self.expenses_list.clear_widgets()
        user_id = App.get_running_app().current_user_id  # Get the current user ID from the app instance
        print(f"Current User ID: {user_id}")  # Debugging print
        expenses = self.db.get_expenses_by_user_id(user_id)  # Fetch expenses for the current user
        print(f"Fetched Expenses: {expenses}")  # Debugging print

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

    def get_icon_for_expense_type(self, expense_type):
        """Return an appropriate icon based on expense type"""
        icon_map = {
            'Education': 'school',
            'Travel': 'airplane',
            'Groceries': 'cart',
            'Rent': 'home',
            'Utilities': 'flash',
            'Investments': 'chart-line',
            'Medical': 'hospital',
            'Pharmaceutical': 'pill',
            'Food': 'food',
            'Entertainment': 'movie',
            'Shopping': 'shopping',
        }
        return icon_map.get(expense_type, 'cash')

    def toggle_menu(self):
        """Opens or closes the navigation drawer."""
        self.nav_drawer.set_state("toggle")

    def open_tool(self, tool_screen):
        """Navigate to another tool screen"""
        self.manager.current = tool_screen
        self.nav_drawer.set_state("close")

    def show_expense_type_dropdown(self, instance):
        """Show a dropdown for selecting expense types."""
        menu_items = [
            {
                "text": type_exp,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=type_exp: self.set_expense_type(x),
            } for type_exp in self.expense_types
        ]
        self.expense_type_menu = MDDropdownMenu(
            caller=self.type_button,
            items=menu_items,
            width_mult=4,
            max_height=dp(250)
        )
        self.expense_type_menu.open()

    def set_expense_type(self, type_exp):
        """Set the selected expense type in the button."""
        self.type_button.text = type_exp
        self.expense_type_menu.dismiss()

    def show_date_picker(self, instance):
        """Open the custom date picker."""
        date_picker_popup = ImprovedDatePickerPopup(
            callback=self.set_date,
            initial_date=self.selected_date
        )
        date_picker_popup.open()

    def set_date(self, date):
        """Set the selected date on the button."""
        self.selected_date = date
        self.date_button.text = f"Date: {date.strftime('%Y-%m-%d')}"

    def log_expense(self, instance):
        """Add a new expense to the database"""
        name = self.name_input.text.strip()
        type_exp = self.type_button.text.strip()
        amount = self.amount_input.text.strip()
        date = self.selected_date.strftime('%Y-%m-%d')

        # Check if the date is in the future
        if self.selected_date > datetime.now():
            self.show_dialog("Error", "You cannot log an expense for a future date.")
            return

        if not name or not type_exp or not amount:
            self.show_dialog("Error", "All fields must be filled out.")
            return

        try:
            amount = float(amount)
            user_id = getattr(self.manager, 'current_user_id', 1)  # Default to 1 if not set
            self.db.add_expense(user_id, name, type_exp, amount, date)
            self.show_dialog("Success", "Expense logged successfully!")
            self.clear_inputs()
            self.refresh_expenses_list()  # Update the list to show the new expense
        except ValueError:
            self.show_dialog("Error", "Amount must be a number.")

    def show_expenses(self, instance):
        """Show all expenses in a detailed view"""
        expenses = self.db.show_expense()
        if not expenses:
            self.show_dialog("No Records", "No expenses recorded.")
            return

        # Sort expenses by date (latest first)
        expenses.sort(key=lambda x: datetime.strptime(x['exp_date'], '%Y-%m-%d'), reverse=True)

        # Create a scrollable dialog to display expenses
        content = ScrollView(size_hint=(1, None), height=dp(500))  # Increased height
        expenses_list = MDList()

        for exp in expenses:
            icon = IconLeftWidget(
                icon=self.get_icon_for_expense_type(exp['exp_type'])
            )
            item = TwoLineIconListItem(
                text=f"{exp['exp_name']} - ₹{exp['exp_amount']}",
                secondary_text=f"{exp['exp_type']} | {exp['exp_date']}",
            )
            item.add_widget(icon)
            expenses_list.add_widget(item)

        content.add_widget(expenses_list)

        dialog = MDDialog(
            title='All Expenses',
            type="custom",
            content_cls=content,
            size_hint=(0.7, 0.5),  # Adjusted size for better fit
            buttons=[
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def show_expense_details(self, expense):
        """Show detailed view of a single expense"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None)

        # Add widgets to the content
        content.add_widget(
            MDLabel(text=f"Name: {expense['exp_name']}", font_style="H6", size_hint_y=None, height=dp(30)))
        content.add_widget(MDLabel(text=f"Type: {expense['exp_type']}", size_hint_y=None, height=dp(30)))
        content.add_widget(MDLabel(text=f"Amount: ₹{expense['exp_amount']}", size_hint_y=None, height=dp(30)))
        content.add_widget(MDLabel(text=f"Date: {expense['exp_date']}", size_hint_y=None, height=dp(30)))

        # Calculate content height based on children
        content.height = sum(child.height + dp(10) for child in content.children)  # Add spacing

        dialog = MDDialog(
            title='Expense Details',
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="EDIT",
                    on_release=lambda x: self.edit_expense(expense, dialog)
                ),
                MDFlatButton(
                    text="DELETE",
                    on_release=lambda x: self.confirm_delete(expense, dialog)
                ),
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def edit_expense(self, expense, parent_dialog=None):
        """Open form to edit an expense"""
        if parent_dialog:
            parent_dialog.dismiss()

        # Prefill the form with existing data
        self.name_input.text = expense['exp_name']
        self.type_button.text = expense['exp_type']
        self.amount_input.text = str(expense['exp_amount'])
        self.date_button.text = f"Date: {expense['exp_date']}"

        # Create a layout for the dialog content
        edit_content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None)

        # Add labels and input fields to the dialog content with explicit heights
        title_label = MDLabel(
            text="Edit the details and confirm.",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )

        name_field = MDTextField(
            hint_text="Expense Name",
            text=self.name_input.text,
            size_hint_y=None,
            height=dp(48)
        )

        type_field = MDTextField(
            hint_text="Expense Type",
            text=self.type_button.text,
            size_hint_y=None,
            height=dp(48)
        )

        amount_field = MDTextField(
            hint_text="Amount",
            text=self.amount_input.text,
            size_hint_y=None,
            height=dp(48)
        )

        date_label = MDLabel(
            text=f"Current Date: {self.date_button.text}",
            size_hint_y=None,
            height=dp(30)
        )

        # Add all widgets to the content
        edit_content.add_widget(title_label)
        edit_content.add_widget(name_field)
        edit_content.add_widget(type_field)
        edit_content.add_widget(amount_field)
        edit_content.add_widget(date_label)

        # Calculate the total height based on the children
        edit_content.height = sum(child.height for child in edit_content.children) + len(edit_content.children) * dp(10)

        # Add a button to confirm the edit
        confirm_button = MDRaisedButton(
            text="Confirm Edit",
            size_hint_x=1
        )
        confirm_button.bind(on_release=lambda x: self.update_expense(expense['id']))

        # Create a dialog to confirm the edit
        edit_dialog = MDDialog(
            title='Edit Expense',
            type="custom",
            content_cls=edit_content,
            buttons=[confirm_button]
        )

        edit_dialog.open()
    def update_expense(self, expense_id):
        """Update the expense in the database"""
        name = self.name_input.text.strip()
        type_exp = self.type_button.text.strip()
        amount = self.amount_input.text.strip()
        date = self.selected_date.strftime('%Y-%m-%d')

        if not name or not type_exp or not amount:
            self.show_dialog("Error", "All fields must be filled out.")
            return

        try:
            amount = float(amount)
            self.db.update_expense(expense_id, name, type_exp, amount, date)  # Update the database
            self.show_dialog("Success", "Expense updated successfully!")
            self.clear_inputs()
            self.refresh_expenses_list()  # Refresh the list to show updated expense
        except ValueError:
            self.show_dialog("Error", "Amount must be a number.")

    def confirm_delete(self, expense, parent_dialog):
        """Show confirmation dialog before deleting an expense"""
        confirm_dialog = MDDialog(
            title="Confirm Deletion",
            text=f"Are you sure you want to delete this expense: {expense['exp_name']}?",
            size_hint=(0.9, 0.4),  # Adjusted size for better fit
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: confirm_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="DELETE",
                    on_release=lambda x: self.delete_expense(expense, parent_dialog, confirm_dialog)
                )
            ]
        )
        confirm_dialog.open()

    def delete_expense(self, expense, parent_dialog, confirm_dialog):
        """Delete the expense and close all dialogs"""
        self.db.delete_expense(expense['id'])  # Delete the expense by ID

        confirm_dialog.dismiss()
        if parent_dialog:
            parent_dialog.dismiss()

        self.refresh_expenses_list()
        self.show_dialog("Success", "Expense deleted successfully!")

    def show_dialog(self, title, message):
        """Show a simple dialog with a message"""
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def clear_inputs(self):
        """Reset all input fields"""
        self.name_input.text = ''
        self.type_button.text = ''
        self.amount_input.text = ''
        self.selected_date = datetime.now()
        self.date_button.text = f"Date: {self.selected_date.strftime('%Y-%m-%d')}"

    def update_expenses_list(self, expenses):
        """Update the displayed expenses list"""
        self.expenses_list.clear_widgets()

        if not expenses:
            self.expenses_list.add_widget(OneLineListItem(
                text="No expenses found",
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

    def show_expense_stats(self, instance):
        """Show expense statistics in a Spotify Wrapped style narrative"""
        user_id = App.get_running_app().current_user_id
        
        # Create a layout for time period selection
        time_period_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None)
        time_period_layout.bind(minimum_height=time_period_layout.setter('height'))  # Make it dynamic
        
        # Add a title
        time_period_layout.add_widget(MDLabel(
            text="Your Expense Story",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(40)
        ))
        
        # Add description
        time_period_layout.add_widget(MDLabel(
            text="Discover your spending habits in a personalized story.",
            halign="center",
            size_hint_y=None,
            height=dp(40)
        ))
        
        # Add time period buttons in a grid
        period_grid = GridLayout(cols=3, spacing=dp(10), size_hint_y=None)
        period_grid.bind(minimum_height=period_grid.setter('height'))  # Make it dynamic
        
        periods = [
            ("1 Week", "1w"),
            ("1 Month", "1m"),
            ("3 Months", "3m"),
            ("6 Months", "6m"),
            ("1 Year", "1y"),
            ("All Time", "all")
        ]
        
        for period_name, period_code in periods:
            btn = MDRaisedButton(
                text=period_name,
                size_hint=(None, None),
                width=dp(100),
                height=dp(40),
                md_bg_color=(0.2, 0.6, 0.9, 1)
            )
            btn.bind(on_release=lambda x, p=period_code: self.generate_expense_story(p))
            period_grid.add_widget(btn)
            
        time_period_layout.add_widget(period_grid)
        
        # Add a nice image or icon
        time_period_layout.add_widget(MDIcon(
            icon="finance",
            halign="center",
            font_size=dp(64),
            size_hint_y=None,
            height=dp(70)
        ))
        
        # Dialog for time period selection
        time_dialog = MDDialog(
            title="Your Financial Journey",
            type="custom",
            content_cls=time_period_layout,
            size_hint=(0.9, None),  # Width is 90% of the screen
            height=dp(400),  # Set a fixed height or adjust dynamically
            buttons=[
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: time_dialog.dismiss()
                )
            ]
        )
        
        time_dialog.open()

    def generate_expense_story(self, period):
        """Generate a narrative based on expense data for the selected time period"""
        user_id = App.get_running_app().current_user_id
        expenses = self.db.get_expenses_by_user_id(user_id)
        
        if not expenses:
            self.show_dialog("No Data", "You haven't logged any expenses yet.")
            return
        
        # Filter expenses based on selected time period
        today = datetime.now()
        filtered_expenses = []
        
        for expense in expenses:
            exp_date = datetime.strptime(expense['exp_date'], '%Y-%m-%d')
            if period == "1w" and (today - exp_date).days <= 7:
                filtered_expenses.append(expense)
            elif period == "1m" and (today - exp_date).days <= 30:
                filtered_expenses.append(expense)
            elif period == "3m" and (today - exp_date).days <= 90:
                filtered_expenses.append(expense)
            elif period == "6m" and (today - exp_date).days <= 180:
                filtered_expenses.append(expense)
            elif period == "1y" and (today - exp_date).days <= 365:
                filtered_expenses.append(expense)
            elif period == "all":
                filtered_expenses.append(expense)
        
        if not filtered_expenses:
            self.show_dialog("No Data", f"No expenses found for the selected period.")
            return
        
        # Calculate insights
        self.total_spent = sum(float(expense['exp_amount']) for expense in filtered_expenses)
        
        # Group by category
        categories = {}
        for expense in filtered_expenses:
            category = expense['exp_type']
            if category in categories:
                categories[category] += float(expense['exp_amount'])
            else:
                categories[category] = float(expense['exp_amount'])
        
        # Sort categories by amount
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        self.top_category = sorted_categories[0][0] if sorted_categories else "None"
        top_amount = sorted_categories[0][1] if sorted_categories else 0
        
        # Get the frequency of expenses
        expense_dates = [datetime.strptime(exp['exp_date'], '%Y-%m-%d') for exp in filtered_expenses]
        date_counts = {}
        for date in expense_dates:
            day_of_week = date.strftime('%A')
            if day_of_week in date_counts:
                date_counts[day_of_week] += 1
            else:
                date_counts[day_of_week] = 1
        
        self.most_active_day = max(date_counts.items(), key=lambda x: x[1])[0] if date_counts else "None"
        
        # Find the biggest single expense
        self.biggest_expense = max(filtered_expenses, key=lambda x: float(x['exp_amount']), default={"exp_amount": 0, "exp_name": "None", "exp_date": "N/A"})
        
        # Generate a narrative
        period_text = {
            "1w": "this week",
            "1m": "this month",
            "3m": "the past 3 months",
            "6m": "the past 6 months",
            "1y": "this year",
            "all": "all time"
        }[period]
        
        # Calculate percentage of top category
        top_category_percentage = (top_amount / self.total_spent) * 100
        
        # Find unique categories
        unique_categories = len(categories)
        
        # Create a personalized story
        story_layout = MDGridLayout(
            cols=1,
            spacing=dp(20),
            padding=dp(20),
            size_hint=(1, None),
            height=dp(700)  # Will be adjusted based on content
        )
        
        # Style classes for different sections
        section_styles = [
            {"bg_color": (0.2, 0.5, 0.9, 0.2), "icon": "cash"},
            {"bg_color": (0.9, 0.3, 0.5, 0.2), "icon": "cart"},
            {"bg_color": (0.5, 0.8, 0.2, 0.2), "icon": "trending-up"},
            {"bg_color": (0.8, 0.4, 0.2, 0.2), "icon": "calendar-clock"},
            {"bg_color": (0.4, 0.3, 0.8, 0.2), "icon": "finance"}
        ]
        
        # Create section 1 - Total spending
        section1 = self.create_story_section(
            f"₹{self.total_spent:.2f}",
            f"That's how much you spent {period_text}!",
            section_styles[0]["bg_color"],
            section_styles[0]["icon"]
        )
        story_layout.add_widget(section1)
        
        # Create section 2 - Top category
        section2 = self.create_story_section(
            f"{self.top_category}",
            f"You spent {top_category_percentage:.1f}% of your money on {self.top_category}. It's your top category {period_text}!",
            section_styles[1]["bg_color"],
            section_styles[1]["icon"]
        )
        story_layout.add_widget(section2)
        
        # Create section 3 - Spending day
        section3 = self.create_story_section(
            f"{self.most_active_day}s",
            f"That's when you're most likely to spend money. Do you have a {self.most_active_day} ritual?",
            section_styles[3]["bg_color"],
            section_styles[3]["icon"]
        )
        story_layout.add_widget(section3)
        
        # Create section 4 - Biggest expense
        section4 = self.create_story_section(
            f"₹{float(self.biggest_expense['exp_amount']):.2f}",
            f"Your largest single expense was {self.biggest_expense['exp_name']} on {self.biggest_expense['exp_date']}. Big day?",
            section_styles[2]["bg_color"],
            section_styles[2]["icon"]
        )
        story_layout.add_widget(section4)
        
        # Create a fun personality section
        personality = self.generate_spending_personality(
            categories, 
            self.total_spent, 
            len(filtered_expenses), 
            self.biggest_expense
        )
        
        section5 = self.create_story_section(
            personality[0],
            personality[1],
            section_styles[4]["bg_color"],
            section_styles[4]["icon"]
        )
        story_layout.add_widget(section5)
        
        # Calculate the actual height needed
        total_height = 0
        for child in story_layout.children:
            total_height += child.height + dp(20)  # Add spacing
        
        story_layout.height = total_height
        
        # Put everything in a scroll view
        scroll_view = ScrollView(size_hint=(1, None), height=dp(500))
        scroll_view.add_widget(story_layout)
        
        # Show the story in a dialog
        story_dialog = MDDialog(
            title=f"Your {period_text.capitalize()} in Expenses",
            type="custom",
            content_cls=scroll_view,
            size_hint=(0.9, None),  # Width is 90% of the screen
            height=dp(total_height + 100),  # Adjust height dynamically based on content
            buttons=[
                MDRaisedButton(
                    text="SHARE",
                    md_bg_color=(0.3, 0.6, 0.9, 1),
                    on_release=lambda x: self.share_story()
                ),
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: story_dialog.dismiss()
                )
            ]
        )
        
        story_dialog.open()
    
    def create_story_section(self, title, description, bg_color, icon):
        """Create a styled section for the story"""
        section = MDCard(
            size_hint=(1, None),
            height=dp(120),
            md_bg_color=bg_color,
            radius=[dp(10)],
            padding=dp(16)
        )
        
        # Layout for the section content
        content = MDBoxLayout(orientation='horizontal')
        
        # Icon on the left
        icon_widget = MDIcon(
            icon=icon,
            font_size=dp(48),
            size_hint=(0.2, 1)
        )
        
        # Text on the right
        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(0.8, 1),
            padding=[0, 0, 0, 0]
        )
        
        title_label = MDLabel(
            text=title,
            font_style="H5",
            size_hint=(1, None),
            height=dp(40)
        )
        
        desc_label = MDLabel(
            text=description,
            size_hint=(1, None),
            height=dp(60)
        )
        
        text_layout.add_widget(title_label)
        text_layout.add_widget(desc_label)
        
        content.add_widget(icon_widget)
        content.add_widget(text_layout)
        
        section.add_widget(content)
        return section
    
    def generate_spending_personality(self, categories, total_spent, num_expenses, biggest_expense):
        """Generate a fun personality type based on spending habits"""
        # Determine personality based on categories and habits
        if 'Food' in categories and categories['Food'] > total_spent * 0.3:
            return "The Foodie", "You love your food! A significant portion of your spending goes to satisfying your taste buds. Bon appétit!"
            
        elif 'Education' in categories and categories['Education'] > total_spent * 0.2:
            return "The Knowledge Seeker", "You're investing in yourself and your future. Knowledge is power, and you're powering up!"
            
        elif 'Shopping' in categories and categories['Shopping'] > total_spent * 0.25:
            return "The Retail Therapist", "Shopping seems to be your go-to activity. Each purchase tells a story in your life's journey!"
            
        elif 'Travel' in categories and categories['Travel'] > 0:
            return "The Explorer", "You value experiences over things. Your spending shows you're creating memories that will last a lifetime!"
            
        elif 'Entertainment' in categories and categories['Entertainment'] > total_spent * 0.15:
            return "The Fun Seeker", "Life's too short not to enjoy it! You prioritize having a good time, and that's worth celebrating."
            
        elif 'Investments' in categories and categories['Investments'] > total_spent * 0.2:
            return "The Future Planner", "You're thinking long-term with your money. Smart moves now can lead to financial freedom later!"
            
        elif num_expenses > 30 and total_spent / num_expenses < 500:
            return "The Micro-Manager", "You make lots of small purchases rather than a few big ones. You're attentive to the details of life!"
            
        elif float(biggest_expense['exp_amount']) > total_spent * 0.4:
            return "The Big Spender", "When you decide to spend, you go all in! You're not afraid to invest significantly in what matters to you."
            
        else:
            return "The Balanced Spender", "Your spending is diverse and balanced across categories. You've got a well-rounded financial life!"
    
    def share_story(self):
        """Copy the expense story to the clipboard"""
        # Generate the story text based on the current stats
        story_text = self.generate_expense_story_text()  # Create a method to generate the story text
        Clipboard.copy(story_text)  # Copy the story text to the clipboard
        self.show_dialog("Share", "Your expense story has been copied to the clipboard and is ready to share!")

    def generate_expense_story_text(self):
        """Generate the text for the expense story"""
        # This method should return a string that represents the expense story
        # You can customize this based on the data you have
        # For example:
        return (
            f"Total Spent: ₹{self.total_spent:.2f}\n"
            f"Top Category: {self.top_category}\n"
            f"Most Active Day: {self.most_active_day}s\n"
            f"Biggest Expense: ₹{self.biggest_expense['exp_amount']} on {self.biggest_expense['exp_name']}.\n"
            f"Your spending habits are unique and reflect your lifestyle!"
        )

class ImprovedDatePickerPopup(Popup):
    """An improved date picker with month and year navigation"""

    def __init__(self, callback, initial_date=None, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.title = "Select Date"
        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = True

        # Set initial date (or use current date)
        if initial_date:
            self.current_date = initial_date
        else:
            self.current_date = datetime.now()

        self.selected_month = self.current_date.month
        self.selected_year = self.current_date.year
        self.selected_day = self.current_date.day

        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Set background color using canvas
        with main_layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(1, 1, 1, 1)  # White color
            self.rect = Rectangle(size=main_layout.size, pos=main_layout.pos)

        # Bind the size and position of the rectangle to the layout
        main_layout.bind(size=self._update_rect, pos=self._update_rect)

        # Month/Year navigation
        nav_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))

        # Previous month button
        prev_month_btn = MDRaisedButton(
            text="<",
            on_release=self.prev_month
        )

        # Month/Year display
        self.month_year_label = MDLabel(
            text=f"{calendar.month_name[self.selected_month]} {self.selected_year}",
            halign="center"
        )

        # Next month button
        next_month_btn = MDRaisedButton(
            text=">",
            on_release=self.next_month
        )

        nav_layout.add_widget(prev_month_btn)
        nav_layout.add_widget(self.month_year_label)
        nav_layout.add_widget(next_month_btn)
        main_layout.add_widget(nav_layout)

        # Weekday headers
        weekdays_layout = GridLayout(cols=7, size_hint_y=None, height=dp(30))
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            weekdays_layout.add_widget(MDLabel(text=day, halign="center"))
        main_layout.add_widget(weekdays_layout)

        # Calendar grid for days
        self.days_grid = GridLayout(cols=7, spacing=(2, 2))
        main_layout.add_widget(self.days_grid)

        # Populate the calendar
        self.update_calendar()

        # Bottom buttons
        buttons_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

        # Today button
        today_btn = MDRaisedButton(
            text="Today",
            on_release=self.select_today
        )

        # Cancel button
        cancel_btn = MDFlatButton(
            text="Cancel",
            on_release=self.dismiss
        )

        buttons_layout.add_widget(today_btn)
        buttons_layout.add_widget(cancel_btn)
        main_layout.add_widget(buttons_layout)

        self.content = main_layout

    def _update_rect(self, instance, value):
        """Update the rectangle size and position"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def update_calendar(self):
        """Update the calendar grid with days for the current month/year"""
        self.days_grid.clear_widgets()

        # Update month/year label
        self.month_year_label.text = f"{calendar.month_name[self.selected_month]} {self.selected_year}"

        # Get the calendar for this month
        cal = calendar.monthcalendar(self.selected_year, self.selected_month)

        # Add day buttons to the grid
        for week in cal:
            for day in week:
                if day == 0:  # Day is not part of this month
                    self.days_grid.add_widget(Button(
                        text="",
                        background_color=(0, 0, 0, 0),
                        disabled=True
                    ))
                else:
                    day_btn = Button(
                        text=str(day),
                        on_release=self.select_date,
                        color=(1, 1, 1, 1)  # Set text color to white
                    )

                    # Highlight current day
                    if (day == self.current_date.day and
                            self.selected_month == self.current_date.month and
                            self.selected_year == self.current_date.year):
                        day_btn.background_color = (0.3, 0.6, 1, 1)  # Highlight color

                    # Highlight selected day
                    if (day == self.selected_day and
                            self.selected_month == self.current_date.month and
                            self.selected_year == self.current_date.year):
                        day_btn.background_color = (0.2, 0.8, 0.2, 1)  # Selection color

                    self.days_grid.add_widget(day_btn)

    def prev_month(self, instance):
        """Go to previous month"""
        if self.selected_month == 1:
            self.selected_month = 12
            self.selected_year -= 1
        else:
            self.selected_month -= 1
        self.update_calendar()

    def next_month(self, instance):
        """Go to next month"""
        if self.selected_month == 12:
            self.selected_month = 1
            self.selected_year += 1
        else:
            self.selected_month += 1
        self.update_calendar()

    def select_today(self, instance):
        """Select today's date and close popup"""
        today = datetime.now()
        self.callback(today)
        self.dismiss()

    def select_date(self, instance):
        """Select a date and close the popup."""
        day = int(instance.text)

        # Create date object and call the callback
        try:
            selected_date = datetime(self.selected_year, self.selected_month, day)
            self.callback(selected_date)
            self.dismiss()
        except ValueError as e:
            print(f"Invalid date: {e}")