import tkinter as tk
from .safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")
        master.geometry("400x600")
        master.resizable(False, False)

        # Цвета для темной темы
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.button_bg = "#505050"
        self.button_fg = "#FFFFFF"
        self.button_active_bg = "#6A6A6A"
        self.display_bg = "#3C3C3C"

        master.configure(bg=self.bg_color)

        # Дисплей
        self.display_var = tk.StringVar()
        self.display = tk.Entry(master, textvariable=self.display_var, font=("Arial", 36), bd=0, relief=tk.FLAT, justify='right', bg=self.display_bg, fg=self.fg_color)
        self.display.pack(pady=20, padx=10, fill='x')
        self.display_var.set("0")
        self.just_calculated = False

        master.bind("<Key>", self.handle_keypress)

        # Рамка для кнопок
        self.button_frame = tk.Frame(master, bg=self.bg_color)
        self.button_frame.pack(fill='both', expand=True)

        # Определение кнопок
        buttons = [
            ('C', 0, 0), ('(', 0, 1), (')', 0, 2), ('←', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('÷', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('×', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3)
        ]

        # Создание и размещение кнопок
        for (text, row, col) in buttons:
            button = tk.Button(self.button_frame, text=text, font=("Arial", 18),
                               fg=self.button_fg, bg=self.button_bg,
                               activeforeground=self.fg_color, activebackground=self.button_active_bg,
                               bd=0, relief=tk.FLAT, padx=20, pady=20,
                               command=lambda t=text: self.on_button_click(t))
            button.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)

        # Настройка растягивания сетки
        for i in range(5):
            self.button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.button_frame.grid_columnconfigure(i, weight=1)

    def on_button_click(self, char):
        current_text = self.display_var.get()

        # Если была ошибка, очищаем поле при любом вводе, кроме 'C' и '←'
        if current_text == "Ошибка" and char not in ['C', '←']:
            current_text = "0"
            self.display_var.set(current_text)

        if char == 'C':
            self.display_var.set("0")
            return

        if char == '←':
            if len(current_text) > 1:
                self.display_var.set(current_text[:-1])
            else:
                self.display_var.set("0")
            return

        if char == '=':
            expression = current_text.replace("×", "*").replace("÷", "/")
            result = safe_eval(expression)
            self.display_var.set(str(result))
            self.just_calculated = True
            return

        # Если только что было вычисление, смотрим, что нажато дальше
        if self.just_calculated:
            if char in "0123456789.":
                # Нажата цифра - начинаем новый ввод
                self.display_var.set(char)
            else:
                # Нажат оператор - продолжаем вычисление
                self.display_var.set(current_text + char)
            self.just_calculated = False
            return

        # Стандартная логика
        if current_text == "0" and char != '.':
            self.display_var.set(char)
        else:
            self.display_var.set(current_text + char)

    def handle_keypress(self, event):
        key = event.keysym
        char = event.char

        if key == "Return" or char == '=':
            self.on_button_click('=')
        elif key == "BackSpace":
            self.on_button_click('←')
        elif key == "Escape":
            self.on_button_click('C')
        elif char in "0123456789.+-*/()":
            if char == '*':
                self.on_button_click('×')
            elif char == '/':
                self.on_button_click('÷')
            else:
                self.on_button_click(char)


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
