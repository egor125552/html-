import tkinter as tk
from tkinter import font
import ast

class CalculatorApp:
    ERROR_MSG = "Ошибка"

    @staticmethod
    def _check_nodes(node):
        if isinstance(node, ast.Expression):
            return CalculatorApp._check_nodes(node.body)
        elif isinstance(node, (ast.Constant, ast.Num)):
            return True
        elif isinstance(node, ast.BinOp):
            allowed_ops = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
            if not isinstance(node.op, allowed_ops): return False
            return CalculatorApp._check_nodes(node.left) and CalculatorApp._check_nodes(node.right)
        elif isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, ast.USub): return False
            return CalculatorApp._check_nodes(node.operand)
        elif isinstance(node, ast.Call): # Allow parentheses
            return False
        return True

    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")
        master.geometry("400x600")
        master.configure(bg='#2E2E2E')

        for i in range(4): master.grid_columnconfigure(i, weight=1)
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=5) # Adjust for extra row

        self.display_font = font.Font(size=24)
        self.button_font = font.Font(size=18)
        self.expression = ""
        self.is_error = False

        self.display = tk.Entry(
            master, font=self.display_font, bg='#1E1E1E', fg='#FFFFFF',
            justify='right', bd=0, insertbackground='white'
        )
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        self.create_buttons()
        self.bind_keyboard()
        self.display.focus_set()

    def bind_keyboard(self):
        self.master.bind('<Key>', self.on_key_press)
        self.master.bind('<Return>', self.on_return_key)
        self.master.bind('<Escape>', lambda e: self.on_button_click('C'))
        self.master.bind('<BackSpace>', self.on_backspace)

    def on_return_key(self, event=None):
        if self.master.focus_get() == self.display:
            self.on_button_click('=')

    def on_key_press(self, event):
        if event.char and event.char in '0123456789./*-+^%()':
            self.on_button_click(event.char)

    def on_backspace(self, event=None):
        if self.is_error: self.expression = ""
        else: self.expression = self.expression[:-1]
        self.is_error = False
        self.update_display()

    def on_button_click(self, char):
        if self.is_error: self.expression = ""
        self.is_error = False

        if char == 'C': self.expression = ""
        elif char == '=':
            self.calculate()
            return
        else: self.expression += str(char)

        self.update_display()

    def calculate(self):
        if not self.expression: return
        try:
            expr = self.expression.replace('^', '**')
            tree = ast.parse(expr, mode='eval')
            if not self._check_nodes(tree): raise ValueError("Unsupported op")
            result = eval(compile(tree, '<string>', 'eval'), {'__builtins__': {}})
            self.expression = str(int(result) if result == int(result) else result)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            self.expression = self.ERROR_MSG
            self.is_error = True
        self.update_display()

    def update_display(self):
        self.display.delete(0, tk.END)
        self.display.insert(0, self.expression)

    def create_buttons(self):
        frame = tk.Frame(self.master, bg='#2E2E2E')
        frame.grid(row=1, column=0, columnspan=4, sticky="nsew")
        for i in range(6): frame.grid_rowconfigure(i, weight=1) # 6 rows
        for i in range(4): frame.grid_columnconfigure(i, weight=1)

        buttons = [
            ('C', 0, 0, 1), ('%', 0, 1, 1), ('^', 0, 2, 1), ('/', 0, 3, 1),
            ('7', 1, 0, 1), ('8', 1, 1, 1), ('9', 1, 2, 1), ('*', 1, 3, 1),
            ('4', 2, 0, 1), ('5', 2, 1, 1), ('6', 2, 2, 1), ('-', 2, 3, 1),
            ('1', 3, 0, 1), ('2', 3, 1, 1), ('3', 3, 2, 1), ('+', 3, 3, 1),
            ('(', 4, 0, 1), (')', 4, 1, 1), ('.', 4, 2, 1), ('=', 4, 3, 1),
            ('0', 5, 0, 4) # Zero on the last row
        ]

        for (text, r, c, s) in buttons: self.create_button(text, r, c, s, frame)

    def create_button(self, text, r, c, s, frame):
        is_op = text in ['/', '*', '-', '+', '=', '^', '%']
        is_special = text in ['C', '(', ')']

        if is_op: bg_color = '#FF9500'
        elif is_special: bg_color = '#A5A5A5'
        else: bg_color = '#4F4F4F'

        btn = tk.Button(
            frame, text=text, font=self.button_font, bg=bg_color, fg='#FFFFFF',
            bd=0, highlightthickness=0, activebackground='#6D6D6D', activeforeground='#FFFFFF',
            command=lambda t=text: self.on_button_click(t)
        )
        btn.grid(row=r, column=c, columnspan=s, sticky="nsew", padx=2, pady=2)
        return btn

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()