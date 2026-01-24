from .safe_eval import safe_eval
import tkinter as tk

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Доступный калькулятор")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#2E2E2E")

        self.just_calculated = False
        self.create_widgets()
        self.root.bind("<Key>", self.handle_keypress)
        self.display.focus_set()

    def create_widgets(self):
        # Frame for the display
        display_frame = tk.Frame(self.root, bg="#2E2E2E")
        display_frame.pack(expand=True, fill="both")

        # Display Entry widget
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            display_frame,
            textvariable=self.display_var,
            font=("Arial", 48, "bold"),
            bg="#3B3B3B",
            fg="#FFFFFF",
            bd=0,
            justify="right",
            insertbackground="#FFFFFF"  # cursor color
        )
        self.display.pack(expand=True, fill="both", padx=10, pady=10)

        # Frame for the buttons
        buttons_frame = tk.Frame(self.root, bg="#2E2E2E")
        buttons_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # Configure grid layout for buttons_frame
        for i in range(5):  # 5 rows
            buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):  # 4 columns
            buttons_frame.grid_columnconfigure(i, weight=1)

        buttons = [
            ('C', 0, 0), ('←', 0, 1), ('^', 0, 2), ('÷', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('×', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 2), ('.', 4, 2), ('=', 4, 3)
        ]

        for (text, row, col, *span) in buttons:
            colspan = span[0] if span else 1
            button = tk.Button(
                buttons_frame,
                text=text,
                font=("Arial", 24, "bold"),
                bg="#505050",
                fg="#FFFFFF",
                bd=0,
                activebackground="#6A6A6A",
                activeforeground="#FFFFFF",
                command=lambda t=text: self.on_button_click(t)
            )
            button.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=2, pady=2)

    def on_button_click(self, char):
        current_text = self.display_var.get()

        if char == 'C':
            self.display_var.set("")
            return

        if char == '←':
            if self.just_calculated:
                self.display_var.set("")
                self.just_calculated = False
            else:
                self.display_var.set(current_text[:-1])
            return

        if char == '=':
            self.calculate()
            return

        # If a calculation was just performed, and the user types a number, start a new calculation.
        if self.just_calculated and char.isdigit():
            self.display_var.set(char)
            self.just_calculated = False
        # Otherwise, if it was an operator, continue with the result.
        elif self.just_calculated and char in "+-×÷^":
             self.just_calculated = False
             self.display_var.set(current_text + char)
        else:
            self.display_var.set(current_text + char)
            self.just_calculated = False


    def calculate(self):
        expression = self.display_var.get()
        # Replace visual operators with Python operators
        expression = expression.replace('×', '*').replace('÷', '/').replace('^', '**')

        result = safe_eval(expression)

        # Format result to avoid ".0" for whole numbers
        if isinstance(result, float) and result.is_integer():
            result = int(result)

        self.display_var.set(str(result))
        self.just_calculated = True

    def handle_keypress(self, event):
        char = event.char
        keysym = event.keysym

        if keysym == "Return" or keysym == "equal":
            self.on_button_click('=')
        elif keysym == "BackSpace":
            self.on_button_click('←')
        elif keysym == "Escape":
            self.on_button_click('C')
        elif char in "0123456789.+-*/^":
            if char == '*':
                self.on_button_click('×')
            elif char == '/':
                self.on_button_click('÷')
            else:
                self.on_button_click(char)
        # Allow navigating and selecting text
        elif keysym in ("Left", "Right", "Home", "End", "Shift_L", "Shift_R"):
            pass


if __name__ == "__main__":
    # To run this as a standalone script for development
    try:
        from safe_eval import safe_eval
    except ImportError:
        # This allows running the script directly during development
        # without package resolution issues.
        pass

    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
