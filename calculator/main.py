import tkinter as tk
from tkinter import font
try:
    # Для запуска как пакет (python -m calculator.main)
    from .safe_eval import safe_eval
except ImportError:
    # Для запуска как скрипт (python calculator/main.py)
    from safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Доступный Калькулятор")
        master.geometry("320x480")
        master.configure(bg="#2E2E2E")
        self.just_calculated = False

        # Настройка шрифтов
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=18)
        self.entry_font = font.Font(family="Arial", size=36, weight="bold")

        # Поле для вывода
        self.display = tk.Entry(
            master,
            font=self.entry_font,
            bg="#3C3C3C",
            fg="#FFFFFF",
            justify="right",
            bd=0,
            insertbackground="#FFFFFF" # Курсор
        )
        self.display.pack(fill="x", padx=10, pady=20, ipady=10)

        # Рамка для кнопок
        button_frame = tk.Frame(master, bg="#2E2E2E")
        button_frame.pack(fill="both", expand=True)

        # Определение кнопок
        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("=", 4, 2), ("+", 4, 3),
            ("C", 5, 0, 2) # Кнопка C занимает 2 колонки
        ]

        # Создание и размещение кнопок
        for (text, row, col, *span) in buttons:
            self.create_button(button_frame, text, row, col, span[0] if span else 1)

        # Настройка сетки
        for i in range(5):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)

        # Привязка событий клавиатуры
        master.bind("<KeyPress>", self.on_key_press)

    def on_key_press(self, event):
        """Обрабатывает нажатия клавиш."""
        key = event.keysym

        if key.isdigit() or key in ".-+/*":
            self.on_button_press(key)
        elif key == "Return" or key == "KP_Enter": # Enter на основной и цифровой клавиатуре
            self.on_button_press("=")
        elif key == "Escape":
            self.on_button_press("C")
        elif key == "BackSpace":
            current_text = self.display.get()
            if current_text:
                self.display.delete(len(current_text) - 1, "end")

    def create_button(self, parent, text, row, col, colspan):
        # Стиль кнопок
        button_style = {
            "font": self.default_font,
            "bg": "#505050",
            "fg": "#FFFFFF",
            "bd": 0,
            "relief": "flat",
            "activebackground": "#6A6A6A",
            "activeforeground": "#FFFFFF"
        }

        if text.isdigit() or text == ".":
            pass # Стандартный стиль для цифр
        elif text == "=":
            button_style["bg"] = "#FF9500" # Оранжевый для =
        else:
            button_style["bg"] = "#333333" # Темнее для операторов

        btn = tk.Button(
            parent,
            text=text,
            **button_style,
            command=lambda t=text: self.on_button_press(t)
        )
        btn.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=5, pady=5)
        return btn

    def on_button_press(self, char):
        """Обрабатывает нажатия кнопок калькулятора."""
        if char == "C":
            self.display.delete(0, "end")
        elif char == "=":
            try:
                expr = self.display.get()
                result = safe_eval(expr)
                self.display.delete(0, "end")
                # Убираем .0 для целых чисел
                if result == int(result):
                    self.display.insert(0, str(int(result)))
                else:
                    self.display.insert(0, str(round(result, 10)))
                self.just_calculated = True
            except (ValueError, ZeroDivisionError) as e:
                self.display.delete(0, "end")
                self.display.insert(0, "Ошибка")
                self.just_calculated = True
        else:
            # Если только что было вычисление, очищаем поле перед вводом нового числа
            if self.just_calculated:
                # Кроме случаев, когда вводится оператор
                if char not in "+-*/":
                    self.display.delete(0, "end")
                self.just_calculated = False

            self.display.insert("end", char)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
