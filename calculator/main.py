import tkinter as tk
import ast
import operator as op

class CalculatorApp:
    # Supported operators for safe evaluation
    operators = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod
    }

    ERROR_MSG = "Error"

    def __init__(self, master):
        self.master = master
        master.title("Calculator")
        master.geometry("400x600")

        # High-contrast dark theme
        master.configure(bg='#2E2E2E')
        self.entry_bg = '#1C1C1C'
        self.entry_fg = '#FFFFFF'
        self.button_bg = '#5C5C5C'
        self.button_fg = '#FFFFFF'
        self.button_active_bg = '#7C7C7C'
        self.operator_button_bg = '#FF8C00'
        self.operator_button_active_bg = '#FFA500'
        self.font = ('Arial', 18)
        self.display_font = ('Arial', 24)

        self.display = tk.Entry(master, width=20, font=self.display_font, borderwidth=0, relief="flat", justify='right', bg=self.entry_bg, fg=self.entry_fg, insertbackground=self.entry_fg)
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, ipady=10)

        # Bind the Enter key to the calculate function
        self.master.bind('<Return>', self.calculate_event)

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', 'C', '+'
        ]

        row_val = 1
        col_val = 0
        for button in buttons:
            self.create_button(button).grid(row=row_val, column=col_val, sticky="nsew", padx=5, pady=5)
            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

        self.create_button('=').grid(row=row_val, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)

        for i in range(6):
            master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            master.grid_columnconfigure(i, weight=1)

    def create_button(self, text):
        if text in '0123456789.':
            bg_color = self.button_bg
            active_bg_color = self.button_active_bg
        elif text == 'C':
            bg_color = self.button_bg
            active_bg_color = self.button_active_bg
        else:
            bg_color = self.operator_button_bg
            active_bg_color = self.operator_button_active_bg

        return tk.Button(self.master, text=text, padx=20, pady=20, font=self.font,
                         bg=bg_color, fg=self.button_fg, activebackground=active_bg_color,
                         activeforeground=self.button_fg, borderwidth=0, relief="flat",
                         command=lambda: self.on_button_click(text))

    def on_button_click(self, char):
        if char == '=':
            self.calculate()
        elif char == 'C':
            self.clear_display()
        else:
            self.display.insert(tk.END, char)

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num): # For older Python versions
            return node.n
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self.operators:
                raise TypeError(node)
            return self.operators[type(node.op)](self._eval_node(node.left), self._eval_node(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._eval_node(node.operand)
        elif isinstance(node, ast.Expression):
             return self._eval_node(node.body)
        else:
            raise TypeError(node)

    def safe_eval(self, expr):
        if not expr:
            return 0
        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree)
        except (TypeError, SyntaxError, KeyError, ZeroDivisionError, ValueError, AttributeError):
            raise ValueError("Invalid expression")

    def calculate_event(self, event):
        self.calculate()

    def calculate(self):
        try:
            expression = self.display.get()
            result = self.safe_eval(expression)
            self.clear_display()
            self.display.insert(0, str(result))
        except (ValueError, ZeroDivisionError):
            self.clear_display()
            self.display.insert(0, self.ERROR_MSG)

    def clear_display(self):
        self.display.delete(0, tk.END)

if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
