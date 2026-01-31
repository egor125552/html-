import tkinter as tk
from tkinter import font
import re
import math

try:
    from .safe_eval import safe_eval
except (ImportError, ValueError):
    try:
        from safe_eval import safe_eval
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessible Calculator")
        self.root.configure(bg="#2d2d2d")

        self.just_calculated = False

        # Fonts for accessibility
        self.display_font = font.Font(size=30, weight='bold')
        self.button_font = font.Font(size=18, weight='bold')

        # Display
        self.display = tk.Entry(
            root,
            font=self.display_font,
            bg="#2d2d2d",
            fg="#ffffff",
            borderwidth=0,
            justify='right',
            insertbackground='#ffffff',
            readonlybackground="#2d2d2d"
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=20)
        self.display.config(state='readonly')

        # Buttons layout (7 rows of buttons)
        # Improved layout for standard feel
        buttons = [
            ('C', 1, 0), ('(', 1, 1), (')', 1, 2), ('÷', 1, 3),
            ('sin', 2, 0), ('cos', 2, 1), ('tan', 2, 2), ('×', 2, 3),
            ('sqrt', 3, 0), ('log', 3, 1), ('exp', 3, 2), ('-', 3, 3),
            ('7', 4, 0), ('8', 4, 1), ('9', 4, 2), ('+', 4, 3),
            ('4', 5, 0), ('5', 5, 1), ('6', 5, 2), ('%', 5, 3),
            ('1', 6, 0), ('2', 6, 1), ('3', 6, 2), ('+/-', 6, 3),
            ('0', 7, 0), ('.', 7, 1), ('pi', 7, 2), ('=', 7, 3),
        ]

        for (text, row, col) in buttons:
            action = lambda x=text: self._on_button_click(x)
            # Focus visibility: highlightthickness set to 2
            btn = tk.Button(
                root, text=text, font=self.button_font, command=action,
                bg="#404040", fg="#ffffff", activebackground="#505050", activeforeground="#ffffff",
                highlightbackground="#2d2d2d", highlightthickness=2,
                borderwidth=1, relief='flat'
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

        # Configure grid weights for resizing
        for i in range(4):
            root.columnconfigure(i, weight=1)
        for i in range(8):
            root.rowconfigure(i, weight=1)

        # Keyboard bindings
        root.bind("<Key>", self._handle_keypress)

    def _update_display(self, text):
        self.display.config(state='normal')
        self.display.delete(0, tk.END)
        self.display.insert(0, text)
        self.display.config(state='readonly')

    def _on_button_click(self, char):
        current = self.display.get()

        if char == 'C':
            self._update_display("")
            self.just_calculated = False
        elif char == '=':
            result = safe_eval(current)
            self._update_display(result)
            self.just_calculated = True
        elif char == '+/-':
            self._toggle_sign()
        elif char == '%':
            self._apply_percent()
        elif char in ('sin', 'cos', 'tan', 'sqrt', 'log', 'exp'):
            if self.just_calculated:
                self._update_display(char + "(")
                self.just_calculated = False
            else:
                self._update_display(current + char + "(")
        elif char in ('pi', 'e'):
            if self.just_calculated:
                self._update_display(char)
                self.just_calculated = False
            else:
                self._update_display(current + char)
        else:
            if self.just_calculated:
                if char.isdigit() or char == '.':
                    self._update_display(char)
                else:
                    self._update_display(current + char)
                self.just_calculated = False
            else:
                self._update_display(current + char)

    def _toggle_sign(self):
        current = self.display.get()
        if not current:
            return

        match = re.search(r'(\(-?[\d.]+\)|-?[\d.]+|pi|e)$', current)
        if match:
            last_part = match.group(1)
            start_index = match.start()
            prefix = current[:start_index]

            if last_part.startswith('(-') and last_part.endswith(')'):
                new_part = last_part[2:-1]
            elif last_part.startswith('(') and last_part.endswith(')'):
                new_part = "(-" + last_part[1:-1] + ")"
            elif last_part.startswith('-'):
                new_part = last_part[1:]
            else:
                new_part = "(-" + last_part + ")"

            self._update_display(prefix + new_part)

    def _apply_percent(self):
        current = self.display.get()
        if not current:
            return

        match = re.search(r'(\(-?[\d.]+\)|-?[\d.]+|pi|e)$', current)
        if match:
            last_part = match.group(1)
            start_index = match.start()
            prefix = current[:start_index]
            self._update_display(prefix + "(" + last_part + "/100)")

    def _handle_keypress(self, event):
        char = event.char
        keysym = event.keysym

        if char.isdigit() or char in "+-*/().%":
            if char == '*': char = '×'
            if char == '/': char = '÷'
            self._on_button_click(char)
        elif keysym == "Return":
            self._on_button_click('=')
        elif keysym == "BackSpace":
            self._backspace()
        elif keysym == "Escape":
            self._on_button_click('C')

    def _backspace(self):
        current = self.display.get()
        self._update_display(current[:-1])

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x600")
    # For better accessibility on macOS, you might consider using 'tkmacosx'
    # if installed, to better support background colors on buttons.
    app = CalculatorApp(root)
    root.mainloop()
