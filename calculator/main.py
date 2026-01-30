import tkinter as tk
from tkinter import font as tkfont
import re
import math
try:
    from .safe_eval import safe_eval
except (ImportError, ValueError):
    from safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessible Scientific Calculator")
        self.root.geometry("400x700")
        self.root.configure(bg='#1c1c1c')

        self.expression = ""
        self.just_calculated = False

        self._setup_ui()
        self._bind_keys()

    def _setup_ui(self):
        # Display
        self.display_var = tk.StringVar(value="0")
        self.display_font = tkfont.Font(family='Arial', size=48, weight='bold')
        self.display_entry = tk.Entry(
            self.root, textvariable=self.display_var, justify='right',
            bg='#1c1c1c', fg='#ffffff', font=self.display_font,
            borderwidth=0, highlightthickness=0, readonlybackground='#1c1c1c'
        )
        self.display_entry.configure(state='readonly')
        self.display_entry.pack(fill='x', expand=False, padx=20, pady=20)

        # Buttons Frame
        self.buttons_frame = tk.Frame(self.root, bg='#1c1c1c')
        self.buttons_frame.pack(fill='both', expand=True)

        self.button_font = tkfont.Font(family='Arial', size=20, weight='bold')

        # (text, row, col, [columnspan], [color], [fg])
        buttons = [
            ('AC', 0, 0, 1, '#a5a5a5', '#000000'), ('(', 0, 1, 1, '#a5a5a5', '#000000'), (')', 0, 2, 1, '#a5a5a5', '#000000'), ('÷', 0, 3, 1, '#ff9500', '#ffffff'),
            ('7', 1, 0, 1, '#333333', '#ffffff'), ('8', 1, 1, 1, '#333333', '#ffffff'), ('9', 1, 2, 1, '#333333', '#ffffff'), ('×', 1, 3, 1, '#ff9500', '#ffffff'),
            ('4', 2, 0, 1, '#333333', '#ffffff'), ('5', 2, 1, 1, '#333333', '#ffffff'), ('6', 2, 2, 1, '#333333', '#ffffff'), ('-', 2, 3, 1, '#ff9500', '#ffffff'),
            ('1', 3, 0, 1, '#333333', '#ffffff'), ('2', 3, 1, 1, '#333333', '#ffffff'), ('3', 3, 2, 1, '#333333', '#ffffff'), ('+', 3, 3, 1, '#ff9500', '#ffffff'),
            ('0', 4, 0, 1, '#333333', '#ffffff'), ('.', 4, 1, 1, '#333333', '#ffffff'), ('=', 4, 2, 1, '#ff9500', '#ffffff'), ('^', 4, 3, 1, '#ff9500', '#ffffff'),
            ('%', 5, 0, 1, '#a5a5a5', '#000000'), ('+/-', 5, 1, 1, '#a5a5a5', '#000000'), ('C', 5, 2, 1, '#a5a5a5', '#000000'), ('√', 5, 3, 1, '#ff9500', '#ffffff'),
            ('sin', 6, 0, 1, '#505050', '#ffffff'), ('cos', 6, 1, 1, '#505050', '#ffffff'), ('tan', 6, 2, 1, '#505050', '#ffffff'), ('π', 6, 3, 1, '#505050', '#ffffff')
        ]

        for b in buttons:
            text, row, col = b[0], b[1], b[2]
            colspan = b[3] if len(b) > 3 else 1
            bg = b[4] if len(b) > 4 else '#333333'
            fg = b[5] if len(b) > 5 else '#ffffff'

            btn = tk.Button(
                self.buttons_frame, text=text, font=self.button_font,
                bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
                highlightthickness=0, borderwidth=0,
                command=lambda t=text: self._on_button_click(t)
            )
            btn.grid(row=row, column=col, columnspan=colspan, sticky='nsew', padx=1, pady=1)

        for i in range(7):
            self.buttons_frame.rowconfigure(i, weight=1)
        for i in range(4):
            self.buttons_frame.columnconfigure(i, weight=1)

    def _on_button_click(self, char):
        if char == 'AC':
            self.expression = ""
            self.just_calculated = False
        elif char == 'C':
            self.expression = self.expression[:-1]
        elif char == '=':
            self._calculate()
            return
        elif char == '+/-':
            self._toggle_sign()
            self._update_display()
            return
        elif char == '%':
            self._apply_percent()
            self._update_display()
            return
        elif char == '√':
            if self.just_calculated:
                self.expression = "√(" + self.expression + ")"
                self.just_calculated = False
            else:
                self.expression += "√("
        elif char in ('sin', 'cos', 'tan'):
            if self.just_calculated:
                self.expression = char + "(" + self.expression + ")"
                self.just_calculated = False
            else:
                self.expression += char + "("
        elif char == 'π':
            if self.just_calculated:
                self.expression = "π"
                self.just_calculated = False
            else:
                self.expression += "π"
        else:
            if self.just_calculated:
                if char.isdigit() or char == '(':
                    self.expression = ""
                self.just_calculated = False
            self.expression += char

        self._update_display()

    def _toggle_sign(self):
        pattern = re.compile(r'(\(-?([\d.]+)\)|-?([\d.]+)$)')
        match = pattern.search(self.expression)
        if match:
            full_match = match.group(0)
            start, end = match.span()
            if full_match.startswith('(') and full_match.endswith(')'):
                inner = full_match[1:-1]
                if inner.startswith('-'):
                    replacement = inner[1:]
                else:
                    replacement = '-' + inner
            else:
                if full_match.startswith('-'):
                    replacement = full_match[1:]
                else:
                    replacement = '-' + full_match

            self.expression = self.expression[:start] + replacement + self.expression[end:]

    def _apply_percent(self):
        pattern = re.compile(r'(-?[\d.]+)$')
        match = pattern.search(self.expression)
        if match:
            num_str = match.group(0)
            start, end = match.span()
            try:
                val = float(num_str) / 100
                self.expression = self.expression[:start] + str(val) + self.expression[end:]
            except ValueError:
                pass

    def _calculate(self):
        # Replace π with pi for safe_eval
        expr_to_eval = self.expression.replace('π', 'pi')
        result = safe_eval(expr_to_eval)
        self.display_entry.configure(state='normal')
        if result == "Error":
            self.display_var.set("Error")
            self.expression = ""
        else:
            if isinstance(result, (int, float)):
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                elif isinstance(result, float):
                    result = round(result, 10)
            self.display_var.set(str(result))
            self.expression = str(result)
            self.just_calculated = True
        self.display_entry.configure(state='readonly')

    def _update_display(self):
        self.display_entry.configure(state='normal')
        if not self.expression:
            self.display_var.set("0")
        else:
            self.display_var.set(self.expression)
        self.display_entry.configure(state='readonly')

    def _bind_keys(self):
        self.root.bind('<Key>', self._handle_keypress)

    def _handle_keypress(self, event):
        char = event.char
        keysym = event.keysym

        if char.isdigit() or char in '+-*/().%^':
            mapping = {'*': '×', '/': '÷'}
            self._on_button_click(mapping.get(char, char))
        elif keysym == 'Return':
            self._on_button_click('=')
        elif keysym == 'BackSpace':
            self._on_button_click('C')
        elif keysym == 'Escape':
            self._on_button_click('AC')

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
