import tkinter as tk
import ast

class CalculatorApp:
    ERROR_MSG = "Ошибка"

    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")
        master.configure(bg="#2E2E2E")

        self.display = tk.Entry(master, width=20, font=('Arial', 24), bd=10, insertwidth=2, bg="#4A4A4A", fg="white", justify='right')
        self.display.grid(row=0, column=0, columnspan=4, pady=10)
        self.display.bind("<Return>", self.calculate)

        buttons = [
            ['(', ')', '**', 'C'],
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', '.', '=', '+']
        ]

        for row_val, row in enumerate(buttons, start=1):
            for col_val, button_text in enumerate(row):
                self.create_button(button_text).grid(row=row_val, column=col_val, sticky="nsew")

        for i in range(6):
            self.master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.master.grid_columnconfigure(i, weight=1)

    def create_button(self, text):
        return tk.Button(self.master, text=text, padx=20, pady=20, font=('Arial', 18), bg="#6A6A6A", fg="white",
                         command=lambda: self.on_button_click(text))

    def safe_eval(self, expr):
        try:
            node = ast.parse(expr, mode='eval').body
            return self._eval_node(node)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError, RecursionError):
            return self.ERROR_MSG

    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            else:
                 raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._eval_node(node.operand)
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")

    def calculate(self, event=None):
        try:
            expression = self.display.get()
            result = self.safe_eval(expression)
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, str(result))
        except Exception:
            self.display.delete(0, tk.END)
            self.display.insert(tk.END, self.ERROR_MSG)

    def on_button_click(self, char):
        if char == 'C':
            self.display.delete(0, tk.END)
        elif char == '=':
            self.calculate()
        else:
            self.display.insert(tk.END, char)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
