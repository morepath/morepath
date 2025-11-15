import pytest


def test_import_error():
    """Test that import errors are properly handled.

    This test file is specifically designed to test import error handling
    during scanning. The import statement below is expected to fail.
    """
    with pytest.raises(ImportError):
        import impossible_import_error_generating_thing_should_be_ignored  # type: ignore # noqa
