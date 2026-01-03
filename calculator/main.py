import tkinter as tk
import ast
import re
import math
from tkinter import font


class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Доступный калькулятор")
        self.geometry("400x700")  # Увеличим высоту для новых кнопок
        self.configure(bg="#1e1e1e")

        # Белый список безопасных функций
        self.SAFE_FUNCTIONS = {
            "sin": math.sin,
            "cos": math.cos,
            "log": math.log,
            "sqrt": math.sqrt,
        }

        self._create_widgets()

    def _create_widgets(self):
        # Настройка шрифтов
        main_font = font.Font(family="Helvetica", size=18)
        display_font = font.Font(family="Helvetica", size=36, weight="bold")

        # Дисплей
        self.display = tk.Entry(
            self,
            font=display_font,
            borderwidth=0,
            relief="flat",
            justify="right",
            bg="#1e1e1e",
            fg="white",
        )
        self.display.pack(pady=20, padx=10, fill="x")

        # Фрейм для кнопок
        button_frame = tk.Frame(self, bg="#1e1e1e")
        button_frame.pack(fill="both", expand=True)

        # Расположение кнопок
        buttons = [
            "sin",
            "cos",
            "log",
            "sqrt",
            "7",
            "8",
            "9",
            "/",
            "4",
            "5",
            "6",
            "*",
            "1",
            "2",
            "3",
            "-",
            "0",
            ".",
            "=",
            "+",
        ]

        row, col = 0, 0
        for button_text in buttons:
            self._create_button(button_frame, button_text, main_font, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Кнопка очистки
        clear_button = tk.Button(
            button_frame,
            text="C",
            font=main_font,
            bg="#3c3c3c",
            fg="white",
            relief="flat",
            command=self._clear_display,
        )
        clear_button.grid(
            row=row, column=0, columnspan=2, sticky="nsew", padx=5, pady=5
        )

        # Кнопка скобок
        paren_button = tk.Button(
            button_frame,
            text="()",
            font=main_font,
            bg="#3c3c3c",
            fg="white",
            relief="flat",
            command=lambda: self._on_button_click("()"),
        )
        paren_button.grid(
            row=row, column=2, columnspan=2, sticky="nsew", padx=5, pady=5
        )

        # Настройка сетки
        for i in range(6):  # Увеличиваем количество строк
            button_frame.rowconfigure(i, weight=1)
        for i in range(4):
            button_frame.columnconfigure(i, weight=1)

    def _create_button(self, parent, text, font, row, col):
        btn = tk.Button(
            parent,
            text=text,
            font=font,
            bg="#3c3c3c",
            fg="white",
            relief="flat",
            command=lambda: self._on_button_click(text),
        )
        btn.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        return btn

    def _on_button_click(self, char):
        if char == "=":
            self._calculate()
        elif char in self.SAFE_FUNCTIONS:
            self.display.insert(tk.END, f"{char}(")
        elif char == "()":
            # Просто вставляем скобки
            self.display.insert(tk.END, "()")
        else:
            self.display.insert(tk.END, char)

    def _clear_display(self):
        self.display.delete(0, tk.END)

    def _calculate(self):
        expression = self.display.get()
        try:
            # Очищаем дисплей перед отображением результата или ошибки
            self.display.delete(0, tk.END)

            # Проверка на последовательные операторы
            if re.search(r"[\+\-\*\/]{2,}", expression):
                raise ValueError("Недопустимое выражение")

            # Разбираем выражение в AST (абстрактное синтаксическое дерево)
            node = ast.parse(expression, mode="eval")

            # Проверяем, что все узлы в дереве разрешены
            self._check_nodes(node)

            # Компилируем и вычисляем AST
            code = compile(node, "<string>", "eval")
            # Передаем безопасные функции в eval
            result = eval(code, {"__builtins__": {}}, self.SAFE_FUNCTIONS)

            self.display.insert(tk.END, str(float(result)))
        except (SyntaxError, ZeroDivisionError, TypeError, ValueError):
            # В случае ошибки показываем сообщение
            self.display.insert(tk.END, "Ошибка")
        except Exception as e:
            # Обработка других непредвиденных ошибок
            print(f"Произошла непредвиденная ошибка: {e}")
            self.display.insert(tk.END, "Ошибка")

    def _check_nodes(self, node):
        # Рекурсивно проверяем все узлы в дереве
        for n in ast.walk(node):
            # Белый список разрешенных типов узлов
            # Белый список разрешенных типов узлов
            allowed_nodes = [
                ast.Expression,
                ast.Constant,
                ast.Num,
                ast.BinOp,
                ast.UnaryOp,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.Pow,
                ast.Mod,
                ast.USub,
                ast.UAdd,
                ast.Call,
                ast.Name,
                ast.Load,
            ]
            if type(n) not in allowed_nodes:
                raise ValueError("Недопустимая операция")

            # Если узел - это вызов функции, проверяем имя
            if isinstance(n, ast.Name) and n.id not in self.SAFE_FUNCTIONS:
                raise ValueError(f"Недопустимая функция: {n.id}")


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
