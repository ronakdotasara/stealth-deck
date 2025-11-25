"""
================================================================================
calculator.py - Calculator Logic for Raspberry Pi
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Calculator logic and expression evaluation.
Handles arithmetic operations, functions, and expression parsing.

Features:
- Basic arithmetic operations
- Advanced functions (sin, cos, sqrt, etc.)
- Expression evaluation
- Error handling
- History tracking

================================================================================
"""

import logging
import math
import re
from typing import Optional, List, Dict, Any
from decimal import Decimal, InvalidOperation


class Calculator:
    """
    Calculator logic engine.
    
    Evaluates mathematical expressions.
    """
    
    def __init__(self):
        """Initialize calculator."""
        self.logger = logging.getLogger('calculator')
        
        self.history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        self.memory = 0.0
        
        self.functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log10,
            'ln': math.log,
            'abs': abs,
            'floor': math.floor,
            'ceil': math.ceil,
            'round': round,
        }
        
        self.constants = {
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau,
        }
    
    def evaluate(self, expression: str) -> Optional[float]:
        """
        Evaluate mathematical expression.
        
        Args:
            expression: Expression to evaluate
            
        Returns:
            Result or None if error
        """
        try:
            expression = expression.strip()
            
            if not expression:
                return None
            
            expression = self._preprocess(expression)
            
            result = self._safe_eval(expression)
            
            self._add_to_history(expression, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return None
    
    def _preprocess(self, expression: str) -> str:
        """
        Preprocess expression.
        
        Args:
            expression: Raw expression
            
        Returns:
            Preprocessed expression
        """
        expression = expression.lower()
        
        expression = expression.replace('^', '**')
        expression = expression.replace('×', '*')
        expression = expression.replace('÷', '/')
        
        for name, value in self.constants.items():
            expression = expression.replace(name, str(value))
        
        expression = re.sub(r'(\d)([a-z])', r'\1*\2', expression)
        
        return expression
    
    def _safe_eval(self, expression: str) -> float:
        """
        Safely evaluate expression.
        
        Args:
            expression: Expression to evaluate
            
        Returns:
            Result
        """
        allowed_chars = set('0123456789+-*/().** ')
        allowed_chars.update(self.functions.keys())
        
        safe_dict = {
            '__builtins__': {},
            **self.functions,
            'pi': math.pi,
            'e': math.e,
        }
        
        result = eval(expression, safe_dict, {})
        
        return float(result)
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: float, b: float) -> Optional[float]:
        """Divide two numbers."""
        if b == 0:
            self.logger.error("Division by zero")
            return None
        return a / b
    
    def power(self, base: float, exponent: float) -> float:
        """Raise to power."""
        return base ** exponent
    
    def sqrt(self, n: float) -> Optional[float]:
        """Square root."""
        if n < 0:
            return None
        return math.sqrt(n)
    
    def percentage(self, value: float, percent: float) -> float:
        """Calculate percentage."""
        return (value * percent) / 100
    
    def memory_store(self, value: float) -> None:
        """Store value in memory."""
        self.memory = value
        self.logger.debug(f"Memory stored: {value}")
    
    def memory_recall(self) -> float:
        """Recall value from memory."""
        return self.memory
    
    def memory_clear(self) -> None:
        """Clear memory."""
        self.memory = 0.0
        self.logger.debug("Memory cleared")
    
    def memory_add(self, value: float) -> None:
        """Add to memory."""
        self.memory += value
        self.logger.debug(f"Memory add: {value}, total: {self.memory}")
    
    def memory_subtract(self, value: float) -> None:
        """Subtract from memory."""
        self.memory -= value
        self.logger.debug(f"Memory subtract: {value}, total: {self.memory}")
    
    def _add_to_history(self, expression: str, result: float) -> None:
        """
        Add calculation to history.
        
        Args:
            expression: Expression evaluated
            result: Result value
        """
        import time
        
        entry = {
            'expression': expression,
            'result': result,
            'timestamp': time.time()
        }
        
        self.history.append(entry)
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get calculation history.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of history entries
        """
        return self.history[-limit:]
    
    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()
        self.logger.info("History cleared")
    
    def format_result(self, result: float, precision: int = 6) -> str:
        """
        Format result for display.
        
        Args:
            result: Result value
            precision: Decimal precision
            
        Returns:
            Formatted string
        """
        if result is None:
            return "Error"
        
        if abs(result) < 1e-10:
            return "0"
        
        if abs(result) > 1e10 or abs(result) < 1e-4:
            return f"{result:.{precision}e}"
        
        if result == int(result):
            return str(int(result))
        
        formatted = f"{result:.{precision}f}"
        formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted
    
    def validate_expression(self, expression: str) -> bool:
        """
        Validate expression syntax.
        
        Args:
            expression: Expression to validate
            
        Returns:
            True if valid
        """
        try:
            expression = self._preprocess(expression)
            
            open_parens = expression.count('(')
            close_parens = expression.count(')')
            
            if open_parens != close_parens:
                return False
            
            self._safe_eval(expression)
            
            return True
            
        except Exception:
            return False
    
    def solve_equation(self, equation: str, variable: str = 'x') -> Optional[float]:
        """
        Solve simple equation (linear).
        
        Args:
            equation: Equation string (e.g., "2x + 5 = 15")
            variable: Variable to solve for
            
        Returns:
            Solution or None
        """
        try:
            if '=' not in equation:
                return None
            
            left, right = equation.split('=')
            
            left = left.strip()
            right = right.strip()
            
            # Simple linear equation solver
            # This is a very basic implementation
            
            return None  # TODO: Implement proper equation solver
            
        except Exception as e:
            self.logger.error(f"Equation solving failed: {e}")
            return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    calc = Calculator()
    
    # Test basic operations
    print(f"2 + 3 = {calc.evaluate('2 + 3')}")
    print(f"10 * 5 = {calc.evaluate('10 * 5')}")
    print(f"sqrt(16) = {calc.evaluate('sqrt(16)')}")
    print(f"sin(pi/2) = {calc.evaluate('sin(pi/2)')}")
    
    # Test history
    history = calc.get_history()
    print(f"\nHistory: {len(history)} entries")
    for entry in history:
        print(f"  {entry['expression']} = {entry['result']}")
