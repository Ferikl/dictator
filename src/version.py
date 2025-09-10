#!/usr/bin/env python3
"""
Version information for DICTATOR
"""

__version__ = "1.0.2"
__author__ = "Chris Watkins"
__email__ = "chris@watkinslabs.com"
__description__ = "Real-time speech-to-text dictation app with floating Qt interface"

def get_version_info():
    """Get formatted version information"""
    return {
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'description': __description__
    }

def get_version_string():
    """Get version as string"""
    return __version__