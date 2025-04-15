from flask import Flask, render_template, request, jsonify
import math
import json
from flask import Flask

app = Flask(__name__)

# Calculator state class
class CalculatorState:
    def __init__(self):
        self.current_input = "0"
        self.previous_input = None
        self.operation = None
        self.memory = 0
        self.history = []
        self.is_scientific_mode = False
        self.is_angle_in_radians = True
        self.waiting_for_operand = False
        self.pending_function = None

    def to_dict(self):
        return {
            "currentInput": self.current_input,
            "previousInput": self.previous_input,
            "operation": self.operation,
            "memory": self.memory,
            "history": self.history,
            "isScientificMode": self.is_scientific_mode,
            "isAngleInRadians": self.is_angle_in_radians,
            "waitingForOperand": self.waiting_for_operand
        }

# Create a global calculator state
calculator = CalculatorState()

# Helper function to handle floating point precision
def round_to_decimal_places(num, places):
    if isinstance(num, (int, float)) and not math.isnan(num):
        multiplier = 10 ** places
        return round(num * multiplier) / multiplier
    return num

# Function to get operation symbol for display
def get_operation_symbol(op):
    symbols = {
        '+': '+',
        '-': '−',
        '*': '×',
        '/': '÷',
        '%': 'mod',
        '^': '^'
    }
    return symbols.get(op, op)

# Add calculation to history
def add_to_history(expression, result):
    calculator.history.insert(0, {
        "expression": expression,
        "result": result
    })
    
    # Keep only the last 10 history items
    if len(calculator.history) > 10:
        calculator.history.pop()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    action = data.get('action')
    value = data.get('value')
    
    result = process_action(action, value)
    return jsonify(result)

def process_action(action, value=None):
    global calculator
    response = {"success": True, "state": None, "error": None}
    
    try:
        if action == "append":
            append_value(value)
        elif action == "operation":
            prepare_binary_operation(value)
        elif action == "calculate":
            perform_calculation()
        elif action == "clear":
            clear_calculator()
        elif action == "backspace":
            backspace()
        elif action == "toggleSign":
            toggle_sign()
        elif action == "memory":
            handle_memory(value)
        elif action in ["sin", "cos", "tan", "asin", "acos", "atan"]:
            apply_trig_function(action)
        elif action in ["log", "ln", "sqrt", "sqr"]:
            apply_function(action)
        elif action == "factorial":
            calculate_factorial()
        elif action == "pow":
            prepare_binary_operation("^")
        elif action == "e":
            calculator.current_input = str(math.e)
        elif action == "pi":
            calculator.current_input = str(math.pi)
        elif action == "mod":
            prepare_binary_operation("%")
        elif action == "deg":
            calculator.is_angle_in_radians = False
        elif action == "rad":
            calculator.is_angle_in_radians = True
        
        response["state"] = calculator.to_dict()
    except Exception as e:
        calculator.current_input = "Error"
        response["success"] = False
        response["error"] = str(e)
        response["state"] = calculator.to_dict()
    
    return response

def append_value(value):
    # If we're waiting for an operand, replace the display
    if calculator.waiting_for_operand:
        calculator.current_input = value
        calculator.waiting_for_operand = False
    elif calculator.current_input == '0' and value != '.':
        # If current input is just '0' and not entering decimal
        calculator.current_input = value
    else:
        # Otherwise append to current input
        # If decimal is pressed and already exists, don't append
        if value == '.' and '.' in calculator.current_input:
            return
        calculator.current_input += value

def prepare_binary_operation(operation):
    if calculator.previous_input is not None and not calculator.waiting_for_operand:
        # If there's already a pending operation, calculate it first
        perform_calculation()
    
    calculator.previous_input = calculator.current_input
    calculator.operation = operation
    calculator.waiting_for_operand = True

def apply_trig_function(func_name):
    try:
        value = float(calculator.current_input)
        
        # Convert degrees to radians if necessary
        if not calculator.is_angle_in_radians and func_name in ["sin", "cos", "tan"]:
            value = value * (math.pi / 180)
        
        # Apply the appropriate function
        if func_name == "sin":
            result = math.sin(value)
        elif func_name == "cos":
            result = math.cos(value)
        elif func_name == "tan":
            result = math.tan(value)
        elif func_name == "asin":
            result = math.asin(value)
        elif func_name == "acos":
            result = math.acos(value)
        elif func_name == "atan":
            result = math.atan(value)
        else:
            raise ValueError(f"Unknown function: {func_name}")
        
        # Check for errors like sin(90) in degrees which should be 1, not slightly off
        if abs(result) < 1e-14:
            final_result = 0
        elif abs(abs(result) - 1) < 1e-14:
            final_result = 1 if result > 0 else -1
        else:
            final_result = round_to_decimal_places(result, 14)
        
        # Format function name for display
        display_func_names = {
            'sin': 'sin', 'cos': 'cos', 'tan': 'tan',
            'asin': 'sin⁻¹', 'acos': 'cos⁻¹', 'atan': 'tan⁻¹'
        }
        display_func_name = display_func_names.get(func_name, func_name)
        
        expression = f"{display_func_name}({calculator.current_input})"
        calculator.current_input = str(final_result)
        
        # Add to history
        add_to_history(expression, calculator.current_input)
        
    except Exception as e:
        calculator.current_input = "Error"
        raise

def apply_function(func_name):
    try:
        value = float(calculator.current_input)
        
        # Apply the appropriate function
        if func_name == "log":
            result = math.log10(value)
        elif func_name == "ln":
            result = math.log(value)
        elif func_name == "sqrt":
            result = math.sqrt(value)
        elif func_name == "sqr":
            result = value * value
        else:
            raise ValueError(f"Unknown function: {func_name}")
        
        rounded_result = round_to_decimal_places(result, 14)
        
        # Format function name for display
        display_func_names = {
            'log': 'log', 'ln': 'ln', 'sqrt': '√', 'sqr': 'sqr'
        }
        display_func_name = display_func_names.get(func_name, func_name)
        
        expression = f"{display_func_name}({calculator.current_input})"
        calculator.current_input = str(rounded_result)
        
        # Add to history
        add_to_history(expression, calculator.current_input)
        
    except Exception as e:
        calculator.current_input = "Error"
        raise

def calculate_factorial():
    try:
        num = int(float(calculator.current_input))
        
        if num < 0 or not float(calculator.current_input).is_integer():
            calculator.current_input = "Error"
            return
        
        # Limit factorials to avoid hanging the server
        if num > 170:
            calculator.current_input = "Error: Value too large"
            return
        
        factorial = 1
        for i in range(2, num + 1):
            factorial *= i
        
        expression = f"{calculator.current_input}!"
        calculator.current_input = str(factorial)
        
        # Add to history
        add_to_history(expression, calculator.current_input)
        
    except Exception as e:
        calculator.current_input = "Error"
        raise

def perform_calculation():
    try:
        if calculator.previous_input is None or calculator.operation is None:
            # No pending operation
            return
        
        prev = float(calculator.previous_input)
        current = float(calculator.current_input)
        
        # Perform the calculation based on the operation
        if calculator.operation == '+':
            result = prev + current
        elif calculator.operation == '-':
            result = prev - current
        elif calculator.operation == '*':
            result = prev * current
        elif calculator.operation == '/':
            if abs(current) < 1e-15:
                raise ZeroDivisionError("Division by zero")
            result = prev / current
        elif calculator.operation == '%':
            if abs(current) < 1e-15:
                raise ZeroDivisionError("Modulo by zero")
            result = prev % current
        elif calculator.operation == '^':
            result = math.pow(prev, current)
        else:
            raise ValueError(f"Unknown operation: {calculator.operation}")
        
        # Handle precision issues
        result = round_to_decimal_places(result, 14)
        
        # Format for display and history
        op_symbol = get_operation_symbol(calculator.operation)
        expression = f"{calculator.previous_input} {op_symbol} {calculator.current_input}"
        
        calculator.current_input = str(result)
        calculator.previous_input = None
        calculator.operation = None
        calculator.waiting_for_operand = True
        
        # Add to history
        add_to_history(expression, calculator.current_input)
        
    except Exception as e:
        calculator.current_input = "Error"
        raise

def clear_calculator():
    calculator.current_input = '0'
    calculator.previous_input = None
    calculator.operation = None
    calculator.waiting_for_operand = False
    calculator.pending_function = None

def backspace():
    if len(calculator.current_input) > 1:
        calculator.current_input = calculator.current_input[:-1]
    else:
        calculator.current_input = '0'

def toggle_sign():
    if calculator.current_input != '0':
        parsed = float(calculator.current_input)
        calculator.current_input = str(-parsed)

def handle_memory(action):
    current_value = float(calculator.current_input)
    
    if action == "clear":
        calculator.memory = 0
    elif action == "recall":
        calculator.current_input = str(calculator.memory)
    elif action == "add":
        calculator.memory = round_to_decimal_places(calculator.memory + current_value, 14)
    elif action == "subtract":
        calculator.memory = round_to_decimal_places(calculator.memory - current_value, 14)

@app.route('/api/get_state', methods=['GET'])
def get_state():
    return jsonify(calculator.to_dict())

# WSGI handler for Vercel
handler = app