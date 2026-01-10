import tkinter as tk
import ast
import operator as op

# Поддерживаемые операторы
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg,
    ast.UAdd: op.pos
}

def safe_eval(expr):
    """
    Безопасно вычисляет строковое выражение, используя AST.
    """
    try:
        node = ast.parse(expr, mode='eval').body
    except (SyntaxError, ValueError):
        raise ValueError("Некорректное выражение")

    def _eval(node):
        if isinstance(node, (ast.Constant, ast.Num)):  # ast.Num для старых версий Python
            return node.n
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in operators:
                raise ValueError(f"Неподдерживаемая операция: {type(node.op)}")
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in operators:
                raise ValueError(f"Неподдерживаемая операция: {type(node.op)}")
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(f"Неподдерживаемый узел: {type(node)}")

    return _eval(node)


class CalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Калькулятор")

        # --- Цвета для тёмной темы ---
        dark_bg = "#2E2E2E"
        light_fg = "#FFFFFF"
        button_bg = "#555555"
        display_bg = "#1E1E1E"

        master.configure(bg=dark_bg)
        self.just_calculated = False

        self.display_text = tk.StringVar()
        self.display = tk.Entry(master, width=15, font=('Arial', 28), borderwidth=0, relief="flat", justify='right', textvariable=self.display_text,
                                bg=display_bg, fg=light_fg, insertbackground=light_fg)
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=20, sticky="nsew")

        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
            ('C', 5, 0, 4)
        ]

        for button_spec in buttons:
            text, row, col = button_spec[0], button_spec[1], button_spec[2]
            col_span = button_spec[3] if len(button_spec) > 3 else 1

            button = tk.Button(master, text=text, font=('Arial', 18, 'bold'),
                             command=lambda t=text: self.on_button_click(t),
                             bg=button_bg, fg=light_fg, activebackground="#6a6a6a", activeforeground=light_fg, relief='flat', borderwidth=0)
            button.grid(row=row, column=col, columnspan=col_span, padx=2, pady=2, sticky="nsew")

        for i in range(4):
            master.grid_columnconfigure(i, weight=1)
        for i in range(1, 6):
            master.grid_rowconfigure(i, weight=1)

        master.bind('<KeyPress>', self.on_key_press)
        self.display.focus_set()

    def on_key_press(self, event):
        key_map = {
            "Return": "=", "KP_Enter": "=", "equal": "=",
            "Escape": "C", "c": "C", "C": "C",
            "BackSpace": "Backspace",
            "plus": "+", "KP_Add": "+",
            "minus": "-", "KP_Subtract": "-",
            "asterisk": "*", "KP_Multiply": "*",
            "slash": "/", "KP_Divide": "/",
            "period": ".", "KP_Decimal": "."
        }
        for i in range(10):
            key_map[str(i)] = str(i)
            key_map[f"KP_{i}"] = str(i)

        if event.keysym in key_map:
            char = key_map[event.keysym]
            if char == "Backspace":
                self.backspace()
            else:
                self.on_button_click(char)

    def backspace(self):
        if self.just_calculated:
            self.display_text.set("")
            self.just_calculated = False
        else:
            current_text = self.display_text.get()
            self.display_text.set(current_text[:-1])

    def on_button_click(self, char):
        current_text = self.display_text.get()

        if char == 'C':
            self.display_text.set("")
            self.just_calculated = False
        elif char == '=':
            self.calculate()
        else:
            if self.just_calculated:
                if char in '/*-+':
                    self.display_text.set(current_text + char)
                else:
                    self.display_text.set(char)
                self.just_calculated = False
            else:
                self.display_text.set(current_text + char)

    def calculate(self):
        try:
            expression = self.display_text.get()
            if not expression:
                return
            result = safe_eval(expression)
            if result == int(result):
                result = int(result)
            self.display_text.set(str(result))
        except Exception:
            self.display_text.set("Ошибка")
        finally:
            self.just_calculated = True

if __name__ == '__main__':
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
