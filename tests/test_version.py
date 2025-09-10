"""
Tests for version module
"""

import pytest
import re
from version import (
    __version__,
    __author__,
    __email__,
    __description__,
    get_version_info,
    get_version_string
)


class TestVersionConstants:
    """Test version constants"""
    
    def test_version_format(self):
        """Test that version follows semantic versioning"""
        version_pattern = r'^\d+\.\d+\.\d+$'
        assert re.match(version_pattern, __version__), f"Version {__version__} doesn't match semantic versioning"
    
    def test_version_not_empty(self):
        """Test that version is not empty"""
        assert __version__ is not None
        assert __version__ != ""
        assert len(__version__) > 0
    
    def test_author_info(self):
        """Test author information is present"""
        assert __author__ is not None
        assert __author__ != ""
        assert "Chris Watkins" in __author__
    
    def test_email_format(self):
        """Test email format is valid"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(email_pattern, __email__), f"Email {__email__} is not valid"
        assert "chris@watkinslabs.com" in __email__
    
    def test_description_present(self):
        """Test description is present and meaningful"""
        assert __description__ is not None
        assert __description__ != ""
        assert len(__description__) > 10
        assert "speech" in __description__.lower() or "dictation" in __description__.lower()


class TestVersionFunctions:
    """Test version utility functions"""
    
    def test_get_version_info_structure(self):
        """Test get_version_info returns correct structure"""
        info = get_version_info()
        
        assert isinstance(info, dict)
        assert 'version' in info
        assert 'author' in info
        assert 'email' in info
        assert 'description' in info
        
        assert info['version'] == __version__
        assert info['author'] == __author__
        assert info['email'] == __email__
        assert info['description'] == __description__
    
    def test_get_version_string(self):
        """Test get_version_string returns string version"""
        version_str = get_version_string()
        
        assert isinstance(version_str, str)
        assert version_str == __version__
    
    def test_version_info_immutable(self):
        """Test that version info doesn't change between calls"""
        info1 = get_version_info()
        info2 = get_version_info()
        
        assert info1 == info2
        assert info1 is not info2  # Different dict objects
    
    def test_version_string_consistency(self):
        """Test version string is consistent"""
        str1 = get_version_string()
        str2 = get_version_string()
        
        assert str1 == str2
        assert str1 == __version__


class TestVersionIntegration:
    """Integration tests for version module"""
    
    def test_version_module_imports(self):
        """Test that version module imports work"""
        import version
        
        # Check all expected attributes exist
        assert hasattr(version, '__version__')
        assert hasattr(version, '__author__')
        assert hasattr(version, '__email__')
        assert hasattr(version, '__description__')
        assert hasattr(version, 'get_version_info')
        assert hasattr(version, 'get_version_string')
    
    def test_version_usable_in_cli(self):
        """Test version can be used in CLI context"""
        from version import __version__
        
        # Test that version can be formatted into strings
        display_string = f"DICTATOR v{__version__}"
        assert "DICTATOR v" in display_string
        assert __version__ in display_string
    
    def test_version_usable_in_gui(self):
        """Test version can be used in GUI context"""
        from version import __version__
        
        # Test that version can be used in window titles
        window_title = f"DICTATOR v{__version__}"
        assert len(window_title) > 0
        assert "DICTATOR" in window_title
        assert __version__ in window_title
    
    def test_version_info_serializable(self):
        """Test that version info can be serialized"""
        import json
        
        info = get_version_info()
        
        # Should be JSON serializable
        json_str = json.dumps(info)
        parsed = json.loads(json_str)
        
        assert parsed == info
    
    def test_version_comparisons(self):
        """Test that version can be compared"""
        from version import __version__
        
        # Should be able to compare versions
        parts = __version__.split('.')
        assert len(parts) == 3
        
        # All parts should be numeric
        for part in parts:
            assert part.isdigit()
            assert int(part) >= 0
    
    def test_version_increment_logic(self):
        """Test version increment logic for build scripts"""
        from version import __version__
        
        # Test parsing current version
        major, minor, patch = map(int, __version__.split('.'))
        
        # Test that we can increment each part
        new_patch = f"{major}.{minor}.{patch + 1}"
        new_minor = f"{major}.{minor + 1}.0"
        new_major = f"{major + 1}.0.0"
        
        # All should be valid version strings
        version_pattern = r'^\d+\.\d+\.\d+$'
        assert re.match(version_pattern, new_patch)
        assert re.match(version_pattern, new_minor)
        assert re.match(version_pattern, new_major)


class TestVersionEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_version_constants_immutable(self):
        """Test that version constants behave as expected"""
        # These should not change during runtime
        original_version = __version__
        original_author = __author__
        original_email = __email__
        original_description = __description__
        
        # After some operations
        _ = get_version_info()
        _ = get_version_string()
        
        # Should still be the same
        assert __version__ == original_version
        assert __author__ == original_author
        assert __email__ == original_email
        assert __description__ == original_description
    
    def test_version_no_leading_zeros(self):
        """Test version has no leading zeros"""
        parts = __version__.split('.')
        
        for part in parts:
            if len(part) > 1:
                assert not part.startswith('0'), f"Version part {part} has leading zero"
    
    def test_version_reasonable_values(self):
        """Test version has reasonable values"""
        major, minor, patch = map(int, __version__.split('.'))
        
        # Reasonable bounds for version numbers
        assert 0 <= major <= 100, "Major version out of reasonable range"
        assert 0 <= minor <= 999, "Minor version out of reasonable range"  
        assert 0 <= patch <= 9999, "Patch version out of reasonable range"
    
    def test_author_email_consistency(self):
        """Test author and email are consistent"""
        # Email domain should match expected pattern
        assert "watkinslabs.com" in __email__
        
        # Author name should be consistent
        assert "Chris" in __author__
        assert "Watkins" in __author__
    
    def test_description_quality(self):
        """Test description is high quality"""
        desc = __description__.lower()
        
        # Should contain relevant keywords
        relevant_keywords = ['speech', 'dictation', 'voice', 'text', 'transcription', 'audio']
        assert any(keyword in desc for keyword in relevant_keywords)
        
        # Should not have obvious typos or issues
        assert '  ' not in __description__  # No double spaces
        assert __description__[0].isupper()  # Starts with capital
        assert not __description__.endswith('.')  # Description, not sentence