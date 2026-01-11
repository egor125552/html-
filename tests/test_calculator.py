import unittest
import tkinter as tk
import sys
import os
from types import SimpleNamespace

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from calculator.main import CalculatorApp

class TestCalculatorApp(unittest.TestCase):

    def setUp(self):
        # Используем отдельный Tcl/Tk интерпретатор для каждого теста
        self.root = tk.Tk()
        self.root.withdraw() # Не отображаем окно
        self.app = CalculatorApp()

    def tearDown(self):
        self.app.destroy()
        self.root.destroy()

    def test_button_clicks(self):
        # Тестируем ввод "12+3="
        self.app._on_button_click("1")
        self.app._on_button_click("2")
        self.assertEqual(self.app.display_var.get(), "12")
        self.app._on_button_click("+")
        self.assertEqual(self.app.display_var.get(), "12+")
        self.app._on_button_click("3")
        self.assertEqual(self.app.display_var.get(), "12+3")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "15")

    def test_clear_button(self):
        self.app._on_button_click("5")
        self.app._on_button_click("*")
        self.app._on_button_click("2")
        self.app._on_button_click("C")
        self.assertEqual(self.app.display_var.get(), "")

    def test_error_state(self):
        self.app._on_button_click("1")
        self.app._on_button_click("/")
        self.app._on_button_click("0")
        self.app._on_button_click("=")
        self.assertEqual(self.app.display_var.get(), "Ошибка")
        # Проверяем, что после ошибки можно начать новый ввод
        self.app._on_button_click("5")
        self.assertEqual(self.app.display_var.get(), "5")

    def test_keyboard_input(self):
        # Эмулируем нажатие клавиш "5", "*", "4", "Enter"
        self.app._on_key_press(SimpleNamespace(keysym='5'))
        self.assertEqual(self.app.display_var.get(), "5")
        self.app._on_key_press(SimpleNamespace(keysym='*'))
        self.assertEqual(self.app.display_var.get(), "5*")
        self.app._on_key_press(SimpleNamespace(keysym='4'))
        self.assertEqual(self.app.display_var.get(), "5*4")
        self.app._on_key_press(SimpleNamespace(keysym='Return'))
        self.assertEqual(self.app.display_var.get(), "20")

    def test_backspace(self):
        self.app._on_button_click("1")
        self.app._on_button_click("2")
        self.app._on_button_click("3")
        self.app._on_key_press(SimpleNamespace(keysym='BackSpace'))
        self.assertEqual(self.app.display_var.get(), "12")

if __name__ == '__main__':
    unittest.main()
