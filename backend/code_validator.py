import subprocess
import os
import json
import re
from typing import Dict, List, Any, Tuple, Optional

class CodeValidator:
    """
    A utility class for validating generated code across different languages.
    Provides static analysis, syntax checking, and potential runtime error detection.
    """
    
    @staticmethod
    def validate_javascript(code: str) -> Tuple[bool, List[str]]:
        """
        Validate JavaScript code using ESLint.
        Returns (success, [error_messages])
        """
        try:
            # Write code to temporary file
            temp_file = "_temp_validation.js"
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Run ESLint if available (non-blocking, just reports)
            try:
                result = subprocess.run(
                    ["npx", "eslint", "--no-eslintrc", "--parser-options", "ecmaVersion:latest", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode != 0:
                    return False, [line for line in result.stderr.split("\n") if line.strip()]
            except Exception as e:
                # If ESLint fails, fall back to basic JS validation
                pass
                
            # Use Node.js to check for syntax errors
            result = subprocess.run(
                ["node", "--check", temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            if result.returncode != 0:
                # Extract error messages
                errors = [line for line in result.stderr.split("\n") if line.strip()]
                return False, errors
            
            return True, []
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
        finally:
            # Ensure cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)

    @staticmethod
    def validate_python(code: str) -> Tuple[bool, List[str]]:
        """
        Validate Python code using the built-in compile function and pylint if available.
        Returns (success, [error_messages])
        """
        try:
            # First, compile the code to check for syntax errors
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                line_no = e.lineno if hasattr(e, 'lineno') else '?'
                return False, [f"Syntax error at line {line_no}: {str(e)}"]
            
            # Write code to temporary file for additional checks
            temp_file = "_temp_validation.py"
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Run pylint if available (non-blocking)
            try:
                result = subprocess.run(
                    ["python", "-m", "pylint", temp_file, "--errors-only"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    return False, [line for line in result.stderr.split("\n") + result.stdout.split("\n") if line.strip()]
            except Exception:
                # Pylint might not be installed, continue without it
                pass
                
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            return True, []
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
        finally:
            # Ensure cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)

    @staticmethod
    def validate_html(code: str) -> Tuple[bool, List[str]]:
        """
        Basic HTML validation - checks for unclosed tags and syntax issues.
        Returns (success, [error_messages])
        """
        # Simple tag matching
        errors = []
        open_tags = []
        tag_pattern = re.compile(r'<(/?)(\w+).*?(/?)>')
        
        for match in tag_pattern.finditer(code):
            is_closing, tag_name, is_self_closing = match.groups()
            
            if is_self_closing or tag_name in ['meta', 'link', 'input', 'img', 'br', 'hr']:
                # Self-closing tags, no need to track
                continue
                
            if is_closing:  # Closing tag
                if not open_tags:
                    errors.append(f"Found closing tag </'{tag_name}'> without matching opening tag")
                elif open_tags[-1] != tag_name:
                    errors.append(f"Expected closing tag </'{open_tags[-1]}'> but found </'{tag_name}'>")
                    open_tags.pop()
                else:
                    open_tags.pop()
            else:  # Opening tag
                open_tags.append(tag_name)
        
        # Check for unclosed tags
        for tag in reversed(open_tags):
            errors.append(f"Unclosed tag <'{tag}'>")
            
        return len(errors) == 0, errors

    @staticmethod
    def validate_css(code: str) -> Tuple[bool, List[str]]:
        """
        Basic CSS validation to check for syntax issues.
        Returns (success, [error_messages])
        """
        errors = []
        
        # Check for unmatched curly braces
        open_braces = 0
        for i, char in enumerate(code):
            if char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1
                if open_braces < 0:
                    errors.append(f"Unexpected closing brace at position {i}")
                    open_braces = 0
        
        if open_braces > 0:
            errors.append(f"Missing {open_braces} closing brace(s)")
            
        return len(errors) == 0, errors
        
    @staticmethod 
    def validate_file(filename: str, content: str) -> Tuple[bool, List[str]]:
        """
        Validate a file's content based on its extension.
        Returns (success, [error_messages])
        """
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ['.js', '.jsx', '.ts', '.tsx']:
            return CodeValidator.validate_javascript(content)
        elif ext in ['.py']:
            return CodeValidator.validate_python(content)
        elif ext in ['.html', '.htm']:
            return CodeValidator.validate_html(content)
        elif ext in ['.css']:
            return CodeValidator.validate_css(content)
        else:
            # For other files, we assume they are valid
            return True, []
            
    @staticmethod
    def validate_project(files: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Validate all files in a project.
        Input: Dictionary of file category -> filename -> content
        Returns: Dictionary with validation results
        """
        validation_results = {
            "valid": True,
            "file_count": 0,
            "error_count": 0,
            "errors": {},
            "warnings": [],
            "fix_suggestions": {}
        }
        
        for category, files_dict in files.items():
            for filename, content in files_dict.items():
                validation_results["file_count"] += 1
                success, errors = CodeValidator.validate_file(filename, content)
                
                if not success:
                    validation_results["valid"] = False
                    validation_results["error_count"] += len(errors)
                    key = f"{category}/{filename}"
                    validation_results["errors"][key] = errors
                    
                    # Generate fix suggestions where possible
                    if len(errors) > 0:
                        validation_results["fix_suggestions"][key] = CodeValidator.generate_fix_suggestion(
                            filename, content, errors
                        )
                        
        # Add general recommendations if there are errors
        if not validation_results["valid"]:
            validation_results["warnings"].append(
                "Validation errors detected. Code may not run correctly."
            )
            
        return validation_results
    
    @staticmethod
    def generate_fix_suggestion(filename: str, content: str, errors: List[str]) -> List[str]:
        """Generate suggestions to fix common errors"""
        suggestions = []
        
        # Common JavaScript fixes
        if filename.endswith(('.js', '.jsx')):
            if any("Unexpected token" in err for err in errors):
                suggestions.append("Check for missing semicolons, parentheses, or brackets")
            if any("undefined" in err.lower() for err in errors):
                suggestions.append("Check for undefined variables or imports")
            if any("import" in err.lower() for err in errors):
                suggestions.append("Make sure all imports are properly defined and modules are installed")
                
        # Common Python fixes
        if filename.endswith('.py'):
            if any("IndentationError" in err for err in errors):
                suggestions.append("Check for consistent indentation (spaces vs tabs)")
            if any("NameError" in err for err in errors):
                suggestions.append("Verify all variables are defined before use")
            if any("ImportError" in err for err in errors):
                suggestions.append("Ensure all imported modules are available and correctly spelled")
                
        # General suggestions
        if not suggestions:
            suggestions.append("Review the code for syntax errors and typos")
            
        return suggestions

# Example usage:
# results = CodeValidator.validate_project(generated_code)
# if not results["valid"]:
#     print(f"Found {results['error_count']} errors in {len(results['errors'])} files")
