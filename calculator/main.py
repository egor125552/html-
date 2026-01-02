import tkinter as tk
import ast

class CalculatorApp:
    """
    Класс для создания приложения-калькулятора с использованием tkinter.
    """
    ERROR_MSG = "Ошибка"
    ALLOWED_NODES = {
        'Expression', 'Constant', 'Num', 'BinOp', 'UnaryOp', 'Add', 'Sub', 'Mult', 'Div', 'Pow', 'Mod', 'USub'
    }

    def __init__(self, master):
        """
        Инициализирует калькулятор.
        """
        self.master = master
        master.title("Супер Калькулятор")
        master.configure(bg="#000000")
        master.bind('<Return>', self.calculate)

        # Поле для ввода и вывода
        self.display = tk.Entry(master, width=20, font=('Arial', 24), bd=10, insertwidth=4, justify='right', bg="#333333", fg="#FFFFFF")
        self.display.grid(row=0, column=0, columnspan=4, pady=10)

        # Рамка для кнопок
        button_frame = tk.Frame(master, bg="#000000")
        button_frame.grid(row=1, column=0, columnspan=4)

        # Определение кнопок
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '=', '+',
            '**', '%'
        ]

        # Создание и размещение кнопок
        row_val = 0
        col_val = 0
        for button in buttons:
            self.create_button(button_frame, button).grid(row=row_val, column=col_val, padx=5, pady=5)
            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

    def create_button(self, frame, text):
        """
        Создает кнопку с заданным текстом и стилем.
        """
        return tk.Button(frame, text=text, width=5, height=2, font=('Arial', 18), bg="#666666", fg="#FFFFFF",
                         command=lambda: self.on_button_click(text))

    def on_button_click(self, char):
        """
        Обрабатывает нажатия кнопок.
        """
        if char == 'C':
            self.display.delete(0, tk.END)
        elif char == '=':
            self.calculate()
        else:
            self.display.insert(tk.END, char)

    def calculate(self, event=None):
        """
        Вычисляет выражение в поле ввода.
        """
        expression = self.display.get()
        try:
            result = self.safe_eval(expression)
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            self.display.delete(0, tk.END)
            self.display.insert(0, self.ERROR_MSG)

    def safe_eval(self, expr):
        """
        Безопасно вычисляет строку, разрешая только базовые математические операции.
        """
        if not expr:
            raise ValueError("Пустое выражение")
        try:
            tree = ast.parse(expr, mode='eval')
            if not self._check_nodes(tree):
                raise ValueError("Недопустимая операция")
            return eval(compile(tree, filename='<ast>', mode='eval'))
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
             raise ValueError("Недопустимое выражение")

    def _check_nodes(self, node):
        """
        Рекурсивно проверяет, что все узлы в AST разрешены.
        """
        if isinstance(node, ast.AST):
            if node.__class__.__name__ not in self.ALLOWED_NODES:
                return False
            for child in ast.iter_child_nodes(node):
                if not self._check_nodes(child):
                    return False
        return True


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
