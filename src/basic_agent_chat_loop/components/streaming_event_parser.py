"""Streaming event parser for extracting text from various agent response formats.

Handles multiple streaming event formats from different agent frameworks:
- AWS Strands (dict and object formats)
- Anthropic API
- OpenAI-compatible APIs
- Generic streaming formats
"""

from typing import Any, Optional


class StreamingEventParser:
    """Parser for extracting text from streaming agent response events.

    Supports multiple event formats and structures to provide a unified
    interface for text extraction from various agent frameworks.
    """

    def parse_event(self, event: Any) -> Optional[str]:
        """Extract text from a streaming event.

        Args:
            event: A streaming event from an agent. Can be:
                - dict: AWS Strands format or simple text dict
                - object with attributes: Anthropic/OpenAI format
                - str: Direct text event

        Returns:
            Extracted text string, or None if no text found

        Examples:
            >>> parser = StreamingEventParser()
            >>>
            >>> # AWS Strands nested dict format
            >>> event = {'event': {'contentBlockDelta': {'delta': {'text': 'Hello'}}}}
            >>> parser.parse_event(event)
            'Hello'
            >>>
            >>> # Simple text dict
            >>> event = {'text': 'World'}
            >>> parser.parse_event(event)
            'World'
            >>>
            >>> # String event
            >>> parser.parse_event('Direct text')
            'Direct text'
        """
        # First check if event is a dict (AWS Strands format)
        if isinstance(event, dict):
            return self._parse_dict_event(event)

        # Check for object with data attribute
        if hasattr(event, "data"):
            return self._parse_data_attribute(event.data)

        # Check for object with delta attribute (AWS Strands/Anthropic objects)
        if hasattr(event, "delta"):
            return self._parse_delta_attribute(event.delta)

        # Check for direct text attribute
        if hasattr(event, "text"):
            return event.text

        # Event is the text itself
        if isinstance(event, str):
            return event

        return None

    def _parse_dict_event(self, event: dict) -> Optional[str]:
        """Parse dictionary-format events (AWS Strands, simple dicts).

        Args:
            event: Dictionary event to parse

        Returns:
            Extracted text or None
        """
        # AWS Strands nested dict format:
        # {'event': {'contentBlockDelta': {'delta': {'text': '...'}}}}
        if "event" in event and isinstance(event["event"], dict):
            nested_event = event["event"]
            if "contentBlockDelta" in nested_event:
                delta_block = nested_event["contentBlockDelta"]
                if isinstance(delta_block, dict) and "delta" in delta_block:
                    delta = delta_block["delta"]
                    if isinstance(delta, dict) and "text" in delta:
                        return delta["text"]

        # Fallback: check for direct text field
        if "text" in event:
            return event["text"]

        return None

    def _parse_data_attribute(self, data: Any) -> Optional[str]:
        """Parse events with a 'data' attribute.

        Args:
            data: The data attribute from an event object

        Returns:
            Extracted text or None
        """
        # String data
        if isinstance(data, str):
            return data

        # Dictionary data
        if isinstance(data, dict):
            # Direct text field
            if "text" in data:
                return data["text"]

            # Content field with blocks
            if "content" in data:
                content = data["content"]
                if isinstance(content, list):
                    # Find first block with text
                    for block in content:
                        if isinstance(block, dict) and "text" in block:
                            return block["text"]
                else:
                    return str(content)

        return None

    def _parse_delta_attribute(self, delta: Any) -> Optional[str]:
        """Parse events with a 'delta' attribute (AWS Strands/Anthropic objects).

        Args:
            delta: The delta attribute from an event object

        Returns:
            Extracted text or None
        """
        # String delta
        if isinstance(delta, str):
            return delta

        # Object with text attribute
        if hasattr(delta, "text"):
            return delta.text

        # Dictionary delta with text
        if isinstance(delta, dict) and "text" in delta:
            return delta["text"]

        return None
