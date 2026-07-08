import tkinter as tk
from tkinter import font as tkfont
import re
import math

try:
    from .safe_eval import safe_eval
except ImportError:
    try:
        from safe_eval import safe_eval
    except ImportError:
        def safe_eval(expr): return "Error"

class AccessibleButton(tk.Label):
    def __init__(self, master, text, command, **kwargs):
        self.command = command
        self.default_bg = kwargs.pop('bg', '#333333')
        self.active_bg = kwargs.pop('activebackground', '#444444')

        # Use a reasonable width/height if not provided, labels use characters for size like buttons
        width = kwargs.pop('width', 5)
        height = kwargs.pop('height', 2)

        super().__init__(master, text=text, bg=self.default_bg, fg='#FFFFFF',
                         font=("Arial", 18, "bold"), padx=5, pady=5,
                         highlightthickness=2, highlightbackground='#121212',
                         highlightcolor='#007AFF', takefocus=True,
                         width=width, height=height, bd=0, relief='flat', **kwargs)

        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Return>", lambda e: self.command())
        self.bind("<space>", lambda e: self.command())
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_enter(self, e):
        self.config(bg=self.active_bg)

    def _on_leave(self, e):
        self.config(bg=self.default_bg)

    def _on_focus_in(self, e):
        self.config(highlightbackground='#007AFF')

    def _on_focus_out(self, e):
        self.config(highlightbackground='#121212')

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessible Calculator")
        self.root.configure(bg='#121212')

        self.expression = ""
        self.just_calculated = False

        self._setup_ui()
        self._bind_keys()

    def _setup_ui(self):
        # Display
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            self.root,
            textvariable=self.display_var,
            font=("Arial", 32),
            bg='#121212',
            fg='#FFFFFF',
            insertbackground='#FFFFFF',
            justify='right',
            readonlybackground='#121212',
            state='readonly',
            highlightthickness=2,
            highlightcolor='#007AFF',
            bd=0
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=20)

        # Buttons grid
        buttons = [
            ('C', 1, 0), ('(', 1, 1), (')', 1, 2), ('÷', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('×', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('-', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('+', 4, 3),
            ('±', 5, 0), ('0', 5, 1), ('.', 5, 2), ('=', 5, 3),
            ('sin', 6, 0), ('cos', 6, 1), ('tan', 6, 2), ('√', 6, 3),
            ('log', 7, 0), ('ln', 7, 1), ('!', 7, 2), ('xʸ', 7, 3),
            ('π', 8, 0), ('e', 8, 1), ('abs', 8, 2), ('%', 8, 3)
        ]

        for (text, row, col) in buttons:
            self._create_button(text, row, col)

        for i in range(4):
            self.root.grid_columnconfigure(i, weight=1)
        for i in range(9):
            self.root.grid_rowconfigure(i, weight=1)

    def _create_button(self, text, row, col):
        btn = AccessibleButton(
            self.root,
            text=text,
            command=lambda t=text: self._on_button_click(t)
        )
        btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

    def _on_button_click(self, char):
        if char == '=':
            self._calculate()
        elif char == 'C':
            self._clear()
        elif char == '±':
            self._toggle_sign()
        elif char == '%':
            self._apply_percent()
        elif char == '√':
            self._append("sqrt(")
        elif char == 'xʸ':
            self._append("**")
        elif char == '×':
            self._append("*")
        elif char == '÷':
            self._append("/")
        elif char == '!':
            self._apply_factorial()
        elif char == 'sin':
            self._append("sin(")
        elif char == 'cos':
            self._append("cos(")
        elif char == 'tan':
            self._append("tan(")
        elif char == 'log':
            self._append("log(")
        elif char == 'ln':
            self._append("ln(")
        elif char == 'abs':
            self._append("abs(")
        elif char == 'π':
            self._append("pi")
        elif char == 'e':
            self._append("e")
        else:
            if self.just_calculated and char.isdigit():
                self._clear()
            self._append(char)
        self.just_calculated = False

    def _append(self, char):
        self.expression += str(char)
        self._update_display()

    def _clear(self):
        self.expression = ""
        self._update_display()

    def _calculate(self):
        if not self.expression:
            return
        result = safe_eval(self.expression)
        self.expression = str(result)
        self._update_display()
        self.just_calculated = True

    def _toggle_sign(self):
        pattern = re.compile(r'(\(-?\d+\.?\d*\)|-?\d+\.?\d*)$')
        match = pattern.search(self.expression)
        if match:
            last_token = match.group(1)
            if last_token.startswith('('):
                inner = last_token[1:-1]
                if inner.startswith('-'):
                    new_token = inner[1:]
                else:
                    new_token = f"-{inner}"
            else:
                if last_token.startswith('-'):
                    new_token = last_token[1:]
                else:
                    new_token = f"(-{last_token})"

            self.expression = self.expression[:match.start()] + new_token
            self._update_display()

    def _apply_percent(self):
        pattern = re.compile(r'(\(-?\d+\.?\d*\)|-?\d+\.?\d*)$')
        match = pattern.search(self.expression)
        if match:
            last_token = match.group(1).strip('()')
            try:
                new_value = float(last_token) / 100
                self.expression = self.expression[:match.start()] + str(new_value)
                self._update_display()
            except ValueError:
                pass

    def _apply_factorial(self):
        pattern = re.compile(r'(\(-?\d+\.?\d*\)|-?\d+\.?\d*)$')
        match = pattern.search(self.expression)
        if match:
            last_token = match.group(1)
            self.expression = self.expression[:match.start()] + f"factorial({last_token})"
            self._update_display()

    def _bind_keys(self):
        self.root.bind('<Key>', self._handle_keypress)

    def _handle_keypress(self, event):
        char = event.char
        keysym = event.keysym

        if char.isdigit() or char in '+-*/().%':
            if char == '*': char = '×'
            if char == '/': char = '÷'
            self._on_button_click(char)
        elif keysym == 'Return':
            self._on_button_click('=')
        elif keysym == 'Escape':
            self._on_button_click('C')
        elif keysym == 'BackSpace':
            self._backspace()
        elif char == '^':
            self._on_button_click('xʸ')
        elif char == 's': self._on_button_click('sin')
        elif char == 'c': self._on_button_click('cos')
        elif char == 't': self._on_button_click('tan')
        elif char == 'q': self._on_button_click('√')
        elif char == 'l': self._on_button_click('log')
        elif char == 'n': self._on_button_click('ln')
        elif char == '!': self._on_button_click('!')
        elif char == 'p': self._on_button_click('π')
        elif char == 'e': self._on_button_click('e')
        elif char == 'a': self._on_button_click('abs')

    def _backspace(self):
        if self.expression:
            if self.expression.endswith('sin(') or self.expression.endswith('cos(') or self.expression.endswith('tan(') or self.expression.endswith('log(') or self.expression.endswith('abs('):
                self.expression = self.expression[:-4]
            elif self.expression.endswith('sqrt('):
                self.expression = self.expression[:-5]
            elif self.expression.endswith('factorial('):
                 self.expression = self.expression[:-10]
            elif self.expression.endswith('ln(') or self.expression.endswith('pi'):
                self.expression = self.expression[:-3] if self.expression.endswith('ln(') else self.expression[:-2]
            elif self.expression.endswith('**'):
                self.expression = self.expression[:-2]
            else:
                self.expression = self.expression[:-1]
            self._update_display()

    def _update_display(self):
        # Display needs to be user friendly
        disp = self.expression.replace('*', '×').replace('/', '÷')
        disp = disp.replace('sqrt(', '√(').replace('**', '^')

        # Replace factorial(x) with x! for display
        # We use a loop to handle nested or multiple factorials
        while 'factorial(' in disp:
            new_disp = re.sub(r'factorial\(([^()]+)\)', r'\1!', disp)
            if new_disp == disp:
                break
            disp = new_disp

        disp = disp.replace('pi', 'π')

        self.display.config(state='normal')
        self.display_var.set(disp if disp else "0")
        self.display.config(state='readonly')

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
