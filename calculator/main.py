import tkinter as tk
from tkinter import font as tkfont
import re
from .safe_eval import safe_eval

class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Супер Доступный Калькулятор")
        self.geometry("400x600")
        self.resizable(False, False)
        self.configure(bg="#2E2E2E")

        self.expression = ""
        self.just_calculated = False

        # --- Styles ---
        self.display_font = tkfont.Font(family="Arial", size=48, weight="bold")
        self.button_font = tkfont.Font(family="Arial", size=20)
        self.colors = {
            "bg": "#2E2E2E",
            "display_bg": "#1F1F1F",
            "fg": "#FFFFFF",
            "button_bg": "#4F4F4F",
            "operator_bg": "#FF9500",
            "special_bg": "#D4D4D2",
            "special_fg": "#1C1C1C",
        }

        # --- Grid Configuration ---
        self.grid_rowconfigure(0, weight=2) # Display row
        for i in range(1, 6):
             self.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

        # --- Display ---
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            self,
            textvariable=self.display_var,
            font=self.display_font,
            bg=self.colors["display_bg"],
            fg=self.colors["fg"],
            justify="right",
            bd=0,
            state="readonly",
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=20)

        # --- Buttons ---
        buttons = [
            ("C", 1, 0, self.colors['special_bg'], self.colors['special_fg']),
            ("+/-", 1, 1, self.colors['special_bg'], self.colors['special_fg']),
            ("%", 1, 2, self.colors['special_bg'], self.colors['special_fg']),
            ("÷", 1, 3, self.colors['operator_bg'], self.colors['fg']),
            ("7", 2, 0, self.colors['button_bg'], self.colors['fg']),
            ("8", 2, 1, self.colors['button_bg'], self.colors['fg']),
            ("9", 2, 2, self.colors['button_bg'], self.colors['fg']),
            ("×", 2, 3, self.colors['operator_bg'], self.colors['fg']),
            ("4", 3, 0, self.colors['button_bg'], self.colors['fg']),
            ("5", 3, 1, self.colors['button_bg'], self.colors['fg']),
            ("6", 3, 2, self.colors['button_bg'], self.colors['fg']),
            ("-", 3, 3, self.colors['operator_bg'], self.colors['fg']),
            ("1", 4, 0, self.colors['button_bg'], self.colors['fg']),
            ("2", 4, 1, self.colors['button_bg'], self.colors['fg']),
            ("3", 4, 2, self.colors['button_bg'], self.colors['fg']),
            ("+", 4, 3, self.colors['operator_bg'], self.colors['fg']),
            ("0", 5, 0, self.colors['button_bg'], self.colors['fg'], 2),
            (".", 5, 2, self.colors['button_bg'], self.colors['fg']),
            ("=", 5, 3, self.colors['operator_bg'], self.colors['fg']),
        ]

        for button_data in buttons:
            text, row, col, bg_color, fg_color = button_data[:5]
            columnspan = button_data[5] if len(button_data) > 5 else 1
            self.create_button(text, row, col, bg_color, fg_color, columnspan)

        # --- Keyboard Bindings ---
        self.bind("<Key>", self._handle_keypress)
        self._update_display("0")

    def create_button(self, text, row, col, bg_color, fg_color, columnspan=1):
        button = tk.Button(
            self,
            text=text,
            font=self.button_font,
            bg=bg_color,
            fg=fg_color,
            bd=0,
            relief=tk.FLAT,
            command=lambda t=text: self._on_button_press(t),
        )
        button.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=5, pady=5)
        return button

    def _handle_keypress(self, event):
        char = event.char
        keysym = event.keysym

        if keysym in ("Return", "KP_Enter"):
            self._on_button_press("=")
        elif keysym == "Escape":
            self._on_button_press("C")
        elif keysym == "BackSpace":
            self._backspace()
        elif char in "0123456789.":
            self._on_button_press(char)
        elif char in "+-*/":
            op_map = {"*": "×", "/": "÷"}
            self._on_button_press(op_map.get(char, char))

    def _on_button_press(self, char):
        if char.isdigit():
            if self.just_calculated or self.expression == "0":
                self.expression = ""
            self.expression += char
            self.just_calculated = False
        elif char == ".":
            # Prevent multiple dots in the last number
            last_number = re.split(r"[\+\-×÷]", self.expression)[-1]
            if "." not in last_number:
                self.expression += char
                self.just_calculated = False
        elif char in "+-×÷":
            if self.expression and self.expression[-1] in "+-×÷":
                # Replace the last operator
                self.expression = self.expression[:-1] + char
            else:
                self.expression += char
            self.just_calculated = False
        elif char == "C":
            self.expression = "0"
        elif char == "=":
            if not self.expression:
                return
            result = safe_eval(self.expression)
            self.expression = str(result)
            self.just_calculated = True
        elif char == "+/-":
            self._toggle_sign()
        elif char == "%":
            self._calculate_percentage()

        self._update_display()

    def _update_display(self, value=None):
        display_value = value if value is not None else self.expression
        if not display_value:
           display_value = "0"
        self.display_var.set(display_value)

    def _backspace(self):
        if self.just_calculated:
            return
        self.expression = self.expression[:-1]
        self._update_display()

    def _toggle_sign(self):
        if self.just_calculated or not self.expression or self.expression == "0":
            return

        parts = re.split(r'(\+|\-|×|÷)', self.expression)
        if parts[-1]:
            try:
                num = float(parts[-1]) * -1
                # Avoid ".0" for whole numbers
                if num.is_integer():
                    parts[-1] = str(int(num))
                else:
                    parts[-1] = str(num)
                self.expression = "".join(parts)
            except ValueError:
                # This can happen if the last part isn't a valid number. Do nothing.
                pass

    def _calculate_percentage(self):
        if self.just_calculated or not self.expression or self.expression == "0":
            return

        parts = re.split(r'(\+|\-|×|÷)', self.expression)
        if parts[-1]:
            try:
                num = float(parts[-1]) / 100
                parts[-1] = str(num)
                self.expression = "".join(parts)
            except ValueError:
                # This can happen if the last part isn't a valid number. Do nothing.
                pass

if __name__ == "__main__":
    # To run this from the root directory, use: python3 -m calculator.main
    app = CalculatorApp()
    app.mainloop()
