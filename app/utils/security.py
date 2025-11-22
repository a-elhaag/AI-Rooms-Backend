"""
Security utilities - Simplified for POC (no JWT, just basic password check).
"""


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Simple password verification for POC.
    In production, use proper hashing like bcrypt.
    
    Args:
        plain_password: Plain text password
        stored_password: Stored password (plain text in POC)
        
    Returns:
        bool: True if password matches
    """
    return plain_password == stored_password
