import tkinter as tk
from tkinter import font as tkfont
import re
try:
    from .safe_eval import safe_eval
except ImportError:
    from safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessible Calculator")
        self.root.configure(bg='#2d2d2d')

        # High contrast theme colors
        self.bg_color = '#2d2d2d'
        self.fg_color = '#ffffff'
        self.btn_bg = '#3d3d3d'
        self.highlight_color = '#007aff' # macOS style blue highlight

        self.display_font = tkfont.Font(family='Arial', size=32, weight='bold')
        self.button_font = tkfont.Font(family='Arial', size=18)

        self.just_calculated = False

        self._setup_ui()
        self._bind_keys()

    def _setup_ui(self):
        # Display
        self.display_var = tk.StringVar(value="0")
        self.display = tk.Entry(
            self.root,
            textvariable=self.display_var,
            font=self.display_font,
            bg=self.bg_color,
            fg=self.fg_color,
            borderwidth=0,
            highlightthickness=2,
            highlightbackground=self.bg_color,
            highlightcolor=self.highlight_color,
            justify='right',
            readonlybackground=self.bg_color,
            state='readonly'
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky='nsew', padx=10, pady=20)

        # Button layout (7 rows x 4 columns)
        buttons = [
            ('sin(', 'cos(', 'tan(', 'log('),
            ('sqrt(', 'exp(', '^', 'pi'),
            ('e', '%', '+/-', 'C'),
            ('7', '8', '9', '÷'),
            ('4', '5', '6', '×'),
            ('1', '2', '3', '-'),
            ('0', '.', '=', '+')
        ]

        for r, row in enumerate(buttons, start=1):
            for c, text in enumerate(row):
                self._create_button(text, r, c)

        # Configure grid weights for responsiveness
        for i in range(4):
            self.root.grid_columnconfigure(i, weight=1)
        for i in range(8):
            self.root.grid_rowconfigure(i, weight=1)

    def _create_button(self, text, row, col):
        btn = tk.Button(
            self.root,
            text=text,
            font=self.button_font,
            bg=self.btn_bg,
            fg=self.fg_color,
            activebackground=self.highlight_color,
            activeforeground=self.fg_color,
            highlightthickness=2,
            highlightbackground=self.bg_color,
            highlightcolor=self.fg_color,
            command=lambda t=text: self._on_button_click(t),
            width=5,
            height=2
        )
        btn.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)

    def _on_button_click(self, text):
        if text == '=':
            self._calculate()
        elif text == 'C':
            self._clear()
        elif text == '+/-':
            self._toggle_sign()
        elif text == '%':
            self._apply_percent()
        else:
            self._append_text(text)

    def _append_text(self, text):
        # Map visual symbols back to math operators if needed
        if text == '×': text = '*'
        if text == '÷': text = '/'

        current = self.display_var.get()

        if self.just_calculated:
            if text.isdigit() or text in ('pi', 'e', 'sin(', 'cos(', 'tan(', 'log(', 'sqrt(', 'exp('):
                current = ""
            self.just_calculated = False

        if current == "0" and text not in ('.', '+', '-', '*', '/', '^'):
            new_text = text
        else:
            new_text = current + text

        self._update_display(new_text)

    def _update_display(self, text):
        self.display.config(state='normal')
        self.display_var.set(text)
        self.display.config(state='readonly')
        self.display.xview_moveto(1) # Scroll to the end

    def _clear(self):
        self._update_display("0")
        self.just_calculated = False

    def _calculate(self):
        expr = self.display_var.get()
        # Clean up expression for safe_eval
        expr = expr.replace('×', '*').replace('÷', '/')
        result = safe_eval(expr)
        self._update_display(result)
        self.just_calculated = True

    def _toggle_sign(self):
        current = self.display_var.get()
        # Find the last number in the expression
        pattern = r'(\(-?([\d.]+)\)|-?([\d.]+)$)'
        match = re.search(pattern, current)
        if match:
            full_match = match.group(0)
            if full_match.startswith('('):
                # It's already negated, e.g., (-5)
                inner = match.group(2)
                new_val = inner
            else:
                # It's not negated or it's a simple negative number without parens
                if full_match.startswith('-'):
                    new_val = full_match[1:]
                else:
                    new_val = f"(-{full_match})"

            new_text = current[:match.start()] + new_val
            self._update_display(new_text)

    def _apply_percent(self):
        current = self.display_var.get()
        pattern = r'(-?[\d.]+)$'
        match = re.search(pattern, current)
        if match:
            num_str = match.group(1)
            try:
                val = float(num_str) / 100
                if val.is_integer():
                    new_val = str(int(val))
                else:
                    new_val = str(val)
                new_text = current[:match.start()] + new_val
                self._update_display(new_text)
            except ValueError:
                pass

    def _backspace(self):
        current = self.display_var.get()
        if len(current) > 1:
            self._update_display(current[:-1])
        else:
            self._update_display("0")

    def _bind_keys(self):
        self.root.bind('<Key>', self._handle_keypress)
        self.root.bind('<Return>', lambda e: self._calculate())
        self.root.bind('<Escape>', lambda e: self._clear())
        self.root.bind('<BackSpace>', lambda e: self._backspace())

    def _handle_keypress(self, event):
        char = event.char
        if char in '0123456789.+-*/^%()':
            self._append_text(char)
        elif char == '=':
            self._calculate()
        elif char == '*':
            self._append_text('×')
        elif char == '/':
            self._append_text('÷')

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
