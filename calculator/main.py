import tkinter as tk
from functools import partial
import re

# Use a relative import since main.py and safe_eval.py are in the same package.
from .safe_eval import safe_eval

class CalculatorApp(tk.Tk):
    """
    The main application class for the calculator, inheriting from tk.Tk.
    It sets up the main window and its components.
    """
    def __init__(self):
        super().__init__()
        self.title("Accessible Calculator")
        self.geometry("400x600")

        # Configure the color scheme for accessibility (dark theme).
        self.configure(bg="#2E2E2E")
        self.style = {
            "bg": "#2E2E2E",
            "fg": "#FFFFFF",
            "btn_bg": "#4F4F4F",
            "btn_fg": "#FFFFFF",
            "display_bg": "#3C3C3C",
            "display_fg": "#FFFFFF",
            "font_large": ("Arial", 24, "bold"),
            "font_medium": ("Arial", 16)
        }

        # Configure the main window grid (1 column, 2 rows: display and buttons).
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)  # Row for the display
        self.grid_rowconfigure(1, weight=4)  # Row for the buttons frame

        self.display_var = tk.StringVar()
        # A flag to track if a calculation was just performed.
        # If so, the next digit press should clear the display.
        self.just_calculated = False
        self._create_display()
        self._create_buttons_frame()

        # Bind keypress events to the handler.
        self.bind("<Key>", self._handle_keypress)

    def _create_display(self):
        """Creates the display widget."""
        display = tk.Entry(self, textvariable=self.display_var,
                           font=("Arial", 48, "bold"),
                           bg=self.style["display_bg"],
                           fg=self.style["display_fg"],
                           justify='right',
                           bd=0,
                           state='readonly',
                           readonlybackground=self.style["display_bg"])
        display.grid(row=0, column=0, sticky="nsew", padx=10, pady=20)
        self.display_var.set("0")

    def _create_buttons_frame(self):
        """Creates the frame for the calculator buttons."""
        buttons_frame = tk.Frame(self, bg=self.style["bg"])
        buttons_frame.grid(row=1, column=0, sticky="nsew")

        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1)
        for i in range(5):
            buttons_frame.grid_rowconfigure(i, weight=1)

        button_layout = [
            ('C', 0, 0), ('+/-', 0, 1), ('%', 0, 2), ('÷', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('×', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 2), ('.', 4, 2), ('=', 4, 3),
        ]

        for (text, row, col, *span) in button_layout:
            colspan = span[0] if span else 1
            self._create_button(buttons_frame, text, row, col, colspan)

    def _create_button(self, parent, text, row, col, colspan=1):
        """Creates a single button."""
        btn = tk.Button(parent, text=text,
                        font=self.style["font_large"],
                        bg=self.style["btn_bg"],
                        fg=self.style["btn_fg"],
                        bd=0,
                        relief=tk.FLAT,
                        activebackground="#6A6A6A",
                        activeforeground="#FFFFFF")
        btn.config(command=partial(self._on_button_press, text))
        btn.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=5, pady=5)
        return btn

    def _on_button_press(self, char):
        """General handler for all button presses."""
        if char.isdigit() or char == '.':
            self._append_to_display(char)
        elif char in ('+', '-', '×', '÷'):
            self._append_to_display(f' {char} ')
        elif char == 'C':
            self._clear()
        elif char == '=':
            self._calculate()
        elif char == '+/-':
            self._toggle_sign()
        elif char == '%':
            self._handle_percentage()

    def _append_to_display(self, text):
        """Appends a character or text to the display."""
        current_text = self.display_var.get()
        if self.just_calculated and text.strip().isdigit():
            current_text = "0"

        self.just_calculated = False

        if current_text == "0" and text.strip().isdigit():
            self.display_var.set(text)
        else:
            self.display_var.set(current_text + text)

    def _clear(self):
        """Clears the display."""
        self.display_var.set("0")
        self.just_calculated = False

    def _calculate(self):
        """Calculates the expression on the display."""
        expression = self.display_var.get()
        expression = expression.replace('×', '*').replace('÷', '/')

        result = safe_eval(expression)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        self.display_var.set(str(result))
        self.just_calculated = True

    def _toggle_sign(self):
        """Toggles the sign of the last number in the expression."""
        current_text = self.display_var.get()

        if self.just_calculated:
            if current_text.startswith('-'):
                self.display_var.set(current_text[1:])
            else:
                self.display_var.set('-' + current_text)
            return

        parts = re.split(r'(\s[-+×÷]\s)', current_text)
        if len(parts) > 0:
            last_part = parts[-1]
            try:
                num = float(last_part)
                if num == 0: return # Don't toggle sign for zero

                if last_part.startswith('-'):
                    parts[-1] = last_part[1:]
                else:
                    parts[-1] = '-' + last_part

                self.display_var.set("".join(parts))
            except ValueError:
                # The last part is not a number (e.g., an operator)
                pass

    def _handle_percentage(self):
        """Converts the last number to its percentage value (divides by 100)."""
        current_text = self.display_var.get()
        parts = re.split(r'(\s[-+×÷]\s)', current_text)
        if len(parts) > 0:
            last_part = parts[-1]
            try:
                num = float(last_part)
                result = num / 100
                if result.is_integer():
                    result = int(result)
                parts[-1] = str(result)
                self.display_var.set("".join(parts))
                # Unlike calculation, this doesn't finalize the expression
                self.just_calculated = False
            except ValueError:
                pass

    def _handle_keypress(self, event):
        """Handles keyboard press events."""
        char = event.char
        keysym = event.keysym

        if char.isdigit() or char == '.':
            self._on_button_press(char)
        elif char in ('+', '-'):
            self._on_button_press(char)
        elif char == '*':
            self._on_button_press('×')
        elif char == '/':
            self._on_button_press('÷')
        elif char == '%':
            self._on_button_press('%')
        elif keysym == "Return" or char == '=':
            self._on_button_press('=')
        elif keysym == "BackSpace":
            self._backspace()
        elif keysym == "Escape" or char.lower() == 'c':
            self._on_button_press('C')

    def _backspace(self):
        """Deletes the last character from the display."""
        current_text = self.display_var.get()
        if len(current_text) > 1:
            if current_text.endswith(' '):
                self.display_var.set(current_text[:-3])
            else:
                self.display_var.set(current_text[:-1])
        else:
            self.display_var.set("0")
        self.just_calculated = False


if __name__ == '__main__':
    app = CalculatorApp()
    app.mainloop()
