import tkinter as tk
from tkinter import font
from .safe_eval import safe_eval

class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Accessible Calculator")
        self.geometry("400x600")

        self.expression = ""
        self.just_calculated = False

        self._configure_styles()
        self._create_widgets()
        self._bind_keys()

    def _configure_styles(self):
        self.configure(bg="#2E2E2E")
        self.option_add("*TButton*foreground", "white")
        self.option_add("*TButton*background", "#505050")

        self.display_font = font.Font(family="TkDefaultFont", size=36, weight="bold")
        self.button_font = font.Font(family="TkDefaultFont", size=18)

    def _create_widgets(self):
        # Display Screen
        self.display_var = tk.StringVar()
        display_frame = tk.Frame(self, bg="#2E2E2E")
        display_frame.pack(expand=True, fill="both", padx=10, pady=20)

        self.display_label = tk.Label(
            display_frame,
            textvariable=self.display_var,
            font=self.display_font,
            anchor="e",
            bg="#2E2E2E",
            fg="white",
            padx=10,
            pady=10
        )
        self.display_label.pack(expand=True, fill="both")

        # Buttons Frame
        button_frame = tk.Frame(self, bg="#2E2E2E")
        button_frame.pack(expand=True, fill="both", padx=5, pady=5)

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('+', 4, 3),
            ('C', 5, 0), ('=', 5, 2, 2) # Span 2 columns
        ]

        for (text, row, col, *span) in buttons:
            self._create_button(text, row, col, span, button_frame)

        # Configure grid weights
        for i in range(5):
            button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)

    def _create_button(self, text, row, col, span, parent):
        btn = tk.Button(
            parent,
            text=text,
            font=self.button_font,
            command=lambda t=text: self.on_button_click(t),
            bg="#505050",
            fg="white",
            relief="flat",
            padx=20,
            pady=20
        )

        columnspan = span[0] if span else 1
        btn.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=2, pady=2)

        if text == '=':
            btn.configure(bg="#FF9500") # Orange for equals
        elif text in '/*-+':
             btn.configure(bg="#707070") # Gray for operators
        elif text == 'C':
            btn.configure(bg="#D4D4D2", fg="black") # Light gray for Clear


    def on_button_click(self, char):
        if char == 'C':
            self.clear_display()
        elif char == '=':
            self.calculate()
        else:
            if self.just_calculated:
                # If a number or dot is pressed after a calculation, start a new expression
                if char in "0123456789.":
                    self.expression = ""
                self.just_calculated = False

            self.expression += str(char)
            self.display_var.set(self.expression)

    def clear_display(self):
        self.expression = ""
        self.display_var.set("")
        self.just_calculated = False

    def calculate(self):
        if not self.expression:
            return
        try:
            result = safe_eval(self.expression)
            # Check if the result is an integer, and format it without .0 if so
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            self.display_var.set(str(result))
            self.expression = str(result)
            self.just_calculated = True
        except (ValueError, ZeroDivisionError) as e:
            self.display_var.set("Error")
            self.expression = ""
            self.just_calculated = True

    def _bind_keys(self):
        self.bind('<Return>', lambda event: self.calculate())
        self.bind('<Escape>', lambda event: self.clear_display())
        self.bind('<BackSpace>', self.handle_backspace)

        for key in "0123456789./*-+":
            self.bind(key, lambda event, k=key: self.on_button_click(k))

    def handle_backspace(self, event=None):
        if self.just_calculated:
            self.clear_display()
            return

        self.expression = self.expression[:-1]
        self.display_var.set(self.expression)


if __name__ == "__main__":
    # To run this application, navigate to the root directory of the project
    # and run the following command:
    # python3 -m calculator.main
    app = CalculatorApp()
    app.mainloop()
