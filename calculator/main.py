import tkinter as tk
from tkinter import messagebox
import sys
import os
import math

# Add the current directory to sys.path to allow imports when run as a script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from safe_eval import safe_eval
except ImportError:
    from .safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Super Accessible Calculator")
        self.root.geometry("500x850")
        self.root.configure(bg="#121212")

        self.expression = ""
        self.just_calculated = False

        self._setup_ui()
        self._setup_keyboard()

    def _setup_ui(self):
        # Display area
        self.display_frame = tk.Frame(self.root, bg="#121212", padx=10, pady=10)
        self.display_frame.pack(fill="x")

        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            self.display_frame,
            textvariable=self.display_var,
            font=("Arial", 36, "bold"),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="white",
            justify="right",
            readonlybackground="#1e1e1e",
            state="readonly",
            relief="flat",
            highlightthickness=2,
            highlightcolor="#bb86fc"
        )
        self.display.pack(fill="x", ipady=20)

        # Buttons area
        self.buttons_frame = tk.Frame(self.root, bg="#121212", padx=10, pady=10)
        self.buttons_frame.pack(expand=True, fill="both")

        buttons = [
            ('sin(', 'cos(', 'tan(', 'sqrt('),
            ('log(', 'ln(', 'exp(', '^'),
            ('pi', 'e', '(', ')'),
            ('AC', 'C', '%', '÷'),
            ('7', '8', '9', '×'),
            ('4', '5', '6', '-'),
            ('1', '2', '3', '+'),
            ('+/-', '0', '.', '=')
        ]

        for r, row in enumerate(buttons):
            self.buttons_frame.grid_rowconfigure(r, weight=1)
            for c, text in enumerate(row):
                self.buttons_frame.grid_columnconfigure(c, weight=1)
                self._create_button(text, r, c)

    def _create_button(self, text, row, col):
        bg_color = "#333333"
        fg_color = "#ffffff"

        if text in ('=',):
            bg_color = "#4caf50"
        elif text in ('+', '-', '×', '÷', '^'):
            bg_color = "#ff9800"
        elif text in ('AC', 'C'):
            bg_color = "#f44336"
        elif text in ('sin(', 'cos(', 'tan(', 'sqrt(', 'log(', 'ln(', 'exp(', 'pi', 'e', '(', ')', '%', '+/-'):
            bg_color = "#424242"

        button = tk.Button(
            self.buttons_frame,
            text=text,
            font=("Arial", 18, "bold"),
            bg=bg_color,
            fg=fg_color,
            activebackground="#555555",
            activeforeground="#ffffff",
            relief="flat",
            highlightthickness=0,
            command=lambda t=text: self._on_button_click(t)
        )
        # For macOS compatibility with background colors in tkinter,
        # sometimes we need to use highlightbackground or other tricks,
        # but in this environment it should work with standard bg if it's linux-based.
        # Actually the environment is Linux, but the request is for macOS.
        # I'll stick to standard tkinter which should work.

        button.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

    def _on_button_click(self, char):
        if char == "AC":
            self.expression = ""
            self.just_calculated = False
        elif char == "C":
            self.expression = self.expression[:-1]
        elif char == "=":
            self._calculate()
            return
        elif char == "+/-":
            self._toggle_sign()
            return
        elif char == "%":
            self._apply_percent()
            return
        else:
            if self.just_calculated and char.isdigit():
                self.expression = char
            else:
                self.expression += char
            self.just_calculated = False

        self._update_display(self.expression)

    def _calculate(self):
        if not self.expression:
            return

        result = safe_eval(self.expression)
        self._update_display(str(result))
        self.expression = str(result) if result != "Error" else ""
        self.just_calculated = True

    def _toggle_sign(self):
        if not self.expression:
            return

        import re
        # Regex to find the last number or a parenthesized negative number
        pattern = r'(\(-?\d+\.?\d*\)|-?\d+\.?\d*)$'
        match = re.search(pattern, self.expression)

        if match:
            last_part = match.group(1)
            start = match.start()

            if last_part.startswith("(-") and last_part.endswith(")"):
                # Remove parentheses and minus: (-5) -> 5
                new_part = last_part[2:-1]
            elif last_part.startswith("-"):
                # Remove minus: -5 -> 5
                new_part = last_part[1:]
            else:
                # Add minus and parentheses: 5 -> (-5)
                new_part = f"(-{last_part})"

            self.expression = self.expression[:start] + new_part
        self._update_display(self.expression)

    def _apply_percent(self):
        if not self.expression:
            return

        import re
        pattern = r'(\d+\.?\d*)$'
        match = re.search(pattern, self.expression)

        if match:
            num = match.group(1)
            start = match.start()
            try:
                # Replace last number with its value divided by 100
                val = float(num) / 100
                # Format to avoid long scientific notation if possible
                new_val = f"{val:g}"
                self.expression = self.expression[:start] + new_val
            except:
                self.expression += "/100"
        else:
            self.expression += "/100"

        self._update_display(self.expression)

    def _update_display(self, text):
        self.display.config(state="normal")
        self.display_var.set(text)
        self.display.config(state="readonly")

    def _setup_keyboard(self):
        self.root.bind("<Key>", self._handle_keypress)

    def _handle_keypress(self, event):
        key = event.char
        keysym = event.keysym

        if key in "0123456789":
            self._on_button_click(key)
        elif key in "+-/.()%^":
            if key == "/":
                self._on_button_click("÷")
            else:
                self._on_button_click(key)
        elif key == "*":
            self._on_button_click("×")
        elif keysym == "Return":
            self._on_button_click("=")
        elif keysym == "BackSpace":
            self._on_button_click("C")
        elif keysym == "Escape":
            self._on_button_click("AC")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    app.run()
