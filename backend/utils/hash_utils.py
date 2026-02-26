"""
SHA-256 hash calculation for files
"""

import hashlib
from werkzeug.datastructures import FileStorage


def calculate_file_hash(file):
    """
    Calculate SHA-256 hash of a file
    """
    # Create hash object
    sha256_hash = hashlib.sha256()
    
    # Read file in chunks to handle large files
    CHUNK_SIZE = 8192
    
    # Reset file pointer to beginning
    file.seek(0)
    
    # Read and update hash
    while True:
        chunk = file.read(CHUNK_SIZE)
        if not chunk:
            break
        sha256_hash.update(chunk)
    
    # Reset file pointer for subsequent reads
    file.seek(0)
    
    # Return hexadecimal representation
    return sha256_hash.hexdigest()


def calculate_bytes_hash(data):
    """
    Calculate SHA-256 hash of bytes data
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data)
    return sha256_hash.hexdigest()


def calculate_string_hash(text):
    """
    Calculate SHA-256 hash of a string
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(text.encode('utf-8'))
    return sha256_hash.hexdigest()


def verify_hash(file, expected_hash):
    """
    Verify if file matches expected hash
    """
    actual_hash = calculate_file_hash(file)
    return actual_hash == expected_hash
