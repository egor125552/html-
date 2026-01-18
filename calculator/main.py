import tkinter as tk
from .safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")
        master.configure(bg="#333")

        self.just_calculated = False

        # Стили
        self.display_font = ("Arial", 28)
        self.button_font = ("Arial", 24)
        self.bg_color = "#333"
        self.fg_color = "#fff"
        self.button_bg = "#555"
        self.button_active_bg = "#777"

        self.display = tk.Entry(
            master,
            width=25,
            font=self.display_font,
            borderwidth=5,
            relief="sunken",
            justify="right",
            bg="#444",
            fg=self.fg_color
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=20)
        self.display.focus_set() # Установить фокус на поле ввода

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
            ('C', 5, 0, 2), ('←', 5, 2, 2) # Добавлена кнопка Backspace
        ]

        for (text, row, col, *span) in buttons:
            colspan = span[0] if span else 1
            button = tk.Button(
                master,
                text=text,
                font=self.button_font,
                bg=self.button_bg,
                fg=self.fg_color,
                activebackground=self.button_active_bg,
                activeforeground=self.fg_color,
                relief="raised",
                borderwidth=3,
                command=lambda t=text: self.on_button_click(t)
            )
            button.grid(row=row, column=col, columnspan=colspan, sticky="nsew", padx=5, pady=5)

        for i in range(1, 6):
            master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            master.grid_columnconfigure(i, weight=1)

        # Привязка клавиш
        master.bind("<Key>", self.handle_keypress)

    def handle_keypress(self, event):
        if event.keysym in "0123456789.+-*/":
            self.on_button_click(event.keysym)
        elif event.keysym == "Return" or event.keysym == "KP_Enter":
            self.calculate()
        elif event.keysym == "Escape":
            self.clear_display()
        elif event.keysym == "BackSpace":
            self.backspace()

    def on_button_click(self, char):
        if char == 'C':
            self.clear_display()
        elif char == '=':
            self.calculate()
        elif char == '←':
            self.backspace()
        else:
            if self.just_calculated:
                self.display.delete(0, tk.END)
                self.just_calculated = False
            self.display.insert(tk.END, char)

    def calculate(self):
        try:
            expression = self.display.get()
            result = safe_eval(expression)
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
            self.just_calculated = True
        except Exception:
            self.display.delete(0, tk.END)
            self.display.insert(0, "Ошибка")
            self.just_calculated = True

    def clear_display(self):
        self.display.delete(0, tk.END)

    def backspace(self):
        self.display.delete(len(self.display.get()) - 1, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
