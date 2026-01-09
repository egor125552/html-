
import tkinter as tk
from tkinter import font

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Accessible Calculator")
        master.configure(bg="#2E2E2E")

        # Font configuration
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Arial", size=16)
        self.entry_font = font.Font(family="Arial", size=24, weight="bold")
        self.button_font = font.Font(family="Arial", size=18)

        # Display
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            master,
            textvariable=self.display_var,
            font=self.entry_font,
            bd=10,
            insertwidth=2,
            width=14,
            justify="right",
            bg="#4A4A4A",
            fg="white",
            disabledbackground="#4A4A4A",
            disabledforeground="white"
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, ipady=10)
        self.display.config(state='disabled')

        # Button layout
        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('C', 4, 2), ('+', 4, 3),
            ('=', 5, 0, 4)
        ]

        self.expression = ""
        self.just_calculated = False
        for (text, row, col, *span) in buttons:
            self.create_button(text, row, col, *span)

        master.bind('<KeyPress>', self.on_key_press)

    def on_key_press(self, event):
        key = event.keysym
        if key in '0123456789.':
            self.on_button_click(key)
        elif key in ('plus', 'minus', 'asterisk', 'slash'):
            op_map = {'plus': '+', 'minus': '-', 'asterisk': '*', 'slash': '/'}
            self.on_button_click(op_map[key])
        elif key in ('Return', 'equal'):
            self.on_button_click('=')
        elif key == 'Escape':
            self.on_button_click('C')

    def create_button(self, text, row, col, *span):
        button = tk.Button(
            self.master,
            text=text,
            font=self.button_font,
            command=lambda: self.on_button_click(text),
            bg="#6A6A6A",
            fg="white",
            activebackground="#7A7A7A",
            activeforeground="white",
            bd=0,
            padx=20,
            pady=20,
            highlightthickness=0
        )
        colspan = span[0] if span else 1
        button.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=5, pady=5)
        self.master.grid_columnconfigure(col, weight=1)
        self.master.grid_rowconfigure(row, weight=1)

    def on_button_click(self, char):
        self.display.config(state='normal')
        if char == 'C':
            self.expression = ""
            self.display_var.set("")
            self.just_calculated = False
        elif char == '=':
            if self.expression:
                try:
                    result = self.safe_eval(self.expression)
                    self.display_var.set(str(result))
                    self.expression = str(result)
                    self.just_calculated = True
                except Exception:
                    self.display_var.set("Error")
                    self.expression = ""
        elif char in "+-*/":
            if self.expression and self.expression[-1] not in "+-*/":
                self.expression += char
                self.display_var.set(self.expression)
            self.just_calculated = False
        else: # Digits and dot
            if self.just_calculated:
                self.expression = ""
                self.just_calculated = False
            self.expression += char
            self.display_var.set(self.expression)
        self.display.config(state='disabled')

    def safe_eval(self, expr):
        import ast
        import operator as op

        operators = {
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
            ast.Div: op.truediv, ast.USub: op.neg
        }

        def _eval_node(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Num): # For older Python
                return node.n
            elif isinstance(node, ast.BinOp):
                left = _eval_node(node.left)
                right = _eval_node(node.right)
                return operators[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = _eval_node(node.operand)
                return operators[type(node.op)](operand)
            else:
                raise TypeError(node)

        tree = ast.parse(expr, mode='eval').body
        return float(_eval_node(tree))


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
