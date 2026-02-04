# Accessible Scientific Calculator (Python)

A super accessible, high-contrast scientific calculator built with Python and Tkinter. Optimized for macOS.

## Features

- **Scientific Functions**: Includes sin, cos, tan, log, ln, sqrt, factorial, abs, and more.
- **Accessibility**:
  - High-contrast dark theme (#1e1e1e background, white text).
  - Large buttons and fonts for better visibility.
  - Full keyboard support for all basic operations and scientific functions.
  - Screen reader friendly using a standard `Entry` widget for display.
- **Secure Evaluation**: Uses Python's `ast` module to safely parse and evaluate expressions without using `eval()`.

## Installation

Ensure you have Python 3 installed. Tkinter is usually included with Python on macOS.

```bash
# Clone the repository
git clone <repository-url>
cd <repository-directory>
```

## Running the Application

To run the calculator:

```bash
python3 -m calculator.main
```

## Keyboard Shortcuts

- **0-9, ., +, -, *, / **: Standard operations
- **Enter (=)**: Calculate result
- **Backspace**: Delete last character
- **Escape (C)**: Clear display
- **( )**: Parentheses
- **^**: Power (xʸ)
- **a**: Absolute value (abs)
- **p**: Pi (optional, but 'pi' can be typed)

## Running Tests

To run the test suite:

```bash
python3 -m unittest discover tests
```
