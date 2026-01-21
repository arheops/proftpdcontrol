import pytest

from ftpmanager.templatetags.ftpmanager_tags import get_item


class TestGetItemFilter:
    """Tests for get_item template filter"""

    def test_get_item_existing_key(self):
        """Test getting an existing key from dictionary"""
        d = {'foo': 'bar', 'baz': 123}
        assert get_item(d, 'foo') == 'bar'
        assert get_item(d, 'baz') == 123

    def test_get_item_missing_key(self):
        """Test getting a missing key returns None"""
        d = {'foo': 'bar'}
        assert get_item(d, 'missing') is None

    def test_get_item_none_dictionary(self):
        """Test with None dictionary returns None"""
        assert get_item(None, 'any_key') is None

    def test_get_item_empty_dictionary(self):
        """Test with empty dictionary returns None"""
        d = {}
        assert get_item(d, 'key') is None

    def test_get_item_various_types(self):
        """Test with various value types"""
        d = {
            'string': 'hello',
            'number': 42,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'none': None,
            'bool': True,
        }
        assert get_item(d, 'string') == 'hello'
        assert get_item(d, 'number') == 42
        assert get_item(d, 'list') == [1, 2, 3]
        assert get_item(d, 'dict') == {'nested': 'value'}
        assert get_item(d, 'none') is None
        assert get_item(d, 'bool') is True

    def test_get_item_integer_key(self):
        """Test with integer key"""
        d = {1: 'one', 2: 'two'}
        assert get_item(d, 1) == 'one'
        assert get_item(d, 2) == 'two'

    def test_get_item_mixed_keys(self):
        """Test dictionary with mixed key types"""
        d = {'string_key': 'string_value', 123: 'int_value'}
        assert get_item(d, 'string_key') == 'string_value'
        assert get_item(d, 123) == 'int_value'
