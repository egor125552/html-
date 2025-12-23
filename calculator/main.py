import tkinter as tk
import ast

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")

        self.expression = ""
        self.display_var = tk.StringVar()
        self.just_calculated = False

        # Настройка цветов для доступности
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.button_bg = "#4A4A4A"
        self.button_fg = "#FFFFFF"
        self.special_button_bg = "#FF8C00"

        master.configure(bg=self.bg_color)

        # Поле для вывода результата
        self.display = tk.Entry(master, textvariable=self.display_var, font=('Arial', 24), bd=10, insertwidth=2, width=14, borderwidth=4, bg=self.bg_color, fg=self.fg_color, justify='right')
        self.display.grid(row=0, column=0, columnspan=4, pady=10)
        self.display_var.set('0')

        # Кнопки
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        row_val = 1
        col_val = 0
        for button in buttons:
            action = lambda x=button: self.click(x)
            if button == '=':
                tk.Button(master, text=button, padx=20, pady=20, font=('Arial', 18), command=action, bg=self.special_button_bg, fg=self.button_fg).grid(row=row_val, column=col_val, sticky="nsew")
            else:
                tk.Button(master, text=button, padx=20, pady=20, font=('Arial', 18), command=action, bg=self.button_bg, fg=self.button_fg).grid(row=row_val, column=col_val, sticky="nsew")

            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

        # Кнопка сброса
        tk.Button(master, text='C', padx=20, pady=20, font=('Arial', 18), command=self.clear, bg=self.special_button_bg, fg=self.button_fg).grid(row=row_val, column=0, columnspan=4, sticky="nsew")

        # Настройка растягивания колонок и строк
        for i in range(4):
            master.grid_columnconfigure(i, weight=1)
        for i in range(row_val + 1):
            master.grid_rowconfigure(i, weight=1)

    def click(self, key):
        if key == '=':
            try:
                result = self.evaluate_expression(self.expression)
                self.display_var.set(str(result))
                self.expression = str(result)
                self.just_calculated = True
            except Exception as e:
                self.display_var.set("Ошибка")
                self.expression = ""
        else:
            operators = ['/', '*', '-', '+']

            if self.just_calculated:
                # Если нажата цифра после вычисления, начинаем новое выражение
                if key not in operators and key != '.':
                    self.expression = ""
                self.just_calculated = False

            if key in operators:
                # Заменяем последний оператор, если он уже есть
                if self.expression and self.expression[-1] in operators:
                    self.expression = self.expression[:-1] + key
                else:
                    self.expression += key
            else:  # Для цифр и точки
                if self.display_var.get() == '0' and key != '.':
                    self.expression = key
                else:
                    self.expression += key

            self.display_var.set(self.expression)

    def clear(self):
        self.expression = ""
        self.display_var.set("0")
        self.just_calculated = False

    def evaluate_expression(self, expression):
        """
        Безопасно вычисляет математическое выражение.
        Использует ast.parse для предотвращения выполнения вредоносного кода.
        """
        try:
            # Парсим выражение
            tree = ast.parse(expression, mode='eval')

            # Проверяем, что в выражении только разрешенные узлы
            # 'Constant' для Python 3.8+, 'Num' для более старых версий
            allowed_nodes = {
                'Expression', 'BinOp', 'UnaryOp', 'Num', 'Add', 'Sub', 'Mult', 'Div', 'USub', 'UAdd', 'Constant'
            }
            for node in ast.walk(tree):
                if type(node).__name__ not in allowed_nodes:
                    raise ValueError("Недопустимая операция")

            # Вычисляем и округляем результат
            result = eval(compile(tree, filename='<string>', mode='eval'))
            if isinstance(result, float):
                return round(result, 10)
            return result
        except (SyntaxError, ValueError, ZeroDivisionError, TypeError) as e:
            # Возвращаем ошибку, если выражение некорректно
            return "Ошибка"


if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
