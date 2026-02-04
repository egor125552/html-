import tkinter as tk
from tkinter import font
import math
import re

try:
    from .safe_eval import safe_eval
except ImportError:
    from safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessible Scientific Calculator")
        self.root.geometry("400x700")
        self.root.configure(bg="#1e1e1e")

        self.expression = ""
        self.just_calculated = False

        # Fonts
        self.display_font = font.Font(family="Helvetica", size=32, weight="bold")
        self.button_font = font.Font(family="Helvetica", size=18, weight="bold")

        # Display
        self.display = tk.Entry(
            root,
            font=self.display_font,
            bg="#2d2d2d",
            fg="white",
            borderwidth=0,
            justify="right",
            highlightthickness=2,
            highlightcolor="#007aff",
            readonlybackground="#2d2d2d"
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=20)
        self.display.config(state="readonly")

        self._create_buttons()
        self._setup_bindings()

    def _create_buttons(self):
        buttons = [
            ('C', 1, 0, '#ff3b30'), ('(', 1, 1, '#4a4a4a'), (')', 1, 2, '#4a4a4a'), ('÷', 1, 3, '#ff9500'),
            ('sin', 2, 0, '#4a4a4a'), ('cos', 2, 1, '#4a4a4a'), ('tan', 2, 2, '#4a4a4a'), ('×', 2, 3, '#ff9500'),
            ('ln', 3, 0, '#4a4a4a'), ('log', 3, 1, '#4a4a4a'), ('√', 3, 2, '#4a4a4a'), ('-', 3, 3, '#ff9500'),
            ('7', 4, 0, '#333333'), ('8', 4, 1, '#333333'), ('9', 4, 2, '#333333'), ('+', 4, 3, '#ff9500'),
            ('4', 5, 0, '#333333'), ('5', 5, 1, '#333333'), ('6', 5, 2, '#333333'), ('xʸ', 5, 3, '#ff9500'),
            ('1', 6, 0, '#333333'), ('2', 6, 1, '#333333'), ('3', 6, 2, '#333333'), ('!', 6, 3, '#ff9500'),
            ('±', 7, 0, '#333333'), ('0', 7, 1, '#333333'), ('.', 7, 2, '#333333'), ('=', 7, 3, '#007aff'),
            ('π', 8, 0, '#4a4a4a'), ('e', 8, 1, '#4a4a4a'), ('%', 8, 2, '#4a4a4a'), ('exp', 8, 3, '#4a4a4a'),
            ('abs', 9, 0, '#4a4a4a'),
        ]

        for (text, row, col, color) in buttons:
            btn = tk.Button(
                self.root,
                text=text,
                font=self.button_font,
                bg=color,
                fg="white",
                highlightbackground=color,
                command=lambda t=text: self._on_button_click(t),
                width=5,
                height=2,
                relief="flat",
                activebackground="#555555"
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

        for i in range(10):
            self.root.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.root.grid_columnconfigure(i, weight=1)

    def _on_button_click(self, char):
        if char == 'C':
            self.expression = ""
            self.just_calculated = False
        elif char == '=':
            self._calculate()
            return
        elif char == '±':
            self._toggle_sign()
        elif char == '%':
            self._apply_percent()
        elif char == 'xʸ':
            self.expression += "**"
        elif char == '×':
            self.expression += "*"
        elif char == '÷':
            self.expression += "/"
        elif char == '√':
            self.expression += "sqrt("
        elif char == 'π':
            self.expression += "pi"
        elif char == '!':
            self._apply_factorial()
        elif char in ['sin', 'cos', 'tan', 'ln', 'log', 'exp', 'abs']:
            self.expression += f"{char}("
        else:
            if self.just_calculated and char.isdigit():
                self.expression = char
                self.just_calculated = False
            else:
                self.expression += str(char)
                self.just_calculated = False

        self._update_display()

    def _calculate(self):
        # Basic balancing of parentheses for ease of use
        open_count = self.expression.count('(')
        close_count = self.expression.count(')')
        if open_count > close_count:
            self.expression += ')' * (open_count - close_count)

        result = safe_eval(self.expression)

        # Format result to be pretty
        if isinstance(result, float):
            if result.is_integer():
                result = int(result)
            else:
                result = round(result, 10)

        self.expression = str(result)
        self.just_calculated = True
        self._update_display()

    def _toggle_sign(self):
        # Toggle sign of the last number in the expression
        pattern = r'(\(-?\d+\.?\d*\)|-?\d+\.?\d*)$'
        match = re.search(pattern, self.expression)
        if match:
            last_num = match.group(0)
            start, end = match.span()
            if last_num.startswith('(-') and last_num.endswith(')'):
                new_num = last_num[2:-1]
            elif last_num.startswith('-'):
                new_num = last_num[1:]
            else:
                new_num = f"(-{last_num})"
            self.expression = self.expression[:start] + new_num

    def _apply_percent(self):
        pattern = r'(\d+\.?\d*)$'
        match = re.search(pattern, self.expression)
        if match:
            num = match.group(0)
            start, end = match.span()
            new_num = str(float(num) / 100)
            self.expression = self.expression[:start] + new_num

    def _apply_factorial(self):
        # Try to find the last number or parenthesized expression
        if self.expression.endswith(')'):
            # Find matching opening parenthesis
            count = 0
            for i in range(len(self.expression) - 1, -1, -1):
                if self.expression[i] == ')':
                    count += 1
                elif self.expression[i] == '(':
                    count -= 1
                if count == 0:
                    self.expression = self.expression[:i] + "factorial(" + self.expression[i:] + ")"
                    break
        else:
            pattern = r'(\d+\.?\d*)$'
            match = re.search(pattern, self.expression)
            if match:
                num = match.group(0)
                start, end = match.span()
                self.expression = self.expression[:start] + f"factorial({num})"

    def _update_display(self):
        # Replace internal python symbols with pretty ones for display
        display_text = self.expression.replace("**", "^").replace("*", "×").replace("/", "÷")

        self.display.config(state="normal")
        self.display.delete(0, tk.END)
        self.display.insert(0, display_text)
        self.display.config(state="readonly")

    def _handle_keypress(self, event):
        char = event.char
        keysym = event.keysym

        if keysym == "Return":
            self._calculate()
        elif keysym == "BackSpace":
            self._backspace()
        elif keysym == "Escape":
            self._on_button_click('C')
        elif char in "0123456789.+-*/()":
            if char == "*":
                self._on_button_click('×')
            elif char == "/":
                self._on_button_click('÷')
            else:
                self._on_button_click(char)
        elif char == "^":
            self._on_button_click('xʸ')
        elif char.lower() == "a":
            self._on_button_click('abs')

    def _backspace(self):
        if self.expression:
            # Handle multi-char functions or constants
            if self.expression.endswith("sqrt("):
                self.expression = self.expression[:-5]
            elif self.expression.endswith(("sin(", "cos(", "tan(", "log(", "exp(", "abs(")):
                self.expression = self.expression[:-4]
            elif self.expression.endswith("factorial("):
                self.expression = self.expression[:-10]
            elif self.expression.endswith("ln("):
                self.expression = self.expression[:-3]
            elif self.expression.endswith("pi"):
                self.expression = self.expression[:-2]
            else:
                self.expression = self.expression[:-1]
            self._update_display()

    def _setup_bindings(self):
        self.root.bind("<Key>", self._handle_keypress)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
