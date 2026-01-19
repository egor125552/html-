import tkinter as tk
from calculator.safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Доступный калькулятор")
        master.configure(bg="#2E2E2E")
        master.geometry("400x600")

        self.display_var = tk.StringVar()
        self.just_calculated = False # Флаг для отслеживания состояния после вычисления
        self.create_widgets()
        self.bind_keys()

    def bind_keys(self):
        """Привязывает события клавиатуры к функциям калькулятора."""
        self.master.bind("<Key>", self.handle_keypress)

    def handle_keypress(self, event):
        """Обрабатывает нажатия клавиш."""
        char = event.char
        keysym = event.keysym

        if char in "0123456789.+-*/":
            self.on_button_click(char)
        elif keysym == "Return" or char == "=":
            self.on_button_click("=")
        elif keysym == "BackSpace":
            self.on_button_click("←")
        elif keysym == "Escape":
            self.on_button_click("C")
        elif char == "c" or char == "C":
             self.on_button_click("C")

    def create_widgets(self):
        # Экран для вывода чисел
        display_entry = tk.Entry(
            self.master,
            textvariable=self.display_var,
            font=("Arial", 36),
            fg="#FFFFFF",
            bg="#3C3C3C",
            bd=0,
            justify="right",
            insertbackground="#FFFFFF" # Цвет курсора
        )
        display_entry.grid(row=0, column=0, columnspan=4, ipady=20, sticky="nsew")
        display_entry.focus_set() # Устанавливаем фокус на поле ввода

        # Определение кнопок
        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("=", 4, 2), ("+", 4, 3),
            ("C", 5, 0, 2), ("←", 5, 2, 2) # Очистить и стереть
        ]

        # Создание и размещение кнопок
        for (text, row, col, *span) in buttons:
            colspan = span[0] if span else 1
            button = tk.Button(
                self.master,
                text=text,
                font=("Arial", 24, "bold"),
                fg="#FFFFFF",
                bg="#505050",
                activebackground="#6A6A6A",
                activeforeground="#FFFFFF",
                bd=0,
                relief="flat",
                command=lambda t=text: self.on_button_click(t)
            )
            button.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=2, pady=2)

        # Настройка растягивания строк и столбцов
        for i in range(6):
            self.master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.master.grid_columnconfigure(i, weight=1)

    def on_button_click(self, char):
        current_text = self.display_var.get()

        if self.just_calculated and char not in "+-*/":
             # Если было вычисление и нажимается не оператор, начинаем новый ввод
            current_text = ""
        self.just_calculated = False

        if char == "=":
            try:
                # Заменяем символ умножения и деления для safe_eval
                expression = current_text.replace("×", "*").replace("÷", "/")
                result = safe_eval(expression)
                # Округляем до 10 знаков после запятой, если это float
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                elif isinstance(result, float):
                    result = round(result, 10)
                self.display_var.set(str(result))
                self.just_calculated = True
            except Exception as e:
                self.display_var.set("Ошибка")
                self.just_calculated = True
        elif char == "C":
            self.display_var.set("")
        elif char == "←":
            self.display_var.set(current_text[:-1])
        else:
            # Заменяем стандартные символы на более наглядные
            display_char = char
            if char == '*':
                display_char = '×'
            elif char == '/':
                display_char = '÷'
            self.display_var.set(current_text + display_char)


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
