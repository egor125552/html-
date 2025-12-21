import tkinter as tk
import ast
import operator as op

# Supported operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
}

def safe_eval(expr):
    """
    Safely evaluate a mathematical expression string.
    """
    try:
        node = ast.parse(expr, mode='eval').body
    except (SyntaxError, TypeError):
        raise ValueError("Malformed expression")

    def _eval(node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            if type(node.op) not in operators:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
             if type(node.op) not in operators:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
             return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

    return _eval(node)


# Цветовая схема для высокой контрастности (темная тема)
BG_COLOR = "#1e1e1e"
DISPLAY_BG_COLOR = "#2e2e2e"
BUTTON_BG_COLOR = "#3e3e3e"
TEXT_COLOR = "#ffffff"
OPERATOR_BG_COLOR = "#ff9f0a"

class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Доступный Калькулятор")
        self.geometry("400x600")
        self.configure(bg=BG_COLOR)

        self.expression = ""
        self.display_text = tk.StringVar()
        self.just_calculated = False # Flag to track if the last action was a calculation

        self.display = tk.Entry(self, font=("Arial", 48), relief=tk.FLAT, justify="right", bd=10,
                                textvariable=self.display_text, bg=DISPLAY_BG_COLOR, fg=TEXT_COLOR,
                                insertbackground=TEXT_COLOR)
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=20)

        # 2D list for button layout
        buttons = [
            ['(', ')', 'C', '/'],
            ['7', '8', '9', '*'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['0', '.', '=']
        ]

        row_val = 1
        for row in buttons:
            col_val = 0
            for button_text in row:
                if button_text == '0':
                    # '0' button spans 2 columns
                    self.create_button(button_text).grid(row=row_val, column=col_val, columnspan=2, sticky="nsew", padx=5, pady=5)
                    col_val += 2
                else:
                    self.create_button(button_text).grid(row=row_val, column=col_val, sticky="nsew", padx=5, pady=5)
                    col_val += 1
            row_val += 1


        # Configure row and column weights
        self.grid_rowconfigure(0, weight=2) # Display row gets more weight
        for i in range(1, 6): # Button rows
            self.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

        self.bind("<Key>", self.on_key_press)
        self.display.focus_set()

    def create_button(self, text):
        bg_color = OPERATOR_BG_COLOR if text in "/*-+=C()" else BUTTON_BG_COLOR

        return tk.Button(self, text=text, font=("Arial", 28, "bold"), relief=tk.FLAT, bg=bg_color, fg=TEXT_COLOR,
                         command=lambda: self.on_button_click(text))

    def on_button_click(self, char):
        if self.just_calculated and char not in "/*-+=()":
            self.expression = ""

        self.just_calculated = False

        if char == 'C' or char == 'c':
            self.expression = ""
            self.display_text.set("")
        elif char == '=':
            if not self.expression:
                return
            try:
                # Use the safe_eval function
                result = str(safe_eval(self.expression))
                self.display_text.set(result)
                self.expression = result
                self.just_calculated = True # Set the flag
            # Catch specific errors
            except (ValueError, TypeError, ZeroDivisionError):
                self.display_text.set("Ошибка")
                self.expression = ""
        else:
            self.expression += str(char)
            self.display_text.set(self.expression)

    def on_key_press(self, event):
        key = event.char
        if key in "0123456789./*-+()":
            self.on_button_click(key)
        elif event.keysym == "Return" or key == "=":
            self.on_button_click("=")
        elif event.keysym == "BackSpace":
            if self.just_calculated:
                self.expression = ""
            else:
                self.expression = self.expression[:-1]
            self.display_text.set(self.expression)
            self.just_calculated = False
        elif event.keysym == "Escape" or key.lower() == "c":
            self.on_button_click("C")


if __name__ == "__main__":
    app = Calculator()
    app.mainloop()
