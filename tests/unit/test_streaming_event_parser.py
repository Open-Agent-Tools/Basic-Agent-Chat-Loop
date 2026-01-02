"""Tests for StreamingEventParser component."""

from basic_agent_chat_loop.components.streaming_event_parser import (
    StreamingEventParser,
)


class TestStreamingEventParserBasic:
    """Test basic event parsing functionality."""

    def test_parse_string_event(self):
        """Test parsing when event is a plain string."""
        parser = StreamingEventParser()
        result = parser.parse_event("Hello, world!")
        assert result == "Hello, world!"

    def test_parse_empty_string_event(self):
        """Test parsing empty string event."""
        parser = StreamingEventParser()
        result = parser.parse_event("")
        assert result == ""

    def test_parse_none_event(self):
        """Test parsing None event returns None."""
        parser = StreamingEventParser()
        result = parser.parse_event(None)
        assert result is None

    def test_parse_unknown_object_returns_none(self):
        """Test parsing unknown object type returns None."""
        parser = StreamingEventParser()

        class UnknownEvent:
            pass

        result = parser.parse_event(UnknownEvent())
        assert result is None


class TestAwsStrandsDictFormat:
    """Test AWS Strands dictionary format events."""

    def test_parse_aws_strands_nested_dict(self):
        """Test parsing AWS Strands nested dictionary format."""
        parser = StreamingEventParser()
        event = {
            "event": {"contentBlockDelta": {"delta": {"text": "AWS Strands text"}}}
        }
        result = parser.parse_event(event)
        assert result == "AWS Strands text"

    def test_parse_aws_strands_missing_text(self):
        """Test AWS Strands format with missing text field."""
        parser = StreamingEventParser()
        event = {"event": {"contentBlockDelta": {"delta": {}}}}
        result = parser.parse_event(event)
        assert result is None

    def test_parse_aws_strands_missing_delta(self):
        """Test AWS Strands format with missing delta field."""
        parser = StreamingEventParser()
        event = {"event": {"contentBlockDelta": {}}}
        result = parser.parse_event(event)
        assert result is None

    def test_parse_aws_strands_missing_content_block(self):
        """Test AWS Strands format with missing contentBlockDelta."""
        parser = StreamingEventParser()
        event = {"event": {}}
        result = parser.parse_event(event)
        assert result is None

    def test_parse_aws_strands_non_dict_delta(self):
        """Test AWS Strands format with non-dict delta."""
        parser = StreamingEventParser()
        event = {"event": {"contentBlockDelta": {"delta": "not a dict"}}}
        result = parser.parse_event(event)
        assert result is None


class TestSimpleDictFormat:
    """Test simple dictionary format events."""

    def test_parse_simple_text_dict(self):
        """Test parsing simple dict with text field."""
        parser = StreamingEventParser()
        event = {"text": "Simple text"}
        result = parser.parse_event(event)
        assert result == "Simple text"

    def test_parse_dict_without_text(self):
        """Test parsing dict without text field."""
        parser = StreamingEventParser()
        event = {"other_field": "value"}
        result = parser.parse_event(event)
        assert result is None

    def test_parse_empty_dict(self):
        """Test parsing empty dictionary."""
        parser = StreamingEventParser()
        result = parser.parse_event({})
        assert result is None


class TestDataAttributeEvents:
    """Test events with data attribute."""

    def test_parse_data_string(self):
        """Test parsing event with string data attribute."""
        parser = StreamingEventParser()

        class Event:
            data = "Data string"

        result = parser.parse_event(Event())
        assert result == "Data string"

    def test_parse_data_dict_with_text(self):
        """Test parsing event with dict data containing text."""
        parser = StreamingEventParser()

        class Event:
            data = {"text": "Text in data dict"}

        result = parser.parse_event(Event())
        assert result == "Text in data dict"

    def test_parse_data_dict_with_content_list(self):
        """Test parsing event with content list in data dict."""
        parser = StreamingEventParser()

        class Event:
            data = {"content": [{"text": "First block"}, {"other": "Second block"}]}

        result = parser.parse_event(Event())
        assert result == "First block"

    def test_parse_data_dict_with_content_string(self):
        """Test parsing event with content string in data dict."""
        parser = StreamingEventParser()

        class Event:
            data = {"content": "Direct content"}

        result = parser.parse_event(Event())
        assert result == "Direct content"

    def test_parse_data_dict_with_content_list_no_text(self):
        """Test parsing content list with no text blocks."""
        parser = StreamingEventParser()

        class Event:
            data = {"content": [{"other": "No text here"}]}

        result = parser.parse_event(Event())
        assert result is None

    def test_parse_data_dict_empty(self):
        """Test parsing event with empty dict data."""
        parser = StreamingEventParser()

        class Event:
            data = {}

        result = parser.parse_event(Event())
        assert result is None


class TestDeltaAttributeEvents:
    """Test events with delta attribute (Anthropic/AWS Strands objects)."""

    def test_parse_delta_string(self):
        """Test parsing event with string delta."""
        parser = StreamingEventParser()

        class Event:
            delta = "Delta text"

        result = parser.parse_event(Event())
        assert result == "Delta text"

    def test_parse_delta_object_with_text_attribute(self):
        """Test parsing event with delta object containing text attribute."""
        parser = StreamingEventParser()

        class Delta:
            text = "Text attribute"

        class Event:
            delta = Delta()

        result = parser.parse_event(Event())
        assert result == "Text attribute"

    def test_parse_delta_dict_with_text(self):
        """Test parsing event with delta dict containing text."""
        parser = StreamingEventParser()

        class Event:
            delta = {"text": "Text in delta dict"}

        result = parser.parse_event(Event())
        assert result == "Text in delta dict"

    def test_parse_delta_dict_without_text(self):
        """Test parsing delta dict without text field."""
        parser = StreamingEventParser()

        class Event:
            delta = {"other": "No text"}

        result = parser.parse_event(Event())
        assert result is None

    def test_parse_delta_object_without_text(self):
        """Test parsing delta object without text attribute."""
        parser = StreamingEventParser()

        class Delta:
            other = "No text"

        class Event:
            delta = Delta()

        result = parser.parse_event(Event())
        assert result is None


class TestTextAttributeEvents:
    """Test events with direct text attribute."""

    def test_parse_text_attribute(self):
        """Test parsing event with direct text attribute."""
        parser = StreamingEventParser()

        class Event:
            text = "Direct text attribute"

        result = parser.parse_event(Event())
        assert result == "Direct text attribute"

    def test_parse_text_attribute_empty(self):
        """Test parsing event with empty text attribute."""
        parser = StreamingEventParser()

        class Event:
            text = ""

        result = parser.parse_event(Event())
        assert result == ""


class TestParsingPriority:
    """Test that parsing follows correct priority order."""

    def test_dict_takes_priority_over_attributes(self):
        """Test that dict parsing is checked before object attributes."""
        parser = StreamingEventParser()
        # This is a dict, so it should use dict parsing even if
        # it looks like it has attributes
        event = {"text": "Dict text", "data": "Should not be used"}
        result = parser.parse_event(event)
        assert result == "Dict text"

    def test_data_attribute_priority_over_delta(self):
        """Test that data attribute is checked before delta."""
        parser = StreamingEventParser()

        class Event:
            data = "Data text"
            delta = "Delta text"

        result = parser.parse_event(Event())
        assert result == "Data text"

    def test_delta_attribute_priority_over_text(self):
        """Test that delta attribute is checked before text."""
        parser = StreamingEventParser()

        class Event:
            delta = "Delta text"
            text = "Text attribute"

        result = parser.parse_event(Event())
        assert result == "Delta text"


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_parse_integer_event(self):
        """Test parsing integer event returns None."""
        parser = StreamingEventParser()
        result = parser.parse_event(123)
        assert result is None

    def test_parse_list_event(self):
        """Test parsing list event returns None."""
        parser = StreamingEventParser()
        result = parser.parse_event([1, 2, 3])
        assert result is None

    def test_parse_unicode_text(self):
        """Test parsing Unicode text."""
        parser = StreamingEventParser()
        result = parser.parse_event("Hello 世界 🌍")
        assert result == "Hello 世界 🌍"

    def test_parse_multiline_text(self):
        """Test parsing multiline text."""
        parser = StreamingEventParser()
        text = "Line 1\nLine 2\nLine 3"
        result = parser.parse_event(text)
        assert result == text

    def test_parse_very_long_text(self):
        """Test parsing very long text."""
        parser = StreamingEventParser()
        text = "A" * 10000
        result = parser.parse_event(text)
        assert result == text
        assert len(result) == 10000
