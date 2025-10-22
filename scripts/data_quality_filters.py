#!/usr/bin/env python3
"""
Data Quality Filters for Import and Deduplication
==================================================
Shared validation functions to ensure data quality across all import scripts

Author: AI Assistant
Date: October 22, 2025
"""

import re
from typing import Optional


def is_valid_company_name(name: str, allow_short_names: bool = True) -> bool:
    """
    Validate company name is not just a legal suffix or invalid data
    
    Args:
        name: Company name to validate
        allow_short_names: If True, allows valid short names like "Meta", "IBM", "EY"
    
    Returns:
        bool: True if valid company name, False if suffix-only or invalid
    
    Examples:
        >>> is_valid_company_name("Apple Inc.")
        True
        >>> is_valid_company_name("Inc.")
        False
        >>> is_valid_company_name("Meta")
        True
        >>> is_valid_company_name("-")
        False
    """
    if not name or not isinstance(name, str):
        return False
    
    name_stripped = name.strip()
    
    # Empty or too short (< 2 chars) - but allow if it's in whitelist
    if len(name_stripped) < 2:
        return False
    
    # Suffix-only patterns (EXACT matches - case insensitive)
    # These are companies that are ONLY the suffix with no actual name
    suffix_only_patterns = [
        r'^\.?\s*Ltd\.?\s*[\)\.]?$',           # Ltd, Ltd., .Ltd, Ltd., etc.
        r'^\.?\s*LTD\.?\s*[\)\.]?$',           # LTD, LTD., etc.
        r'^\.?\s*Inc\.?\s*[\)\.]?$',           # Inc, Inc., .Inc, Inc., etc.
        r'^\.?\s*LLC\s*[\)\.]?$',              # LLC
        r'^\.?\s*Corp\.?\s*[\)\.]?$',          # Corp, Corp.
        r'^\.?\s*Corporation\s*[\)\.]?$',      # Corporation
        r'^\.?\s*Limited\s*[\)\.]?$',          # Limited
        r'^\.?\s*L\.?\s*P\.?\s*[\)\.]?$',     # L.P., LP
        r'^\.?\s*P\.?\s*C\.?\s*[\)\.]?$',     # P.C., PC (Professional Corporation)
        r'^\.?\s*LLP\s*[\)\.]?$',              # LLP (Limited Liability Partnership)
    ]
    
    for pattern in suffix_only_patterns:
        if re.match(pattern, name_stripped, re.IGNORECASE):
            return False
    
    # Pure punctuation or very short meaningless names
    if re.match(r'^[\s\-\.\*_,;:!@#$%^&\(\)\[\]\{\}]+$', name_stripped):
        return False
    
    # Just numbers
    if re.match(r'^\d+$', name_stripped):
        return False
    
    # Single character (unless it's in whitelist below)
    if len(name_stripped) == 1:
        return False
    
    # Whitelist for valid short company names (2-4 characters)
    # These are legitimate companies with short names
    if allow_short_names:
        valid_short_names = {
            # Cryptocurrency/Blockchain
            'okx', '0x', 'okex', 'ftx', 'gem', 'dydx', 'snx', 'omg', 'bat', '1inch',
            
            # Tech companies
            'meta', 'uber', 'ibm', 'sap', 'hp', 'ge', 'dell', 'box', 'snap', 
            'lyft', 'zoom', 'okta', 'wish', 'grab', 'yelp', 'nike', 'visa',
            'ebay', 'etsy', 'hulu', 'roku', 'sony', 'asus', 'acer', 'lg',
            
            # Financial services
            'citi', 'hsbc', 'ubs', 'rbc', 'anz', 'td', 'pwc', 'kpmg', 'ey',
            'adp', 'fis', 'mufg', 'jpmc', 'bny',
            
            # Consulting/Services
            'bcg', 'kpmg', 'ey', 'pwc', 'abb',
            
            # Media/Entertainment
            'hbo', 'amc', 'fox', 'nbc', 'cbs', 'bbc', 'mtv', 'espn',
            
            # Retail
            'gap', 'tjx', 'cvs', 'tgt',
            
            # Other
            'aws', 'gsk', '3m', 'bp', 'ups', 'dhl', 'fedex', 'att',
            'nasa', 'fbi', 'cia', 'nsa', 'doe', 'hhs', 'fda', 'cdc',
        }
        
        if name_stripped.lower() in valid_short_names:
            return True
    
    # If length is 2-3 chars and not in whitelist, be cautious
    # Allow if it contains letters and is not just punctuation
    if len(name_stripped) <= 3 and not allow_short_names:
        # Must have at least 2 letters
        if len(re.findall(r'[a-zA-Z]', name_stripped)) < 2:
            return False
    
    # Passed all checks
    return True


def normalize_company_name_for_matching(name: str) -> str:
    """
    Normalize company name for matching purposes (deduplication)
    
    This is DIFFERENT from validation - it's for finding duplicates.
    We still remove suffixes but DON'T validate if the result is empty.
    
    Args:
        name: Company name to normalize
    
    Returns:
        str: Normalized name for matching
    
    Examples:
        >>> normalize_company_name_for_matching("Apple Inc.")
        'apple'
        >>> normalize_company_name_for_matching("Canonical Ltd.")
        'canonical'
    """
    if not name:
        return ""
    
    name = name.lower().strip()
    
    # Remove common legal suffixes for matching purposes
    # But NOTE: We keep the company in our group even if it normalizes to empty
    # The validation function above will prevent creation of new suffix-only companies
    suffixes = [
        r'\s+(labs?|inc\.?|llc|corp\.?|corporation|ltd\.?|limited|'
        r'network|protocol|technologies|tech|group)$'
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)
    
    # Remove special characters but keep spaces
    name = re.sub(r'[^\w\s]', '', name)
    
    return name.strip()


def should_skip_company_deduplication(name: str) -> bool:
    """
    Determine if a company should be skipped during deduplication
    
    Skip companies that:
    - Are suffix-only (they're bad data, not real companies)
    - Are pure punctuation
    - Are too short to safely deduplicate
    
    Args:
        name: Company name to check
    
    Returns:
        bool: True if should skip, False if should include in deduplication
    
    Examples:
        >>> should_skip_company_deduplication("Ltd.")
        True
        >>> should_skip_company_deduplication("Apple Ltd.")
        False
    """
    # If it fails validation, skip it
    if not is_valid_company_name(name, allow_short_names=False):
        return True
    
    # Additional deduplication-specific rules
    
    # Very short names (< 3 chars) - risky to deduplicate
    # unless they're in the whitelist
    if len(name.strip()) < 3:
        valid_short = {'ey', 'ge', 'hp', '0x', 'ge', 'lg', '3m', 'bp'}
        if name.strip().lower() not in valid_short:
            return True
    
    return False


def get_company_validation_message(name: str) -> Optional[str]:
    """
    Get a human-readable message explaining why a company name is invalid
    
    Args:
        name: Company name to validate
    
    Returns:
        str: Error message if invalid, None if valid
    """
    if not name or not isinstance(name, str):
        return "Company name is empty or not a string"
    
    name_stripped = name.strip()
    
    if len(name_stripped) < 2:
        return f"Company name too short: '{name_stripped}' (< 2 characters)"
    
    if not is_valid_company_name(name):
        # Check specific patterns to give helpful message
        if re.match(r'^\.?\s*(Ltd|LTD|Inc|LLC|Corp|Corporation|Limited|L\.?P\.?|P\.?C\.?|LLP)\.?\s*$', 
                   name_stripped, re.IGNORECASE):
            return f"Company name is only a legal suffix: '{name_stripped}'"
        
        if re.match(r'^[\s\-\.\*_,;:!@#$%^&\(\)\[\]\{\}]+$', name_stripped):
            return f"Company name is only punctuation: '{name_stripped}'"
        
        if re.match(r'^\d+$', name_stripped):
            return f"Company name is only numbers: '{name_stripped}'"
        
        return f"Company name failed validation: '{name_stripped}'"
    
    return None


# For backwards compatibility with existing code
def validate_company_name(name: str) -> bool:
    """Alias for is_valid_company_name for backwards compatibility"""
    return is_valid_company_name(name)


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("Apple Inc.", True, "Valid company with suffix"),
        ("Inc.", False, "Suffix only"),
        ("Ltd.", False, "Suffix only"),
        ("LLC", False, "Suffix only"),
        ("Meta", True, "Valid short name"),
        ("IBM", True, "Valid short name (whitelist)"),
        ("EY", True, "Valid short name (whitelist)"),
        ("-", False, "Just punctuation"),
        ("***", False, "Just punctuation"),
        ("", False, "Empty string"),
        ("A", False, "Single character"),
        ("0X", True, "Valid crypto company"),
        ("P.C.", False, "Suffix only (Professional Corporation)"),
        ("Google LLC", True, "Valid company with LLC suffix"),
        ("Canonical Ltd.", True, "Valid company with Ltd suffix"),
        ("123", False, "Just numbers"),
    ]
    
    print("Running validation tests...\n")
    passed = 0
    failed = 0
    
    for name, expected, description in test_cases:
        result = is_valid_company_name(name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description}")
        print(f"        Input: '{name}' -> Expected: {expected}, Got: {result}")
        
        if not result:
            msg = get_company_validation_message(name)
            print(f"        Message: {msg}")
        print()
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")

