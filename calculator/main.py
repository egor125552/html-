import tkinter as tk
from tkinter import font
import re
import math

try:
    from .safe_eval import safe_eval
except ImportError:
    try:
        from safe_eval import safe_eval
    except ImportError:
        def safe_eval(expr): return "Error"

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessible Scientific Calculator")
        self.root.geometry("400x700")
        self.root.configure(bg="#121212")

        self.just_calculated = False

        # Fonts
        self.display_font = font.Font(family="Helvetica", size=32, weight="bold")
        self.button_font = font.Font(family="Helvetica", size=18, weight="bold")

        # Display
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            root,
            textvariable=self.display_var,
            font=self.display_font,
            bg="#121212",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            borderwidth=0,
            highlightthickness=2,
            highlightcolor="#00FF00",
            highlightbackground="#333333",
            justify="right",
            readonlybackground="#121212",
            state="readonly"
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=20)

        # Buttons configuration
        buttons = [
            ('sin', 1, 0), ('cos', 1, 1), ('tan', 1, 2), ('√', 1, 3),
            ('log', 2, 0), ('ln', 2, 1), ('!', 2, 2), ('xʸ', 2, 3),
            ('π', 3, 0), ('e', 3, 1), ('(', 3, 2), (')', 3, 3),
            ('C', 4, 0), ('%', 4, 1), ('±', 4, 2), ('÷', 4, 3),
            ('7', 5, 0), ('8', 5, 1), ('9', 5, 2), ('×', 5, 3),
            ('4', 6, 0), ('5', 6, 1), ('6', 6, 2), ('-', 6, 3),
            ('1', 7, 0), ('2', 7, 1), ('3', 7, 2), ('+', 7, 3),
            ('0', 8, 0), ('.', 8, 1), ('⌫', 8, 2), ('=', 8, 3),
        ]

        for (text, row, col) in buttons:
            self._create_button(text, row, col)

        # Grid configuration
        for i in range(9):
            self.root.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.root.grid_columnconfigure(i, weight=1)

        # Keyboard bindings
        self.root.bind("<Key>", self._handle_keypress)
        self.root.bind("<Return>", lambda e: self._calculate())
        self.root.bind("<BackSpace>", lambda e: self._backspace())
        self.root.bind("<Escape>", lambda e: self._clear())

    def _create_button(self, text, row, col):
        bg_color = "#333333"
        fg_color = "#FFFFFF"
        if text in ['=', '+', '-', '×', '÷', 'xʸ']:
            bg_color = "#FF9500"
            fg_color = "#000000"
        elif text == 'C':
            bg_color = "#FF3B30"
        elif text in ['sin', 'cos', 'tan', '√', 'log', 'ln', '!', 'π', 'e', '(', ')', '%', '±']:
            bg_color = "#555555"

        btn = tk.Button(
            self.root,
            text=text,
            font=self.button_font,
            bg=bg_color,
            fg=fg_color,
            activebackground="#666666",
            activeforeground="#FFFFFF",
            highlightthickness=2,
            highlightcolor="#00FF00",
            relief="flat",
            command=lambda t=text: self._on_button_click(t)
        )
        btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

    def _update_display(self, text):
        self.display.config(state="normal")
        self.display_var.set(text)
        self.display.config(state="readonly")
        self.display.xview_moveto(1) # Scroll to end

    def _on_button_click(self, char):
        current = self.display_var.get()

        # Map display labels to internal function names
        label_to_func = {
            '√': 'sqrt',
            '!': 'factorial',
            'xʸ': '**',
            'π': 'pi',
            '±': '+/-'
        }

        op = label_to_func.get(char, char)

        if op == '=':
            self._calculate()
        elif op == 'C':
            self._clear()
        elif op == '⌫':
            self._backspace()
        elif op == '+/-':
            self._toggle_sign()
        elif op == '%':
            self._apply_percent()
        elif op in ['sin', 'cos', 'tan', 'sqrt', 'log', 'ln', 'factorial']:
            if self.just_calculated:
                self._update_display(f"{op}({current})")
                self.just_calculated = False
            else:
                self._update_display(current + f"{op}(")
        else:
            if self.just_calculated:
                if char.isdigit() or char == '.':
                    self._update_display(char)
                else:
                    self._update_display(current + char)
                self.just_calculated = False
            else:
                self._update_display(current + char)

    def _calculate(self):
        expr = self.display_var.get()
        if not expr:
            return
        result = safe_eval(expr)
        self._update_display(result)
        self.just_calculated = True

    def _clear(self):
        self._update_display("")
        self.just_calculated = False

    def _backspace(self):
        current = self.display_var.get()
        self._update_display(current[:-1])
        self.just_calculated = False

    def _toggle_sign(self):
        current = self.display_var.get()
        # Regex to find the last number or parenthesized negative number
        pattern = r'(\(-?\d+\.?\d*\)|-?\d+\.?\d*)$'
        match = re.search(pattern, current)
        if match:
            num_str = match.group(1)
            if num_str.startswith('(-') and num_str.endswith(')'):
                new_num = num_str[2:-1]
            elif num_str.startswith('-'):
                new_num = num_str[1:]
            else:
                new_num = f"(-{num_str})"
            self._update_display(current[:match.start()] + new_num)

    def _apply_percent(self):
        current = self.display_var.get()
        pattern = r'(\(-?\d+\.?\d*\)|-?\d+\.?\d*)$'
        match = re.search(pattern, current)
        if match:
            num_str = match.group(1)
            # Remove parentheses if present
            clean_num = num_str.replace('(', '').replace(')', '')
            try:
                val = float(clean_num) / 100
                if val.is_integer():
                    val = int(val)
                self._update_display(current[:match.start()] + str(val))
            except ValueError:
                pass

    def _handle_keypress(self, event):
        char = event.char
        if char.isdigit() or char in '+-*/.%()':
            # Map visual operators
            mapping = {'*': '×', '/': '÷'}
            self._on_button_click(mapping.get(char, char))
        elif char == '^':
            self._on_button_click('**')

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
