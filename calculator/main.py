import tkinter as tk
import ast
import operator as op

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        if master:
            self.setup_ui()

    def setup_ui(self):
        self.master.title("Калькулятор")
        self.master.configure(bg='#333333')

        # Привязываем события клавиатуры к окну
        self.master.bind("<Key>", self.on_key_press)

        dark_bg = '#333333'
        button_bg = '#555555'
        text_color = '#FFFFFF'
        display_bg = '#444444'
        display_font = ('Arial', 24, 'bold')
        button_font = ('Arial', 16)

        self.display = tk.Entry(self.master, width=20, font=display_font,
                                bg=display_bg, fg=text_color,
                                borderwidth=10, relief=tk.FLAT, justify='right')
        self.display.grid(row=0, column=0, columnspan=4, padx=15, pady=15)
        self.display.focus_set() # Устанавливаем фокус на поле ввода

        for i in range(4):
            self.master.grid_columnconfigure(i, weight=1)
        for i in range(1, 6):
            self.master.grid_rowconfigure(i, weight=1)

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
            ('C', 5, 0, 4)
        ]

        for (text, row, col, *span) in buttons:
            width = span[0] if span else 1
            button = tk.Button(self.master, text=text, font=button_font,
                               bg=button_bg, fg=text_color,
                               borderwidth=0, relief=tk.FLAT,
                               command=lambda t=text: self.on_button_click(t))
            button.grid(row=row, column=col, columnspan=width, sticky='nsew', padx=2, pady=2)

    def on_key_press(self, event):
        """Обрабатывает нажатия клавиш."""
        key = event.keysym
        char = event.char

        if char in '0123456789./*-+':
            self.on_button_click(char)
        elif key == 'Return' or char == '=':
            self.on_button_click('=')
        elif key == 'BackSpace':
            current_text = self.display.get()
            if current_text:
                self.display.delete(len(current_text) - 1, tk.END)
        elif key == 'Escape' or char.lower() == 'c':
            self.on_button_click('C')

    def on_button_click(self, char):
        if char == 'C':
            self.display.delete(0, tk.END)
        elif char == '=':
            try:
                result = self.safe_eval(self.display.get())
                self.display.delete(0, tk.END)
                self.display.insert(0, str(result))
            except Exception:
                self.display.delete(0, tk.END)
                self.display.insert(0, "Ошибка")
        else:
            self.display.insert(tk.END, char)

    operators = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv
    }

    def safe_eval(self, expr):
        try:
            tree = ast.parse(expr, mode='eval').body
            return self._eval_node(tree)
        except (ValueError, TypeError, SyntaxError, ZeroDivisionError, KeyError):
            raise ValueError("Ошибка в выражении")

    def _eval_node(self, node):
        if isinstance(node, (ast.Constant, ast.Num)):
            return node.n if hasattr(node, 'n') else node.value
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self.operators:
                raise TypeError(f"Неподдерживаемая операция: {type(node.op).__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.operators[type(node.op)](left, right)
        else:
            raise TypeError(f"Неподдерживаемый тип узла: {type(node).__name__}")

if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
