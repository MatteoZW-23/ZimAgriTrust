"""
Input Validation and Sanitization
Prevents injection attacks and ensures data integrity
"""

import re
from typing import Any, Optional
from pydantic import BaseModel, field_validator
from html import escape

class InputValidator:
    """Validates and sanitizes user input to prevent security vulnerabilities"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """
        Sanitize string input to prevent XSS and injection attacks
        
        Args:
            input_str: The input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Truncate to max length
        input_str = input_str[:max_length]
        
        # Remove null bytes
        input_str = input_str.replace('\x00', '')
        
        # Escape HTML entities to prevent XSS
        input_str = escape(input_str)
        
        return input_str
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not phone:
            return False
        
        # Remove spaces and special characters
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Check format (international: + followed by digits)
        if not re.match(r'^\+\d{7,15}$', cleaned):
            return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email:
            return False
        
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_national_id(national_id: str) -> bool:
        """
        Validate national ID format
        
        Args:
            national_id: National ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not national_id:
            return False
        
        # Remove spaces and hyphens
        cleaned = re.sub(r'[\s-]', '', national_id)
        
        # Check if alphanumeric and reasonable length (8-20 characters)
        if not re.match(r'^[A-Za-z0-9]{8,20}$', cleaned):
            return False
        
        return True
    
    @staticmethod
    def validate_amount(amount: Any) -> bool:
        """
        Validate monetary amount
        
        Args:
            amount: Amount to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            amount_float = float(amount)
            # Check if positive and reasonable
            return 0 <= amount_float <= 1000000000  # Max 1 billion
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_sql_input(input_str: str) -> str:
        """
        Sanitize input for SQL queries (defense in depth)
        Note: SQLAlchemy ORM provides primary protection, this is additional defense
        
        Args:
            input_str: Input to sanitize
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Remove SQL injection patterns
        dangerous_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION|OR|AND)\b)",
            r"(\b(WHERE|HAVING|GROUP BY|ORDER BY)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(;|')",
            r"(\b(1=1|1=2|true|false)\b)",
        ]
        
        for pattern in dangerous_patterns:
            input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE)
        
        return input_str
    
    @staticmethod
    def validate_file_upload(filename: str, max_size_mb: int = 10) -> dict:
        """
        Validate file upload
        
        Args:
            filename: Name of the file
            max_size_mb: Maximum file size in MB
            
        Returns:
            Dictionary with validation result
        """
        result = {"valid": True, "error": None}
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if f'.{file_ext}' not in allowed_extensions:
            result["valid"] = False
            result["error"] = f"File type .{file_ext} not allowed"
            return result
        
        # Check for suspicious patterns in filename
        suspicious_patterns = ['..', '/', '\\', '\x00']
        for pattern in suspicious_patterns:
            if pattern in filename:
                result["valid"] = False
                result["error"] = "Invalid filename"
                return result
        
        return result
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False
        
        # Basic URL validation
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(pattern, url) is not None


class SecureBaseModel(BaseModel):
    """Base model with input validation"""
    
    @field_validator("*")
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize all string fields"""
        if isinstance(v, str):
            return InputValidator.sanitize_string(v)
        return v


class SQLInjectionPrevention:
    """Additional SQL injection prevention measures"""
    
    @staticmethod
    def is_suspicious_query(query: str) -> bool:
        """
        Check if query contains suspicious patterns
        
        Args:
            query: SQL query to check
            
        Returns:
            True if suspicious, False otherwise
        """
        suspicious_patterns = [
            r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION)\b.*\b(WHERE|HAVING)\b.*\b(OR|AND)\b.*\b(=|LIKE)\b.*\b(1=1|1=2|true|false)\b)",
            r"(?i)(--|#|\/\*|\*\/)",
            r"(?i)(\bEXEC\b|\bEXECUTE\b)",
            r"(?i)(\bxp_cmdshell\b|\bsp_oacreate\b)",
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query):
                return True
        
        return False


class XSSPrevention:
    """Cross-Site Scripting prevention"""
    
    @staticmethod
    def sanitize_html(input_str: str) -> str:
        """
        Sanitize HTML input to prevent XSS
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Escape HTML entities
        dangerous_chars = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
        }
        
        for char, replacement in dangerous_chars.items():
            input_str = input_str.replace(char, replacement)
        
        return input_str
    
    @staticmethod
    def is_xss_attempt(input_str: str) -> bool:
        """
        Check if input contains XSS patterns
        
        Args:
            input_str: Input to check
            
        Returns:
            True if XSS attempt detected, False otherwise
        """
        xss_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
            r'document\.cookie',
            r'eval\s*\(',
            r'expression\s*\(',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        
        return False


class CSRFProtection:
    """Cross-Site Request Forgery protection"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """
        Generate CSRF token
        
        Returns:
            CSRF token
        """
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, session_token: str) -> bool:
        """
        Validate CSRF token
        
        Args:
            token: Token from request
            session_token: Token stored in session
            
        Returns:
            True if valid, False otherwise
        """
        if not token or not session_token:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        import secrets
        return secrets.compare_digest(token, session_token)
