"""
================================================================================
latex_converter.py - LaTeX to Unicode Converter
================================================================================
Version: 1.0.0
Date: 2025-11-25
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Converts LaTeX mathematical expressions to Unicode for display.
Handles common mathematical symbols and expressions.

Features:
- LaTeX symbol conversion
- Subscript/superscript handling
- Fraction formatting
- Greek letters
- Mathematical operators

================================================================================
"""

import logging
import re
from typing import Optional


class LaTeXConverter:
    """
    LaTeX to Unicode converter.
    
    Converts LaTeX math expressions to Unicode text.
    """
    
    def __init__(self):
        """Initialize LaTeX converter."""
        self.logger = logging.getLogger('latex_converter')
        
        # Greek letters
        self.greek_letters = {
            'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
            'epsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ',
            'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ',
            'nu': 'ν', 'xi': 'ξ', 'pi': 'π', 'rho': 'ρ',
            'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ', 'phi': 'φ',
            'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
            'Alpha': 'Α', 'Beta': 'Β', 'Gamma': 'Γ', 'Delta': 'Δ',
            'Theta': 'Θ', 'Lambda': 'Λ', 'Pi': 'Π', 'Sigma': 'Σ',
            'Phi': 'Φ', 'Psi': 'Ψ', 'Omega': 'Ω'
        }
        
        # Mathematical symbols
        self.math_symbols = {
            'infty': '∞', 'partial': '∂', 'nabla': '∇',
            'pm': '±', 'mp': '∓', 'times': '×', 'div': '÷',
            'cdot': '·', 'ast': '∗', 'star': '⋆',
            'leq': '≤', 'geq': '≥', 'neq': '≠', 'approx': '≈',
            'equiv': '≡', 'sim': '∼', 'propto': '∝',
            'in': '∈', 'notin': '∉', 'subset': '⊂', 'supset': '⊃',
            'cap': '∩', 'cup': '∪', 'emptyset': '∅',
            'exists': '∃', 'forall': '∀', 'neg': '¬',
            'wedge': '∧', 'vee': '∨', 'implies': '⇒',
            'iff': '⇔', 'leftarrow': '←', 'rightarrow': '→',
            'leftrightarrow': '↔', 'uparrow': '↑', 'downarrow': '↓',
            'int': '∫', 'sum': '∑', 'prod': '∏',
            'sqrt': '√', 'angle': '∠', 'perp': '⊥',
            'parallel': '∥', 'degree': '°'
        }
        
        # Superscript digits
        self.superscripts = {
            '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
            '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
            '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
            'n': 'ⁿ'
        }
        
        # Subscript digits
        self.subscripts = {
            '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
            '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
            '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎'
        }
    
    def convert(self, latex: str) -> str:
        """
        Convert LaTeX to Unicode.
        
        Args:
            latex: LaTeX string
            
        Returns:
            Unicode string
        """
        try:
            result = latex
            
            # Remove math mode delimiters
            result = re.sub(r'\$\$?', '', result)
            result = re.sub(r'\\[\[\(\)\]]', '', result)
            
            # Convert Greek letters
            result = self._convert_greek(result)
            
            # Convert math symbols
            result = self._convert_symbols(result)
            
            # Convert superscripts
            result = self._convert_superscripts(result)
            
            # Convert subscripts
            result = self._convert_subscripts(result)
            
            # Convert fractions
            result = self._convert_fractions(result)
            
            # Convert sqrt
            result = self._convert_sqrt(result)
            
            # Clean up
            result = self._cleanup(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"LaTeX conversion failed: {e}")
            return latex
    
    def _convert_greek(self, text: str) -> str:
        """Convert Greek letters."""
        result = text
        
        for latex, unicode_char in self.greek_letters.items():
            result = re.sub(r'\\' + latex + r'\b', unicode_char, result)
        
        return result
    
    def _convert_symbols(self, text: str) -> str:
        """Convert mathematical symbols."""
        result = text
        
        for latex, unicode_char in self.math_symbols.items():
            result = re.sub(r'\\' + latex + r'\b', unicode_char, result)
        
        return result
    
    def _convert_superscripts(self, text: str) -> str:
        """Convert superscripts."""
        def replace_superscript(match):
            content = match.group(1)
            return ''.join(self.superscripts.get(c, c) for c in content)
        
        # Match ^{...} or ^x
        result = re.sub(r'\^\{([^}]+)\}', replace_superscript, text)
        result = re.sub(r'\^(\w)', replace_superscript, result)
        
        return result
    
    def _convert_subscripts(self, text: str) -> str:
        """Convert subscripts."""
        def replace_subscript(match):
            content = match.group(1)
            return ''.join(self.subscripts.get(c, c) for c in content)
        
        # Match _{...} or _x
        result = re.sub(r'_\{([^}]+)\}', replace_subscript, text)
        result = re.sub(r'_(\w)', replace_subscript, result)
        
        return result
    
    def _convert_fractions(self, text: str) -> str:
        """Convert fractions."""
        # Simple fractions like \frac{a}{b}
        def replace_fraction(match):
            numerator = match.group(1)
            denominator = match.group(2)
            return f"({numerator}/{denominator})"
        
        result = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', replace_fraction, text)
        
        return result
    
    def _convert_sqrt(self, text: str) -> str:
        """Convert square roots."""
        # \sqrt{x} -> √x
        def replace_sqrt(match):
            content = match.group(1)
            return f"√({content})"
        
        result = re.sub(r'\\sqrt\{([^}]+)\}', replace_sqrt, text)
        
        return result
    
    def _cleanup(self, text: str) -> str:
        """Clean up remaining LaTeX artifacts."""
        # Remove common LaTeX commands
        result = re.sub(r'\\[a-z]+\*?', '', text)
        
        # Remove braces
        result = result.replace('{', '').replace('}', '')
        
        # Clean up whitespace
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    def is_latex(self, text: str) -> bool:
        """
        Check if text contains LaTeX.
        
        Args:
            text: Text to check
            
        Returns:
            True if contains LaTeX
        """
        latex_patterns = [
            r'\$',
            r'\\[a-z]+',
            r'\^',
            r'_',
            r'\\frac',
            r'\\sqrt'
        ]
        
        for pattern in latex_patterns:
            if re.search(pattern, text):
                return True
        
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    converter = LaTeXConverter()
    
    # Test conversions
    tests = [
        r"$E = mc^2$",
        r"$\alpha + \beta = \gamma$",
        r"$x^2 + y^2 = r^2$",
        r"$\frac{a}{b} + \frac{c}{d}$",
        r"$\sqrt{x^2 + y^2}$",
        r"$\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$",
        r"$\int_0^{\infty} e^{-x} dx = 1$"
    ]
    
    for latex in tests:
        unicode_text = converter.convert(latex)
        print(f"{latex:40} → {unicode_text}")
