import tkinter as tk
from tkinter import font
from .safe_eval import safe_eval

class CalculatorApp:
    def __init__(self, master):
        self.just_calculated = False
        self.master = master
        master.title("Калькулятор")
        master.geometry("400x600")
        master.resizable(False, False)

        # Configure dark theme
        master.configure(bg="#2E2E2E")
        self.master.option_add("*background", "#2E2E2E")
        self.master.option_add("*foreground", "white")
        self.master.option_add("*font", "Helvetica 18")
        self.master.option_add("*borderwidth", "0")

        # Define fonts
        self.display_font = font.Font(family="Helvetica", size=48, weight="bold")
        self.button_font = font.Font(family="Helvetica", size=18)

        # Display
        self.display_var = tk.StringVar()
        self.display_var.set("0")

        display_frame = tk.Frame(master, bg="#2E2E2E")
        display_frame.pack(pady=20, padx=10, fill="x")

        self.display = tk.Entry(
            display_frame,
            textvariable=self.display_var,
            font=self.display_font,
            bg="#2E2E2E",
            fg="white",
            justify="right",
            bd=0,
            insertbackground="white", # cursor color
            state="readonly"
        )
        self.display.pack(fill="x", ipady=10)

        # Button Frame
        button_frame = tk.Frame(master, bg="#2E2E2E")
        button_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_buttons(button_frame)

        # Bind keyboard
        self.master.bind("<Key>", self.handle_keypress)

    def handle_keypress(self, event):
        char = event.char
        keysym = event.keysym

        if keysym in ('Return', 'KP_Enter'):
            self.on_button_click('=')
        elif keysym == 'BackSpace':
            self.on_button_click('←')
        elif keysym == 'Escape':
            self.on_button_click('C')
        elif char in "0123456789.+-*/":
            self.on_button_click(char)
        elif char in "cC":
             self.on_button_click('C')

    def create_buttons(self, parent):
        buttons = [
            ('C', 1, 0), ('←', 1, 1), ('÷', 1, 2), ('×', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('-', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('+', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2),
            ('0', 5, 0, 2), ('.', 5, 2)
        ]

        for (text, row, col, *spans) in buttons:
            colspan = spans[0] if spans else 1

            # Button colors
            bg_color = "#4F4F4F"
            if text in "/*-+=":
                bg_color = "#FF9500" # Orange for operators
            elif text in "C←":
                bg_color = "#D4D4D2" # Light gray for top buttons

            fg_color = "white"
            if text in "C←":
                fg_color = "black"

            btn = tk.Button(
                parent,
                text=text,
                font=self.button_font,
                bg=bg_color,
                fg=fg_color,
                activebackground="#6E6E6E",
                activeforeground="white",
                command=lambda t=text: self.on_button_click(t)
            )
            btn.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")

        # Equals button (spans two rows)
        eq_btn = tk.Button(
            parent,
            text="=",
            font=self.button_font,
            bg="#FF9500",
            fg="white",
            activebackground="#6E6E6E",
            activeforeground="white",
            command=lambda t="=": self.on_button_click(t)
        )
        eq_btn.grid(row=4, column=3, rowspan=2, padx=5, pady=5, sticky="nsew")

        for i in range(4):
            parent.grid_columnconfigure(i, weight=1)
        for i in range(1, 6): # Rows 1 to 5
            parent.grid_rowconfigure(i, weight=1)

    def on_button_click(self, char):
        current_text = self.display_var.get()

        if char == 'C':
            self.display_var.set('0')
            self.just_calculated = False
        elif char == '←':
            if self.just_calculated:
                self.display_var.set('0')
            elif len(current_text) > 1:
                self.display_var.set(current_text[:-1])
            else:
                self.display_var.set('0')
            self.just_calculated = False
        elif char == '=':
            if not current_text or self.just_calculated:
                return

            try:
                # Replace visual operators with Python operators
                expression = current_text.replace('×', '*').replace('÷', '/')
                result = safe_eval(expression)

                # Format result
                if result == int(result):
                    self.display_var.set(str(int(result)))
                else:
                    self.display_var.set(f"{result:.10f}".rstrip('0').rstrip('.'))

                self.just_calculated = True

            except (ValueError, TypeError, ZeroDivisionError):
                self.display_var.set("Ошибка")
                self.just_calculated = True

        elif char in "×÷+-":
             # If last char is an operator, replace it
            if current_text and current_text[-1] in "×÷+-":
                self.display_var.set(current_text[:-1] + char)
            else:
                self.display_var.set(current_text + char)
            self.just_calculated = False
        else: # Digits and dot
            if current_text == '0' or self.just_calculated or current_text == "Ошибка":
                self.display_var.set(char)
            else:
                self.display_var.set(current_text + char)
            self.just_calculated = False

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
