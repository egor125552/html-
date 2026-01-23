import tkinter as tk
from tkinter import font
# Используем относительный импорт, так как main.py и safe_eval.py находятся в одном пакете
from .safe_eval import safe_eval

class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Настройки окна
        self.title("Доступный калькулятор")
        self.geometry("400x600")
        self.configure(bg="#2e2e2e")
        self.resizable(False, False)

        # Стили
        self.large_font = font.Font(family="Helvetica", size=18)
        self.display_font = font.Font(family="Helvetica", size=36, weight="bold")

        # Переменная для хранения выражения
        self.expression = tk.StringVar()
        self.just_calculated = False # Флаг состояния: True, если последнее действие - вычисление

        self._create_widgets()
        self.bind_all("<Key>", self._handle_keypress) # Привязываем события клавиатуры

    def _handle_keypress(self, event):
        """Обрабатывает нажатия клавиш."""
        char = event.char
        keysym = event.keysym

        if keysym == "Return" or char == "=":
            self._calculate()
        elif keysym == "BackSpace":
            self._on_button_click('←')
        elif keysym == "Escape":
            self._on_button_click('C')
        elif char in "0123456789.()+-":
            self._on_button_click(char)
        elif char == '*':
            self._on_button_click('×')
        elif char == '/':
            self._on_button_click('÷')

    def _create_widgets(self):
        # Поле вывода
        display_frame = tk.Frame(self)
        display_frame.pack(fill="x", padx=10, pady=20)

        display = tk.Entry(display_frame, textvariable=self.expression, font=self.display_font,
                           bg="#3c3c3c", fg="white", justify="right", bd=0, state="readonly")
        display.pack(fill="both", expand=True)

        # Кнопки
        buttons_frame = tk.Frame(self, bg="#2e2e2e")
        buttons_frame.pack(fill="both", expand=True, padx=5, pady=5)

        buttons = [
            ('C', 1, 0), ('←', 1, 1), ('(', 1, 2), (')', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('÷', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('×', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('-', 4, 3),
            ('0', 5, 0, 2), ('.', 5, 2), ('+', 5, 3),
            ('=', 6, 0, 4)
        ]

        for (text, row, col, *span) in buttons:
            buttons_frame.grid_columnconfigure(col, weight=1)
            buttons_frame.grid_rowconfigure(row, weight=1)

            if text in "0123456789.": btn_bg, btn_fg = "#505050", "white"
            elif text in "÷×-+()": btn_bg, btn_fg = "#ff9500", "white"
            elif text == "=": btn_bg, btn_fg = "#ff9500", "white"
            else: btn_bg, btn_fg = "#d4d4d2", "black"

            btn = tk.Button(buttons_frame, text=text, font=self.large_font,
                            bg=btn_bg, fg=btn_fg, bd=0, relief="flat",
                            activebackground="#3c3c3c", activeforeground="white",
                            command=lambda t=text: self._on_button_click(t))

            colspan = span[0] if span else 1
            btn.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=2, pady=2)

    def _on_button_click(self, char):
        current_expression = self.expression.get()

        if char == 'C':
            self.expression.set("")
            self.just_calculated = False
        elif char == '←':
            if self.just_calculated:
                self.expression.set("")
                self.just_calculated = False
            else:
                self.expression.set(current_expression[:-1])
        elif char == '=':
            self._calculate()
        else:
            if self.just_calculated:
                # Начинаем новое выражение с цифры или скобки
                if char in "0123456789.()":
                    self.expression.set(char)
                # Продолжаем вычисление с предыдущим результатом
                else:
                    self.expression.set(current_expression + char)
                self.just_calculated = False
            else:
                if current_expression in ["Ошибка ввода", "Деление на ноль"]:
                    self.expression.set(char)
                else:
                    self.expression.set(current_expression + char)

    def _calculate(self):
        current_expression = self.expression.get()
        # Заменяем визуальные символы на операторы для safe_eval
        eval_expression = current_expression.replace('×', '*').replace('÷', '/')

        result = safe_eval(eval_expression)

        # Убираем .0 для целых чисел
        if isinstance(result, float) and result.is_integer():
            result = int(result)

        self.expression.set(str(result))
        self.just_calculated = True


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
