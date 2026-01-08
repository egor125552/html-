import tkinter as tk
import ast
import operator as op

# Поддерживаемые операторы
operators = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
    ast.USub: op.neg
}

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")

        # Настройки для доступности
        master.configure(bg="#2E2E2E")
        self.font = ("Arial", 24)
        self.entry_font = ("Arial", 36)

        # Поле для ввода и вывода
        self.entry = tk.Entry(master, font=self.entry_font, borderwidth=0, relief="flat", justify="right", bg="#4A4A4A", fg="#FFFFFF")
        self.entry.grid(row=0, column=0, columnspan=4, padx=10, pady=20, sticky="nsew")

        # Кнопки
        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
            ('C', 5, 0, 2)
        ]

        for (text, row, col, *span) in buttons:
            colspan = span[0] if span else 1
            self.create_button(text, row, col, colspan)

        # Настройка сетки
        for i in range(6):
            master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            master.grid_columnconfigure(i, weight=1)

    def create_button(self, text, row, col, colspan=1):
        if text == '=':
            bg_color = "#FFA500" # Orange
            fg_color = "#FFFFFF"
        elif text in '/*-+':
            bg_color = "#666666" # Dark Gray
            fg_color = "#FFFFFF"
        elif text == 'C':
            bg_color = "#D3D3D3" # Light Gray
            fg_color = "#000000"
        else:
            bg_color = "#4A4A4A" # Gray
            fg_color = "#FFFFFF"

        button = tk.Button(self.master, text=text, font=self.font,
                           command=lambda: self.on_button_click(text),
                           bg=bg_color, fg=fg_color, borderwidth=0, relief="flat",
                           activebackground="#555555", activeforeground="#FFFFFF")
        button.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
        return button

    def on_button_click(self, char):
        if char == 'C':
            self.entry.delete(0, tk.END)
        elif char == '=':
            try:
                result = self.safe_eval(self.entry.get())
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, str(result))
            except Exception as e:
                self.entry.delete(0, tk.END)
                self.entry.insert(tk.END, "Error")
        else:
            self.entry.insert(tk.END, char)

    def safe_eval(self, expr):
        """Безопасное вычисление строки с использованием AST."""
        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree.body)
        except (SyntaxError, ZeroDivisionError, TypeError, KeyError):
            raise ValueError("Invalid expression")

    def _eval_node(self, node):
        """Рекурсивное вычисление узла AST."""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant): # Для Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            return operators[type(node.op)](operand)
        else:
            raise TypeError(f"Unsupported node type: {type(node).__name__}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
