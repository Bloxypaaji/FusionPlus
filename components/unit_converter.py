from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.menu import MDDropdownMenu


class UnitConverter(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        # Define units and conversion factors
        self.units = {
            "Length": ["Inches", "Feet", "Miles", "Centimeters", "Meters", "Kilometers"],
            "Weight": ["Pounds", "Kilograms"],
            "Temperature": ["Fahrenheit", "Celsius"]
        }
        self.conversion_factors = {
            "Inches": {"Centimeters": 2.54, "Feet": 1 / 12, "Meters": 0.0254},
            "Feet": {"Inches": 12, "Meters": 0.3048, "Kilometers": 0.0003048},
            "Miles": {"Kilometers": 1.60934, "Feet": 5280},
            "Centimeters": {"Inches": 1 / 2.54, "Meters": 0.01},
            "Meters": {"Centimeters": 100, "Feet": 1 / 0.3048, "Kilometers": 0.001},
            "Kilometers": {"Miles": 1 / 1.60934, "Meters": 1000},
            "Pounds": {"Kilograms": 0.453592},
            "Kilograms": {"Pounds": 1 / 0.453592},
            "Fahrenheit": {"Celsius": lambda f: (f - 32) * 5 / 9},
            "Celsius": {"Fahrenheit": lambda c: (c * 9 / 5) + 32}
        }

        # UI Layout
        self.layout = BoxLayout(orientation="vertical", spacing=10)

        # Top App Bar with Hamburger Menu
        self.toolbar = MDTopAppBar(
            title="Unit Converter",
            left_action_items=[["menu", lambda x: self.toggle_menu()]],
            md_bg_color=(0.129, 0.588, 0.953, 1)
        )
        self.layout.add_widget(self.toolbar)

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

        # Input Layout (From Unit)
        self.input_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=60)
        self.input_field = MDTextField(hint_text="Enter value", input_filter="float", size_hint_x=0.7, font_size="18sp",
                                       mode="rectangle")
        self.from_unit_button = MDRaisedButton(text="Select Unit", size_hint_x=0.3,
                                               on_release=lambda _: self.show_menu("from"))
        self.input_layout.add_widget(self.input_field)
        self.input_layout.add_widget(self.from_unit_button)
        self.layout.add_widget(self.input_layout)

        # Output Layout (To Unit)
        self.output_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=60)
        self.output_field = MDTextField(hint_text="Result", readonly=True, size_hint_x=0.7, font_size="18sp",
                                        mode="rectangle")
        self.to_unit_button = MDRaisedButton(text="Select Unit", size_hint_x=0.3,
                                             on_release=lambda _: self.show_menu("to"))
        self.output_layout.add_widget(self.output_field)
        self.output_layout.add_widget(self.to_unit_button)
        self.layout.add_widget(self.output_layout)

        # Output Unit Label
        self.output_label = Label(text="", font_size="18sp", size_hint_y=None, height=40, halign="center")
        self.layout.add_widget(self.output_label)

        # Convert Button (Centered & Large)
        self.button_layout = BoxLayout(size_hint_y=None, height=80)
        self.convert_button = MDRaisedButton(
            text="Convert", md_bg_color=(0.129, 0.588, 0.953, 1),
            size_hint_x=0.5, size_hint_y=None, height=60,
            pos_hint={"center_x": 0.5}, on_release=lambda _: self.convert()
        )
        self.button_layout.add_widget(Widget(size_hint_x=0.25))  # Left spacing
        self.button_layout.add_widget(self.convert_button)
        self.button_layout.add_widget(Widget(size_hint_x=0.25))  # Right spacing
        self.layout.add_widget(self.button_layout)

        # Bottom Spacing
        self.layout.add_widget(Widget(size_hint_y=1))

        # Add Widgets in Correct Order
        self.add_widget(self.layout)
        self.add_widget(self.nav_drawer)

    def show_menu(self, unit_type):
        menu_items = []
        for category, units in self.units.items():
            for unit in units:
                menu_items.append({
                    "text": unit,
                    "on_release": lambda x=unit, ut=unit_type: self.set_unit(x, ut)
                })

        caller = self.from_unit_button if unit_type == "from" else self.to_unit_button

        self.menu = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=4
        )

        self.menu.open()

    def set_unit(self, unit, unit_type):
        if unit_type == 'from':
            self.from_unit_button.text = unit
        else:
            self.to_unit_button.text = unit
        self.menu.dismiss()

    def convert(self):
        input_text = self.input_field.text
        from_unit = self.from_unit_button.text
        to_unit = self.to_unit_button.text

        if not input_text:
            self.output_field.text = ""
            self.output_label.text = "Please enter a value"
            return

        if from_unit == "Select Unit" or to_unit == "Select Unit":
            self.output_field.text = ""
            self.output_label.text = "Please select units"
            return

        if from_unit == to_unit:
            self.output_field.text = input_text
            self.output_label.text = to_unit
            return

        try:
            value = float(input_text)
            result = self.convert_units(value, from_unit, to_unit)

            if result is not None:
                self.output_field.text = f"{result:.2f}"
                self.output_label.text = to_unit
            else:
                self.output_field.text = ""
                self.output_label.text = "Invalid conversion"
        except ValueError:
            self.output_field.text = ""
            self.output_label.text = "Invalid input"

    def convert_units(self, value, from_unit, to_unit):
        """ Multi-step conversion if direct conversion is unavailable. """
        if from_unit in self.conversion_factors and to_unit in self.conversion_factors[from_unit]:
            factor = self.conversion_factors[from_unit][to_unit]
            return factor(value) if callable(factor) else value * factor

        for intermediate_unit in ["Meters", "Kilograms", "Celsius"]:
            if from_unit in self.conversion_factors and intermediate_unit in self.conversion_factors[from_unit]:
                step1 = self.convert_units(value, from_unit, intermediate_unit)
                if step1 is not None and to_unit in self.conversion_factors[intermediate_unit]:
                    return self.convert_units(step1, intermediate_unit, to_unit)

        return None

    def toggle_menu(self):
        self.nav_drawer.set_state("toggle")

    def open_tool(self, tool_name):
        self.manager.current = tool_name
        self.nav_drawer.set_state("close")
