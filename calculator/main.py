import tkinter as tk
from tkinter import font as tkfont
import re
# Примечание: импорт .safe_eval вызовет ошибку, если запускать файл напрямую.
# Этот файл предназначен для запуска как модуль: python3 -m calculator.main
from .safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Доступный калькулятор")
        self.root.geometry("400x600")
        self.root.configure(bg="#2e2e2e")

        # Настройка стилей
        self.large_font = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.display_font = tkfont.Font(family="Helvetica", size=36, weight="bold")

        # Переменная для хранения выражения
        self.expression = tk.StringVar()
        self.expression.set("")
        self.just_calculated = False

        # Создание виджетов
        self._create_display()
        self._create_buttons()
        self._bind_keys()

    def _bind_keys(self):
        """Привязывает события клавиатуры к функциям калькулятора."""
        self.root.bind("<Key>", self._handle_keypress)
        # Для клавиш, которые могут не иметь `char`
        self.root.bind("<Return>", lambda event: self._on_button_click('='))
        self.root.bind("<BackSpace>", lambda event: self._backspace())
        self.root.bind("<Escape>", lambda event: self._on_button_click('C'))

    def _handle_keypress(self, event):
        """Обрабатывает общие нажатия клавиш."""
        char = event.char
        if char in "0123456789.":
            self._on_button_click(char)
        elif char in "+-":
            self._on_button_click(char)
        elif char == '*':
            self._on_button_click('×')
        elif char == '/':
            self._on_button_click('÷')
        elif char in "()":
            self._on_button_click('()')

    def _backspace(self):
        """Удаляет последний символ из выражения."""
        current_expression = self.expression.get()
        if current_expression:
            self.expression.set(current_expression[:-1])

    def _create_display(self):
        """Создает дисплей калькулятора."""
        display_frame = tk.Frame(self.root, bg="#2e2e2e")
        display_frame.pack(expand=True, fill="both", padx=10, pady=10)

        display = tk.Entry(
            display_frame,
            textvariable=self.expression,
            font=self.display_font,
            fg="#FFFFFF",
            bg="#3c3c3c",
            bd=0,
            justify="right",
            state="readonly",
        )
        display.pack(expand=True, fill="both")

    def _create_buttons(self):
        """Создает кнопки калькулятора."""
        buttons_frame = tk.Frame(self.root, bg="#2e2e2e")
        buttons_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # Определение сетки кнопок: (текст, ряд, колонка, columnspan)
        buttons = [
            ('C', 0, 0), ('()', 0, 1), ('%', 0, 2), ('÷', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('×', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('+/-', 4, 0), ('0', 4, 1), ('.', 4, 2), ('=', 4, 3),
        ]

        for i in range(5):
            buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1)

        for (text, row, col, *span) in buttons:
            self._create_button(text, row, col, span[0] if span else 1, buttons_frame)

    def _create_button(self, text, row, col, colspan, parent):
        """Создает отдельную кнопку."""
        # Назначение цветов в зависимости от типа кнопки
        if text.isdigit() or text == '.':
            bg_color, fg_color = "#505050", "#FFFFFF"
        elif text in ['÷', '×', '-', '+', '=']:
            bg_color, fg_color = "#FF9500", "#FFFFFF"
        else:
            bg_color, fg_color = "#3c3c3c", "#FFFFFF"

        button = tk.Button(
            parent,
            text=text,
            font=self.large_font,
            fg=fg_color,
            bg=bg_color,
            bd=0,
            relief="flat",
            command=lambda t=text: self._on_button_click(t)
        )
        button.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=2, pady=2)
        return button

    def _on_button_click(self, char):
        """Обрабатывает нажатия кнопок."""
        current_expression = self.expression.get()

        if char == 'C':
            self.expression.set("")
            return
        if char == '=':
            self._calculate_result()
            return
        if char == '+/-':
            self._toggle_sign()
            return
        if char == '%':
            self._calculate_percentage()
            return
        if char == '()':
            self._handle_parentheses()
            return

        if self.just_calculated:
            if char.isdigit() or char == '.':
                self.expression.set(self._map_operator(char))
            else:
                self.expression.set(current_expression + self._map_operator(char))
            self.just_calculated = False
        else:
            self.expression.set(current_expression + self._map_operator(char))

    def _map_operator(self, char):
        """Сопоставляет символы дисплея с внутренними символами."""
        if char == '×': return '*'
        if char == '÷': return '/'
        return char

    def _calculate_result(self):
        """Вычисляет и отображает результат."""
        current_expression = self.expression.get()
        if not current_expression:
            return
        try:
            result = safe_eval(current_expression)
            self.expression.set(str(result))
            self.just_calculated = True
        except Exception:
            self.expression.set("Error")
            self.just_calculated = True

    def _toggle_sign(self):
        """Переключает знак последнего числа в выражении."""
        expression = self.expression.get()
        # Паттерн для поиска последнего числа (может быть просто числом или числом в скобках)
        match = re.search(r'([+\-*/])?((?:\(-?[\d\.]+\))|[\d\.]+)$', expression)

        if not match: return

        operator = match.group(1) or ""
        number_str = match.group(2)
        start_pos = match.start(2)

        try:
            # Используем safe_eval для правильной обработки "(...)"
            value = safe_eval(number_str)
            new_value = -value

            # Оборачиваем в скобки, чтобы избежать неоднозначности типа 5--2
            new_number_str = f"({new_value})" if new_value < 0 and operator else str(new_value)

            self.expression.set(expression[:start_pos] + new_number_str)
        except Exception:
            # Если последняя часть не является валидным числом, ничего не делаем
            return

    def _calculate_percentage(self):
        """Вычисляет процент от последнего числа."""
        expression = self.expression.get()
        # Паттерн для поиска последнего числа, аналогично _toggle_sign
        match = re.search(r'((?:\(-?[\d\.]+\))|[\d\.]+)$', expression)

        if not match: return

        number_str = match.group(1)
        start_pos = match.start(1)

        try:
            value = safe_eval(number_str)
            new_value = value / 100.0
            self.expression.set(expression[:start_pos] + str(new_value))
            self.just_calculated = True
        except Exception:
            return

    def _handle_parentheses(self):
        """Добавляет открывающую или закрывающую скобку."""
        current = self.expression.get()
        open_parens = current.count('(')
        close_parens = current.count(')')
        last_char = current[-1] if current else ''

        if last_char in '0123456789.)' and open_parens > close_parens:
            self.expression.set(current + ')')
        else:
            self.expression.set(current + '(')

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
