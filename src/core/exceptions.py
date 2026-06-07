"""Custom exceptions"""

class MediaStreamAnalyzerError(Exception):
    """Base exception"""
    pass

class InputError(MediaStreamAnalyzerError):
    """Input-related error"""
    pass

class SRTConnectionError(InputError):
    """SRT connection error"""
    pass

class AnalyzerError(MediaStreamAnalyzerError):
    """Analyzer-related error"""
    pass

class APIError(MediaStreamAnalyzerError):
    """API-related error"""
    pass
