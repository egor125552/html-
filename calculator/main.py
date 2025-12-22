import tkinter as tk
import ast
import operator as op

class CalculatorLogic:
    def __init__(self):
        self.expression = ""
        self.just_calculated = False
        self._operators = {
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
            ast.Div: op.truediv, ast.Pow: op.pow
        }

    def process_input(self, text):
        if self.just_calculated and text not in "+-*/()**=":
            self.expression = ""
        self.just_calculated = False

        if text == 'C':
            self.expression = ""
        elif text == '<-':
            self.expression = self.expression[:-1]
        elif text == '=':
            if self.expression:
                self._calculate()
        else:
            self.expression += text

    def get_expression(self):
        return self.expression

    def _calculate(self):
        self.just_calculated = True
        try:
            parsed_expr = ast.parse(self.expression, mode='eval').body
            result = self._safe_eval(parsed_expr)
            self.expression = str(result)
        except (TypeError, SyntaxError, ZeroDivisionError, KeyError, ValueError, NameError):
            self.expression = "Error"

    def _safe_eval(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return self._operators[type(node.op)](self._safe_eval(node.left), self._safe_eval(node.right))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._safe_eval(node.operand)
        else:
            raise TypeError(node)

class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.geometry("400x700")
        self.logic = CalculatorLogic()
        self._create_widgets()
        self._bind_keyboard()

    def _create_widgets(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)
        self.grid_columnconfigure(0, weight=1)

        self.display = tk.Entry(self, font=("Helvetica", 24, "bold"), borderwidth=5, relief="ridge", justify='right', state='readonly')
        self.display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=1, column=0, sticky="nsew")

        buttons = [
            ('C', 0, 0, 2), ('<-', 0, 2, 2),
            ('(', 1, 0), (')', 1, 1), ('**', 1, 2), ('/', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('*', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('-', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('+', 4, 3),
            ('0', 5, 0, 2), ('.', 5, 2), ('=', 5, 3)
        ]

        for i in range(6):
            buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1)

        for (text, row, col, *span) in buttons:
            colspan = span[0] if len(span) > 0 else 1
            button = tk.Button(
                buttons_frame,
                text=text,
                font=("Helvetica", 18, "bold"),
                command=lambda t=text: self._on_button_click(t)
            )
            button.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")

    def _on_button_click(self, text):
        self.logic.process_input(text)
        self._update_display()

    def _update_display(self):
        expression = self.logic.get_expression()
        self.display.config(state='normal')
        self.display.delete(0, tk.END)
        self.display.insert(0, expression)
        self.display.config(state='readonly')

    def _bind_keyboard(self):
        self.bind("<Key>", self._on_key_press)

    def _on_key_press(self, event):
        char = event.char
        if char in "0123456789.+-*/()":
            self._on_button_click(char)
        elif event.keysym == "Return" or char == "=":
            self._on_button_click("=")
        elif event.keysym == "BackSpace":
            self._on_button_click("<-")
        elif event.keysym == "Escape":
            self._on_button_click("C")


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()
