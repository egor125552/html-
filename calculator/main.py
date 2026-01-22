import tkinter as tk
from .safe_eval import safe_eval

class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Доступный калькулятор")
        self.geometry("400x600")
        self.configure(bg="#2E2E2E")
        self.just_calculated = False
        self._create_widgets()
        self.bind_keys()

    def _create_widgets(self):
        # Дисплей
        self.display_var = tk.StringVar()
        self.display = tk.Entry(self, textvariable=self.display_var, font=("Arial", 36), bd=0, fg="#FFFFFF", bg="#3C3C3C", justify="right", insertbackground="#FFFFFF")
        self.display.grid(row=0, column=0, columnspan=4, ipady=20, sticky="nsew")

        # Кнопки
        buttons = [
            # Ряд 1
            ('C', 1, 0), ('()', 1, 1), ('^', 1, 2), ('←', 1, 3),
            # Ряд 2
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('÷', 2, 3),
            # Ряд 3
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('×', 3, 3),
            # Ряд 4
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('-', 4, 3),
            # Ряд 5
            ('0', 5, 0, 2), ('.', 5, 2), ('+', 5, 3),
            # Ряд 6
            ('=', 6, 0, 4)
        ]

        for (text, row, col, *span) in buttons:
            colspan = span[0] if span else 1
            self.add_button(text, row, col, colspan)

        # Конфигурация сетки
        for i in range(7):  # 7 рядов, включая дисплей и новый ряд для "="
            self.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

    def add_button(self, text, row, col, colspan):
        button = tk.Button(self, text=text, font=("Arial", 24), command=lambda t=text: self.on_button_click(t),
                           bg="#505050", fg="#FFFFFF", bd=0, activebackground="#6A6A6A", activeforeground="#FFFFFF")
        button.grid(row=row, column=col, columnspan=colspan, rowspan=1, sticky="nsew", padx=1, pady=1)

    def on_button_click(self, char):
        if char == 'C':
            self.display_var.set("")
        elif char == '←':
            self.backspace()
        elif char == '=':
            self.calculate()
        elif char == '()':
            self.add_parentheses()
        else:
            if self.just_calculated and char.isdigit():
                self.display_var.set("")
            self.just_calculated = False
            current_text = self.display_var.get()
            self.display_var.set(current_text + char)

    def calculate(self):
        expression = self.display_var.get().replace('×', '*').replace('÷', '/').replace('^', '**')
        result = safe_eval(expression)
        self.display_var.set(str(result))
        self.just_calculated = True

    def backspace(self):
        if self.just_calculated:
            self.display_var.set("")
            self.just_calculated = False
        else:
            self.display_var.set(self.display_var.get()[:-1])

    def add_parentheses(self):
        current_text = self.display_var.get()
        # Простая логика: если открывающих скобок больше, добавляем закрывающую, и наоборот
        if current_text.count('(') > current_text.count(')'):
            self.display_var.set(current_text + ')')
        else:
            self.display_var.set(current_text + '(')

    def bind_keys(self):
        self.bind("<Key>", self.handle_keypress)

    def handle_keypress(self, event):
        key = event.char
        if key.isdigit() or key in "+-*/.()^":
            self.on_button_click(key)
        elif event.keysym == "Return" or key == "=":
            self.on_button_click('=')
        elif event.keysym == "BackSpace":
            self.on_button_click('←')
        elif event.keysym.lower() == "c":
             self.on_button_click('C')


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
