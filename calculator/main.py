import tkinter as tk
import ast

class CalculatorApp:
    ERROR_MSG = "Ошибка"

    def __init__(self, master):
        self.master = master
        master.title("Доступный калькулятор")

        self.master.configure(bg="#2E2E2E")

        self.display = tk.Entry(
            master,
            font=("Arial", 24),
            borderwidth=0,
            relief="flat",
            justify="right",
            bg="#3C3C3C",
            fg="white",
            insertbackground="white",
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, ipady=10, sticky="nsew")

        button_layout = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("=", 4, 2), ("+", 4, 3),
            ("C", 5, 0, 2),
        ]

        for (text, row, col, *span) in button_layout:
            self.create_button(text, row, col, span[0] if span else 1)

    def create_button(self, text, row, col, colspan):
        button = tk.Button(
            self.master,
            text=text,
            font=("Arial", 18),
            borderwidth=0,
            relief="flat",
            bg="#505050",
            fg="white",
            activebackground="#6A6A6A",
            activeforeground="white",
            command=lambda: self.on_button_click(text),
        )
        button.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
        self.master.grid_columnconfigure(col, weight=1)
        self.master.grid_rowconfigure(row, weight=1)

    def on_button_click(self, char):
        if char == "C":
            self.display.delete(0, tk.END)
        elif char == "=":
            self.calculate()
        else:
            self.display.insert(tk.END, char)

    def calculate(self):
        try:
            expression = self.display.get()
            result = self.safe_eval(expression)
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
        except Exception:
            self.display.delete(0, tk.END)
            self.display.insert(0, self.ERROR_MSG)

    def safe_eval(self, expression):
        try:
            tree = ast.parse(expression, mode="eval")
            if self._check_nodes(tree.body):
                return eval(compile(tree, "<string>", "eval"), {"__builtins__": {}}, {})
            else:
                raise ValueError("Небезопасная операция")
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            raise

    def _check_nodes(self, node):
        if isinstance(node, ast.Expression):
            return self._check_nodes(node.body)
        elif isinstance(node, ast.Constant) or isinstance(node, ast.Num): # Num для Python < 3.8
            return True
        elif isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
        ):
            return self._check_nodes(node.left) and self._check_nodes(node.right)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return self._check_nodes(node.operand)
        return False

    def run(self):
        self.master.bind("<Return>", lambda event: self.calculate())
        self.master.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    app.run()
