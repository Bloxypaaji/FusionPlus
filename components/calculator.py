import math
import re
import numpy as np
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import OneLineListItem, MDList
from kivy.uix.scrollview import ScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from sympy import symbols, Eq, solve, latex, sympify, diff, integrate
from kivy.metrics import dp  # Ensure dp is imported


class EquationSolver(MDBoxLayout):
    """A component for solving polynomial equations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 10
        self.padding = 15
        self.size_hint_y = None
        self.height = 400

        # Equation Input
        self.equation_input = MDTextField(
            hint_text="Enter equation (e.g., x**2 - 4*x + 3 = 0)",
            font_size=18,
            size_hint=(1, None),
            height="50dp",
            helper_text="Use Python syntax (e.g., x**2 for x²)",
            helper_text_mode="on_focus"
        )

        # Solve Button
        solve_button = MDRaisedButton(
            text="Solve",
            font_size=16,
            size_hint=(1, None),
            height="50dp",
            on_release=self.solve_equation
        )

        # Result Section
        self.result_scroll = ScrollView(size_hint=(1, None), height=250)
        self.result_label = MDLabel(
            text="Solutions will appear here",
            font_size=16,
            halign="left",
            size_hint_y=None,
            padding=(10, 10)
        )
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        self.result_scroll.add_widget(self.result_label)

        # Add widgets to layout
        self.add_widget(self.equation_input)
        self.add_widget(solve_button)
        self.add_widget(self.result_scroll)

    def solve_equation(self, instance):
        """Solves the polynomial equation and displays the result."""
        equation_str = self.equation_input.text.strip()

        try:
            # Parse equation (handle both formats: "expression = 0" and just "expression")
            if "=" in equation_str:
                left, right = equation_str.split("=", 1)
                left = left.strip()
                right = right.strip()
                equation_str = f"({left}) - ({right})"

            # Create a symbolic variable
            x = symbols('x')

            # Convert string to symbolic expression
            expr = sympify(equation_str)

            # Solve the equation
            solutions = solve(expr, x)

            if not solutions:
                self.result_label.text = "No solutions found."
                return

            # Format results
            result_text = "Solutions:\n\n"
            for i, sol in enumerate(solutions):
                result_text += f"x{i + 1} = {sol}\n\n"

            # Add the factored form if it's a polynomial
            try:
                factored = expr.factor()
                result_text += f"Factored form:\n{factored} = 0\n\n"
            except:
                pass

            self.result_label.text = result_text

        except Exception as e:
            self.result_label.text = f"Error: {str(e)}\n\nPlease check your equation format."


class Calculator(MDScreen):
    def __init__(self, app=None, **kwargs):
        self.app = app
        kwargs.pop("app", None)
        super().__init__(**kwargs)

        # Set theme colors directly
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Blue"

        # Initialize the last answer
        self.last_answer = None
        self.is_rad_mode = True  # Default to radians for trig functions

        # 🔹 **Main Layout**
        self.layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)

        # 🔹 **Top Navigation Bar**
        self.top_bar = MDTopAppBar(
            title="Fusion+ - Calculator",
            left_action_items=[["menu", lambda x: self.toggle_menu()]],
            elevation=2,
            pos_hint={"top": 1}
        )

        # 🔹 **Navigation Drawer**
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

        # 🔹 **Display Area (Two parts - input and history)**
        self.display_box = MDBoxLayout(orientation="vertical", size_hint_y=None, height="120dp")

        # History display (shows previous calculation)
        self.history_display = MDLabel(
            text="",
            font_style="Caption",
            halign="right",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )

        # Main input box
        self.input_box = MDTextField(
            hint_text="Enter expression",
            font_size=32,
            halign="right",
            size_hint_y=None,
            height="60dp",
        )

        # Error label
        self.error_label = Label(
            text="",
            color=(1, 0, 0, 1),
            size_hint_y=None,
            height="30dp"
        )

        # Add display components
        self.display_box.add_widget(self.history_display)
        self.display_box.add_widget(self.input_box)
        self.display_box.add_widget(self.error_label)

        # 🔹 **Button Grid Layout with improved styling**
        self.button_layout = GridLayout(cols=4, spacing=8, padding=[5, 5, 5, 5])

        # Button configuration with categories
        buttons = [
            # Row 1 - Clear and basic operations
            [{"text": "C", "type": "clear"}, {"text": "CE", "type": "clear"},
             {"text": "√", "type": "function"}, {"text": "+", "type": "operator"}],
            # Row 2 - Trig functions and operations
            [{"text": "sin", "type": "function"}, {"text": "cos", "type": "function"},
             {"text": "tan", "type": "function"}, {"text": "-", "type": "operator"}],
            # Row 3 - Numbers and operations
            [{"text": "7", "type": "number"}, {"text": "8", "type": "number"},
             {"text": "9", "type": "number"}, {"text": "*", "type": "operator"}],
            # Row 4 - Numbers and operations
            [{"text": "4", "type": "number"}, {"text": "5", "type": "number"},
             {"text": "6", "type": "number"}, {"text": "/", "type": "operator"}],
            # Row 5 - Numbers and operations
            [{"text": "1", "type": "number"}, {"text": "2", "type": "number"},
             {"text": "3", "type": "number"}, {"text": "^", "type": "operator"}],
            # Row 6 - Numbers and brackets
            [{"text": "0", "type": "number"}, {"text": ".", "type": "number"},
             {"text": "(", "type": "bracket"}, {"text": ")", "type": "bracket"}],
            # Row 7 - Functions and constants
            [{"text": "log", "type": "function"}, {"text": "ln", "type": "function"},
             {"text": "π", "type": "constant"}, {"text": "e", "type": "constant"}],
            # Row 8 - Special functions
            [{"text": "x!", "type": "function"}, {"text": "rad", "type": "mode"},
             {"text": "deg", "type": "mode"}, {"text": "Ans", "type": "memory"}],
            # Row 9 - Advanced features
            [{"text": "Polynomial", "type": "tool"}, {"text": "Linear Algebra", "type": "tool"},
             {"text": "Binary Converter", "type": "tool"},{"text": "=", "type": "equals"}],
        ]

        # Create buttons with proper styling based on type
        for row in buttons:
            for btn_info in row:
                # Ensure btn_info is a dictionary with expected keys
                if isinstance(btn_info, dict) and "text" in btn_info and "type" in btn_info:
                    btn_type = btn_info["type"]
                    text = btn_info["text"]
                    # Updated Light Material UI Color Palette for Black Text
                    if btn_type == "operator":
                        md_bg_color = [0.68, 0.85, 0.90, 1]  # Light Sky Blue
                    elif btn_type == "equals":
                        md_bg_color = [0.76, 0.91, 0.62, 1]  # Soft Green
                    elif btn_type == "clear":
                        md_bg_color = [1.0, 0.71, 0.71, 1]  # Gentle Coral
                    elif btn_type == "function":
                        md_bg_color = [1.0, 0.85, 0.56, 1]  # Soft Amber
                    elif btn_type == "tool":
                        md_bg_color = [0.88, 0.88, 0.88, 1]  # Light Gray
                    else:
                        md_bg_color = [0.95, 0.95, 0.95, 1]  # Crisp Off-White

                    button = MDRaisedButton(
                        text=text,
                        font_size=18,
                        size_hint=(1, None),
                        height="50dp",
                        md_bg_color=md_bg_color,
                        text_color=[0, 0, 0, 1]
                    )
                    button.bind(on_press=self.on_button_press)
                    self.button_layout.add_widget(button)
                else:
                    print(f"Warning: Button configuration is not valid for {btn_info}")

        # 🔹 **Scrollable View for buttons**
        self.scroll_view = ScrollView()
        self.scroll_view.add_widget(self.button_layout)

        # 🔹 **Adding Widgets to Layout**
        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.display_box)
        self.layout.add_widget(self.scroll_view)
        self.add_widget(self.layout)
        self.add_widget(self.nav_drawer)

        # History of calculations for step-wise solutions
        self.calculation_steps = []

    def create_button(self, label, bg_color=None):
        """Create calculator buttons with improved styling."""
        if bg_color is None:
            bg_color = [0.3, 0.3, 0.3, 1]  # Default dark gray

        button = MDRaisedButton(
            text=label,
            font_size=18,
            size_hint=(1, None),
            height="50dp",
            elevation=2,
            md_bg_color=bg_color,
            text_color=[1, 1, 1, 1]
        )
        button.bind(on_press=self.on_button_press)
        return button

    def on_button_press(self, instance):
        """Handle button presses with improved functionality."""
        current = self.input_box.text.strip()
        button_text = instance.text
        self.error_label.text = ""

        try:
            if button_text == "C":
                # Clear all
                self.input_box.text = ""
                self.history_display.text = ""
                self.calculation_steps = []
            elif button_text == "CE":
                # Clear entry (last character)
                self.input_box.text = current[:-1]
            elif button_text == "=":
                # Calculate and store result
                self.history_display.text = current
                self.calculation_steps = []  # Reset steps for new calculation
                self.last_answer = self.evaluate_expression(current)
                self.input_box.text = str(self.last_answer)
            elif button_text == "Ans":
                # Insert last answer
                if self.last_answer is not None:
                    self.input_box.text += str(self.last_answer)
            elif button_text == "Binary Converter":
                # Open binary converter dialog
                self.open_binary_converter()
            elif button_text == "Polynomial":
                # Open polynomial solver dialog
                self.open_polynomial_solver()
            elif button_text == "Linear Algebra":
                # Open linear algebra dialog
                self.open_linear_algebra_dialog()
            elif button_text == "√":
                self.input_box.text += "sqrt("
            elif button_text == "^":
                self.input_box.text += "^"
            elif button_text == "π":
                self.input_box.text += str(math.pi)
            elif button_text == "e":
                self.input_box.text += str(math.e)
            elif button_text in ["sin", "cos", "tan", "log", "ln"]:
                self.input_box.text += f"{button_text}("
            elif button_text == "x!":
                # Handle factorial
                if current:
                    try:
                        num = float(eval(current))
                        if num.is_integer() and num >= 0:
                            self.input_box.text = str(math.factorial(int(num)))
                        else:
                            self.error_label.text = "Factorial requires a non-negative integer"
                    except:
                        self.error_label.text = "Cannot calculate factorial"
            elif button_text == "rad":
                # Switch to radian mode
                self.is_rad_mode = True
                self.error_label.text = "Radian mode activated"
            elif button_text == "deg":
                # Switch to degree mode
                self.is_rad_mode = False
                self.error_label.text = "Degree mode activated"
            else:
                # Add the button text to the input
                self.input_box.text += button_text
        except Exception as e:
            self.error_label.text = f"Error: {str(e)}"

    def evaluate_expression(self, expression):
        """Convert infix to postfix and evaluate the result with step tracking."""
        try:
            # Preprocess the expression
            expression = expression.replace("^", "**")

            # Record the initial step
            self.calculation_steps.append(f"Original: {expression}")

            # Handle special functions
            expression = self.handle_special_functions(expression)

            # Evaluate using Python's eval for simplicity and safety
            result = eval(expression)

            # Record the final result
            self.calculation_steps.append(f"Result: {result}")

            return result
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Error: {str(e)}"

    def handle_special_functions(self, expression):
        """Process special mathematical functions in the expression."""
        # Replace sqrt with math.sqrt
        expression = re.sub(r'sqrt\(', 'math.sqrt(', expression)

        # Handle trigonometric functions based on the current mode
        if "sin(" in expression or "cos(" in expression or "tan(" in expression:
            if not self.is_rad_mode:
                # In degree mode, convert the argument to radians
                expression = re.sub(r'sin\((.+?)\)', r'math.sin(math.radians(\1))', expression)
                expression = re.sub(r'cos\((.+?)\)', r'math.cos(math.radians(\1))', expression)
                expression = re.sub(r'tan\((.+?)\)', r'math.tan(math.radians(\1))', expression)
            else:
                # In radian mode, use the angles directly
                expression = re.sub(r'sin\(', 'math.sin(', expression)
                expression = re.sub(r'cos\(', 'math.cos(', expression)
                expression = re.sub(r'tan\(', 'math.tan(', expression)

        # Handle logarithmic functions
        expression = re.sub(r'log\(', 'math.log10(', expression)
        expression = re.sub(r'ln\(', 'math.log(', expression)

        # Record the processed expression for steps
        self.calculation_steps.append(f"Processed: {expression}")

        return expression

    def toggle_menu(self):
        """Opens or closes the navigation drawer."""
        self.nav_drawer.set_state("toggle")

    def open_tool(self, tool_name):
        """Navigates to the selected tool."""
        self.manager.current = tool_name
        self.nav_drawer.set_state("close")

    def open_polynomial_solver(self):
        """Open the equation solver in a dialog."""
        self.equation_solver = EquationSolver()
        dialog = MDDialog(
            title="Polynomial Equation Solver",
            type="custom",
            content_cls=self.equation_solver,
            buttons=[
                MDRaisedButton(
                    text="CLOSE",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
            size_hint=(0.9, None),
            height=500
        )
        dialog.open()

    def open_linear_algebra_dialog(self):
        """Open a dialog for linear algebra operations."""
        content = MDBoxLayout(orientation='vertical', padding=15, spacing=10, size_hint_y=None, height=400)

        # Matrix size selection
        size_box = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=50, spacing=10)
        size_box.add_widget(MDLabel(text="Matrix Size:", size_hint=(0.3, None), height=50))

        self.rows_input = MDTextField(
            hint_text="Rows",
            input_filter="int",
            size_hint=(0.35, None),
            height=50
        )
        self.cols_input = MDTextField(
            hint_text="Columns",
            input_filter="int",
            size_hint=(0.35, None),
            height=50
        )

        size_box.add_widget(self.rows_input)
        size_box.add_widget(self.cols_input)
        content.add_widget(size_box)

        # Operation selection
        operation_box = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=50)
        operation_box.add_widget(MDLabel(text="Operation:", size_hint=(0.3, None), height=50))

        self.operation_input = MDTextField(
            hint_text="det, inv, solve, etc.",
            size_hint=(0.7, None),
            height=50
        )
        operation_box.add_widget(self.operation_input)
        content.add_widget(operation_box)

        # Matrix input
        self.matrix_input = MDTextField(
            hint_text="Enter matrix elements separated by commas and rows by semicolons\n(e.g., 1,2,3;4,5,6)",
            multiline=True,
            size_hint=(1, None),
            height=100
        )
        content.add_widget(self.matrix_input)

        # For linear systems: b vector input
        self.vector_input = MDTextField(
            hint_text="For solving Ax=b, enter b vector (e.g., 1,2,3)",
            size_hint=(1, None),
            height=50
        )
        content.add_widget(self.vector_input)

        # Calculate button
        calculate_button = MDRaisedButton(
            text="Calculate",
            on_release=self.perform_linear_algebra,
            size_hint=(1, None),
            height=50
        )
        content.add_widget(calculate_button)

        # Result display
        self.la_result = MDLabel(
            text="Result will appear here",
            size_hint=(1, None),
            height=50
        )
        content.add_widget(self.la_result)

        dialog = MDDialog(
            title="Linear Algebra Solver",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="CLOSE",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
            size_hint=(0.9, None)
        )
        dialog.open()

    def perform_linear_algebra(self, instance):
        """Perform linear algebra operations based on user input."""
        try:
            # Parse matrix input
            matrix_str = self.matrix_input.text.strip()
            if not matrix_str:
                self.la_result.text = "Please enter a matrix"
                return

            # Parse matrix: rows separated by semicolons, elements by commas
            rows = matrix_str.split(';')
            matrix = []
            for row in rows:
                elements = [float(x.strip()) for x in row.split(',')]
                matrix.append(elements)

            A = np.array(matrix)
            operation = self.operation_input.text.strip().lower()

            # Perform the requested operation
            if operation == "det":
                result = np.linalg.det(A)
                self.la_result.text = f"Determinant: {result:.4f}"

            elif operation == "inv":
                if A.shape[0] != A.shape[1]:
                    self.la_result.text = "Error: Matrix must be square for inversion"
                    return
                result = np.linalg.inv(A)
                result_str = "Inverse Matrix:\n"
                for row in result:
                    result_str += " ".join([f"{x:.4f}" for x in row]) + "\n"
                self.la_result.text = result_str

            elif operation == "solve":
                # For solving Ax=b linear systems
                vector_str = self.vector_input.text.strip()
                if not vector_str:
                    self.la_result.text = "Please enter vector b for solving Ax=b"
                    return

                b = np.array([float(x.strip()) for x in vector_str.split(',')])
                if A.shape[0] != len(b):
                    self.la_result.text = "Error: Matrix rows must match vector length"
                    return

                x = np.linalg.solve(A, b)
                result_str = "Solution x:\n"
                for i, val in enumerate(x):
                    result_str += f"x{i + 1} = {val:.4f}\n"
                self.la_result.text = result_str

            elif operation == "eigen":
                if A.shape[0] != A.shape[1]:
                    self.la_result.text = "Error: Matrix must be square for eigenvalues"
                    return

                eigenvalues, eigenvectors = np.linalg.eig(A)
                result_str = "Eigenvalues:\n"
                for i, val in enumerate(eigenvalues):
                    result_str += f"λ{i + 1} = {val:.4f}\n"
                self.la_result.text = result_str

            else:
                self.la_result.text = "Supported operations: det, inv, solve, eigen"

        except Exception as e:
            self.la_result.text = f"Error: {str(e)}"

    def show_stepwise_solution(self, expression):
        """Show stepwise solution for the given expression."""
        try:
            # If we have calculation steps from a previous evaluation
            if not self.calculation_steps and expression:
                # Try to evaluate the expression to generate steps
                self.evaluate_expression(expression)

            if not self.calculation_steps:
                self.error_label.text = "No steps available. Calculate first."
                return

            # Create a layout for the dialog
            content = MDBoxLayout(orientation='vertical', spacing=10, padding=15, size_hint_y=None, height=400)

            # Title for the solution
            content.add_widget(MDLabel(
                text="Step-by-Step Solution",
                font_style="H5",
                size_hint_y=None,
                height=50
            ))

            # Create a scroll view for steps
            scroll = ScrollView(size_hint=(1, None), height=300)
            steps_box = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
            steps_box.bind(minimum_height=steps_box.setter('height'))

            # Add each step as a label
            for i, step in enumerate(self.calculation_steps):
                step_label = MDLabel(
                    text=f"Step {i + 1}: {step}",
                    size_hint_y=None,
                    height=40
                )
                steps_box.add_widget(step_label)

            scroll.add_widget(steps_box)
            content.add_widget(scroll)

            # Create the dialog
            dialog = MDDialog(
                title="Solution Steps",
                type="custom",
                content_cls=content,
                buttons=[
                    MDRaisedButton(
                        text="CLOSE",
                        on_release=lambda x: dialog.dismiss()
                    )
                ],
                size_hint=(0.9, None),
                height=500
            )
            dialog.open()

        except Exception as e:
            self.error_label.text = f"Error generating steps: {str(e)}"

    def open_binary_converter(self):
        """Open the binary converter dialog with an improved modern design."""
        content = MDBoxLayout(orientation='vertical', padding=20, spacing=15, size_hint_y=None, height=450)

        # Title with improved styling
        title_box = MDBoxLayout(size_hint_y=None, height=60)
        title_label = MDLabel(
            text="Binary Converter",
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=[0.129, 0.588, 0.953, 1],  # White text for better contrast
            halign="center"
        )
        title_box.add_widget(title_label)
        content.add_widget(title_box)

        # Input field with modern styling
        self.number_input = MDTextField(
            hint_text="Enter a number",
            font_size=18,
            size_hint_y=None,
            height="60dp",
            mode="fill",
            hint_text_color_normal=[0.5, 0.5, 0.5, 1],  # Gray hint text
            line_color_normal=[0.25, 0.25, 0.25, 1],  # Dark line color
            line_color_focus=[0.25, 0.25, 0.25, 1]  # Dark line color when focused
        )
        content.add_widget(self.number_input)

        # Conversion type selector
        self.selected_conversion = "Decimal to Binary"

        # Create a more visually appealing dropdown button
        conversion_button = MDRaisedButton(
            text=self.selected_conversion,
            size_hint=(1, None),
            height="50dp",
            md_bg_color=[0.129, 0.588, 0.953, 1],  # Primary color: #2196F3
            text_color=[1, 1, 1, 1],  # White text
            font_size=16,
            elevation=2
        )

        # Define conversion options
        conversion_items = [
            {"text": "Decimal to Binary"},
            {"text": "Decimal to Hexadecimal"},
            {"text": "Binary to Decimal"},
            {"text": "Binary to Hexadecimal"},
            {"text": "Hexadecimal to Decimal"},
            {"text": "Hexadecimal to Binary"},
            {"text": "Decimal to Octal"},
            {"text": "Octal to Decimal"}
        ]

        # Fixed dropdown handling with proper callback
        def show_conversion_menu(button):
            menu_items = [
                {
                    "text": item["text"],
                    "viewclass": "OneLineListItem",
                    "height": dp(56),
                    "on_release": lambda x=item["text"]: set_conversion_type(x)
                } for item in conversion_items
            ]

            self.conversion_menu = MDDropdownMenu(
                caller=conversion_button,
                items=menu_items,
                width_mult=4
            )

            self.conversion_menu.open()

        def set_conversion_type(text):
            self.selected_conversion = text
            conversion_button.text = text
            self.conversion_menu.dismiss()

        # Properly bind button to the show_menu function
        conversion_button.bind(on_release=show_conversion_menu)
        content.add_widget(conversion_button)

        # Spacer
        content.add_widget(MDBoxLayout(size_hint_y=None, height=10))

        # Result display with improved styling
        result_box = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=100,
            padding=[15, 10],
            md_bg_color=[0.97, 0.97, 0.97, 1]  # Crisp Light Gray
        )

        result_title = MDLabel(
            text="Result:",
            theme_text_color="Custom",
            bold=True,
            size_hint_y=None,
            height=30,
            text_color=[0, 0, 0, 1]  # Black text for result title
        )

        self.result_label = MDLabel(
            text="Converted value will appear here",
            theme_text_color="Custom",
            font_size=18,
            bold=True,
            halign="center",
            text_color=[0, 0, 0, 1]  # Black text for result label
        )

        result_box.add_widget(result_title)
        result_box.add_widget(self.result_label)
        content.add_widget(result_box)

        # Convert button with accent color
        convert_button = MDRaisedButton(
            text="CONVERT",
            size_hint=(1, None),
            height="50dp",
            elevation=3,
            md_bg_color=[0.129, 0.588, 0.953, 1],  # Primary color: #2196F3
            text_color=[1, 1, 1, 1],  # White text
            font_size=16,
            on_release=self.convert_number
        )
        content.add_widget(convert_button)

        # Create the dialog with improved styling
        self.dialog = MDDialog(
            title="Number Converter",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="CLOSE",
                    md_bg_color=[1, 1, 1, 1],  # White background
                    text_color=[0.129, 0.588, 0.953, 1],  # Text color: #2196F3
                    on_release=lambda x: self.dialog.dismiss()
                )
            ],
            size_hint=(0.9, None),
            height=600,
            radius=[20, 7, 20, 7]
        )
        self.dialog.open()

    def convert_number(self, instance):
        """Convert the input number based on the selected conversion type with error handling."""
        try:
            input_value = self.number_input.text.strip()
            if not input_value:
                self.result_label.text = "Please enter a number"
                return

            # Dictionary to store conversion functions
            conversion_functions = {
                "Decimal to Binary": self.decimal_to_binary,
                "Decimal to Hexadecimal": self.decimal_to_hexadecimal,
                "Binary to Decimal": self.binary_to_decimal,
                "Binary to Hexadecimal": self.binary_to_hexadecimal,
                "Hexadecimal to Decimal": self.hexadecimal_to_decimal,
                "Hexadecimal to Binary": self.hexadecimal_to_binary,
                "Decimal to Octal": self.decimal_to_octal,
                "Octal to Decimal": self.octal_to_decimal
            }
            
            # Check if selected conversion is valid
            if self.selected_conversion in conversion_functions:
                result = conversion_functions[self.selected_conversion](input_value)
                # Format the result with the appropriate prefix
                if self.selected_conversion.endswith("Binary"):
                    self.result_label.text = f"Binary: 0b{result}"
                elif self.selected_conversion.endswith("Hexadecimal"):
                    self.result_label.text = f"Hexadecimal: 0x{result}"
                elif self.selected_conversion.endswith("Octal"):
                    self.result_label.text = f"Octal: 0o{result}"
                else:
                    self.result_label.text = f"Decimal: {result}"
            else:
                self.result_label.text = "Invalid conversion type"

        except ValueError as e:
            self.result_label.text = f"Invalid input: {str(e)}"
        except Exception as e:
            self.result_label.text = f"Error: {str(e)}"

    # Conversion functions
    def decimal_to_binary(self, value):
        """Convert decimal to binary."""
        return bin(int(value))[2:]  # Remove '0b' prefix
        
    def decimal_to_hexadecimal(self, value):
        """Convert decimal to hexadecimal."""
        return hex(int(value))[2:].upper()  # Remove '0x' prefix and convert to uppercase
        
    def binary_to_decimal(self, value):
        """Convert binary to decimal."""
        # Validate binary input
        if not all(bit in '01' for bit in value):
            raise ValueError("Binary values must consist of only 0s and 1s")
        return str(int(value, 2))
        
    def binary_to_hexadecimal(self, value):
        """Convert binary to hexadecimal."""
        # Validate binary input
        if not all(bit in '01' for bit in value):
            raise ValueError("Binary values must consist of only 0s and 1s")
        decimal = int(value, 2)
        return hex(decimal)[2:].upper()
        
    def hexadecimal_to_decimal(self, value):
        """Convert hexadecimal to decimal."""
        # Validate hex input
        valid_hex_chars = set("0123456789ABCDEFabcdef")
        if not all(c in valid_hex_chars for c in value):
            raise ValueError("Hexadecimal values must consist of 0-9 and A-F")
        return str(int(value, 16))
        
    def hexadecimal_to_binary(self, value):
        """Convert hexadecimal to binary."""
        # Validate hex input
        valid_hex_chars = set("0123456789ABCDEFabcdef")
        if not all(c in valid_hex_chars for c in value):
            raise ValueError("Hexadecimal values must consist of 0-9 and A-F")
        decimal = int(value, 16)
        return bin(decimal)[2:]
        
    def decimal_to_octal(self, value):
        """Convert decimal to octal."""
        return oct(int(value))[2:]  # Remove '0o' prefix
        
    def octal_to_decimal(self, value):
        """Convert octal to decimal."""
        # Validate octal input
        if not all(digit in '01234567' for digit in value):
            raise ValueError("Octal values must consist of digits 0-7")
        return str(int(value, 8))


# Add a new class for the Mathematical Expression Solver
class MathExpressionSolver(MDScreen):
    def __init__(self, app=None, **kwargs):
        self.app = app
        kwargs.pop("app", None)
        super().__init__(**kwargs)

        # Main layout
        self.layout = MDBoxLayout(orientation="vertical", padding=10, spacing=10)

        # Top bar
        self.top_bar = MDTopAppBar(
            title="Math Expression Solver",
            elevation=2,
            pos_hint={"top": 1}
        )

        # Expression input
        self.expression_input = MDTextField(
            hint_text="Enter mathematical expression",
            font_size=18,
            multiline=True,
            size_hint=(1, None),
            height="100dp"
        )

        # Solve button
        solve_button = MDRaisedButton(
            text="Solve Expression",
            font_size=16,
            size_hint=(1, None),
            height="50dp",
            on_release=self.solve_expression
        )

        # Results display
        self.result_scroll = ScrollView(size_hint=(1, 1))
        self.result_label = MDLabel(
            text="Results will appear here",
            font_size=16,
            halign="left",
            valign="top",
            size_hint_y=None
        )
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        self.result_scroll.add_widget(self.result_label)

        # Add widgets to layout
        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.expression_input)
        self.layout.add_widget(solve_button)
        self.layout.add_widget(self.result_scroll)

        self.add_widget(self.layout)

    def solve_expression(self, instance):
        """Parse and solve the mathematical expression."""
        expr_text = self.expression_input.text.strip()

        if not expr_text:
            self.result_label.text = "Please enter an expression"
            return

        try:
            # Convert common symbols to Python syntax
            expr_text = expr_text.replace("^", "**")
            expr_text = expr_text.replace("√", "math.sqrt")
            expr_text = expr_text.replace("π", "math.pi")

            # Replace functions with math module equivalents
            expr_text = re.sub(r'sin\(', 'math.sin(', expr_text)
            expr_text = re.sub(r'cos\(', 'math.cos(', expr_text)
            expr_text = re.sub(r'tan\(', 'math.tan(', expr_text)
            expr_text = re.sub(r'log\(', 'math.log10(', expr_text)
            expr_text = re.sub(r'ln\(', 'math.log(', expr_text)

            # Format display steps
            steps = ["Original expression: " + self.expression_input.text]
            steps.append("Converted to Python: " + expr_text)

            # Evaluate the expression
            result = eval(expr_text)
            steps.append(f"Final result: {result}")

            # Display results
            self.result_label.text = "\n".join(steps)

        except Exception as e:
            self.result_label.text = f"Error: {str(e)}\n\nPlease check your expression format."