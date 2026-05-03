"""
Password Validator for Enhanced Security
Validates passwords against complexity requirements
"""

import re
from app.core.config import settings


class PasswordValidator:
    """Validates password strength and complexity"""
    
    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Validate password against security requirements
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check minimum length
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
        
        # Check for uppercase
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for lowercase
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for digit
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        # Check for special character
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check for common passwords (basic check)
        common_passwords = [
            'password', '123456', '12345678', 'qwerty', 'abc123',
            'monkey', 'letmein', 'dragon', '111111', 'baseball',
            'iloveyou', 'master', 'sunshine', 'ashley', 'bailey',
            'passw0rd', 'admin', 'welcome', 'login'
        ]
        if password.lower() in common_passwords:
            return False, "Password is too common. Please choose a stronger password"
        
        return True, ""
    
    @staticmethod
    def get_strength_score(password: str) -> int:
        """
        Calculate password strength score (0-100)
        
        Returns:
            int: Strength score from 0 (weak) to 100 (strong)
        """
        score = 0
        
        # Length contribution (up to 25 points)
        if len(password) >= 8:
            score += 10
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 5
        
        # Uppercase contribution (up to 15 points)
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'[A-Z].*[A-Z]', password):
            score += 5
        
        # Lowercase contribution (up to 15 points)
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[a-z].*[a-z]', password):
            score += 5
        
        # Digit contribution (up to 15 points)
        if re.search(r'\d', password):
            score += 10
        if re.search(r'\d.*\d', password):
            score += 5
        
        # Special character contribution (up to 15 points)
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>].*[!@#$%^&*(),.?":{}|<>]', password):
            score += 5
        
        # Variety contribution (up to 15 points)
        char_types = 0
        if re.search(r'[A-Z]', password):
            char_types += 1
        if re.search(r'[a-z]', password):
            char_types += 1
        if re.search(r'\d', password):
            char_types += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            char_types += 1
        
        if char_types == 4:
            score += 15
        elif char_types == 3:
            score += 10
        elif char_types == 2:
            score += 5
        
        return min(score, 100)
    
    @staticmethod
    def get_strength_label(score: int) -> str:
        """Get human-readable strength label"""
        if score < 30:
            return "Weak"
        elif score < 50:
            return "Fair"
        elif score < 70:
            return "Good"
        elif score < 90:
            return "Strong"
        else:
            return "Very Strong"
