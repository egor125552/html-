from calculator.safe_eval import safe_eval
import tkinter as tk

class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Доступный калькулятор")
        self.geometry("400x600")
        self.configure(bg="#2E2E2E")
        self.just_calculated = False

        self.display = tk.Entry(self, font=("Arial", 32), borderwidth=0, relief="flat", justify="right", bg="#1C1C1C", fg="white")
        self.display.pack(padx=10, pady=20, fill="x", ipady=10)

        self.create_buttons()
        self.bind_keys()

    def bind_keys(self):
        self.bind('<Key>', self.handle_keypress)

    def handle_keypress(self, event):
        key = event.char
        if key in '0123456789.':
            self.on_button_click(key)
        elif key in '/*-+':
            self.on_button_click(key)
        elif key == '\r' or key == '=': # Enter key
            self.calculate()
        elif key == '\x08': # Backspace key
            self.backspace()
        elif key.lower() == 'c':
            self.clear_display()

    def backspace(self):
        if self.just_calculated:
            self.display.delete(0, tk.END)
            self.just_calculated = False
            return
        current_text = self.display.get()
        if current_text:
            self.display.delete(len(current_text) - 1, tk.END)

    def create_buttons(self):
        button_frame = tk.Frame(self, bg="#2E2E2E")
        button_frame.pack(fill="both", expand=True, padx=5, pady=5)

        buttons = [
            ('C', 1, 0), ('←', 1, 1), ('%', 1, 2), ('/', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('*', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('-', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('+', 4, 3),
            ('0', 5, 0, 2), ('.', 5, 2), ('=', 5, 3)
        ]

        for (text, row, col, *span) in buttons:
            style = {
                "font": ("Arial", 22, "bold"),
                "borderwidth": 0,
                "relief": "flat",
                "fg": "white",
                "activebackground": "#757575",
                "activeforeground": "white"
            }

            if text in '0123456789.':
                style["bg"] = "#505050"
            elif text in '/*-+=':
                style["bg"] = "#FF9500" # Оранжевый для операторов
            else: # Для 'C' и других
                style["bg"] = "#D4D4D2"
                style["fg"] = "black"
                style["activebackground"] = "#EAEAEA"
                style["activeforeground"] = "black"

            action = None
            if text == 'C':
                action = self.clear_display
            elif text == '=':
                action = self.calculate
            elif text == '←':
                action = self.backspace
            else:
                action = lambda t=text: self.on_button_click(t)

            button = tk.Button(button_frame, text=text, **style, command=action)

            columnspan = span[0] if span else 1
            button.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=2, pady=2)

        for i in range(5):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)

    def on_button_click(self, char):
        is_operator = char in '/*-+'
        if self.just_calculated:
            if is_operator:
                self.just_calculated = False
            else:
                self.display.delete(0, tk.END)
                self.just_calculated = False
        self.display.insert(tk.END, char)

    def clear_display(self):
        self.display.delete(0, tk.END)

    def calculate(self):
        expression = self.display.get()
        try:
            result = safe_eval(expression)
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
            self.just_calculated = True
        except Exception as e:
            self.display.delete(0, tk.END)
            self.display.insert(0, "Ошибка")
            self.just_calculated = True


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
