import tkinter as tk
from calculator.safe_eval import safe_eval

class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Доступный калькулятор")
        self.configure(bg="#2E2E2E")
        self.expression = ""
        self.just_calculated = False
        self._create_widgets()
        self.bind("<Key>", self._on_key_press)
        self.focus_set()

    def _create_widgets(self):
        # Настройка стилей для виджетов
        style_options = {
            "font": ("TkDefaultFont", 24),
            "borderwidth": 0,
            "relief": "flat",
            "bg": "#2E2E2E",
            "fg": "#FFFFFF",
        }

        # Поле для вывода результата
        self.display_var = tk.StringVar()
        self.display = tk.Entry(
            self,
            textvariable=self.display_var,
            font=("TkDefaultFont", 48),
            bg="#3B3B3B",
            fg="#FFFFFF",
            justify="right",
            relief="flat",
            borderwidth=0,
            state="readonly",
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Настройка растягивания колонок и рядов
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)
        for i in range(1, 6):
            self.grid_rowconfigure(i, weight=1)

        # Определение раскладки кнопок
        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("C", 4, 0), ("0", 4, 1), ("=", 4, 2), ("+", 4, 3),
        ]

        # Создание кнопок
        for (text, row, col) in buttons:
            button = tk.Button(self, text=text, **style_options, command=lambda t=text: self._on_button_click(t))
            button.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            if text in "0123456789":
                button.config(bg="#505050")
            elif text == "C":
                button.config(bg="#D4D4D2", fg="#1C1C1E")
            elif text in "/*-+=":
                button.config(bg="#FF9500", fg="#FFFFFF")

    def _on_button_click(self, char):
        if self.just_calculated and char not in "/*-+":
            self.expression = ""
            self.just_calculated = False

        if char == "C":
            self.expression = ""
        elif char == "=":
            result = safe_eval(self.expression)
            if result is not None:
                # Убираем .0 для целых чисел
                if result == int(result):
                    self.expression = str(int(result))
                else:
                    self.expression = str(round(result, 8)) # Округляем до 8 знаков
            else:
                self.expression = "Ошибка"
            self.just_calculated = True
        else:
            self.expression += str(char)

        self.display_var.set(self.expression)

    def _on_key_press(self, event):
        key = event.keysym
        if key.isdigit() or key in "/*-+":
            self._on_button_click(key)
        elif key == "Return" or key == "KP_Enter":
            self._on_button_click("=")
        elif key == "Escape":
            self._on_button_click("C")
        elif key == "BackSpace":
            if self.expression and self.expression != "Ошибка":
                self.expression = self.expression[:-1]
                self.display_var.set(self.expression)


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
