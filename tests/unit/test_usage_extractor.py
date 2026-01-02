"""Tests for UsageExtractor component."""

from basic_agent_chat_loop.components.usage_extractor import UsageExtractor


class TestTokenExtractionBasic:
    """Test basic token usage extraction."""

    def test_extract_none_response(self):
        """Test extraction from None response."""
        extractor = UsageExtractor()
        result = extractor.extract_token_usage(None)
        assert result is None

    def test_extract_empty_dict(self):
        """Test extraction from empty dict."""
        extractor = UsageExtractor()
        result = extractor.extract_token_usage({})
        assert result is None

    def test_extract_empty_object(self):
        """Test extraction from object without usage."""
        extractor = UsageExtractor()

        class EmptyResponse:
            pass

        result = extractor.extract_token_usage(EmptyResponse())
        assert result is None


class TestBedrockAccumulatedUsage:
    """Test AWS Bedrock accumulated usage extraction."""

    def test_extract_bedrock_accumulated_usage(self):
        """Test extraction from Bedrock accumulated usage."""
        extractor = UsageExtractor()

        class AccumulatedUsage:
            inputTokens = 100
            outputTokens = 50

        class Metrics:
            accumulated_usage = AccumulatedUsage()

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 100, "output_tokens": 50}
        assert is_accumulated is True

    def test_extract_bedrock_dict_usage(self):
        """Test extraction from Bedrock dict format."""
        extractor = UsageExtractor()

        class Metrics:
            accumulated_usage = {"inputTokens": 200, "outputTokens": 100}

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 200, "output_tokens": 100}
        assert is_accumulated is True

    def test_extract_bedrock_missing_metrics(self):
        """Test Bedrock response without metrics."""
        extractor = UsageExtractor()

        class Result:
            pass

        response = {"result": Result()}
        result = extractor.extract_token_usage(response)
        assert result is None

    def test_extract_bedrock_missing_accumulated_usage(self):
        """Test Bedrock response without accumulated_usage."""
        extractor = UsageExtractor()

        class Metrics:
            pass

        class Result:
            metrics = Metrics()

        response = {"result": Result()}
        result = extractor.extract_token_usage(response)
        assert result is None


class TestAnthropicStyleUsage:
    """Test Anthropic/Claude style usage extraction."""

    def test_extract_anthropic_usage_object(self):
        """Test extraction from object with usage attribute."""
        extractor = UsageExtractor()

        class Usage:
            input_tokens = 150
            output_tokens = 75

        class Response:
            usage = Usage()

        result = extractor.extract_token_usage(Response())
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 150, "output_tokens": 75}
        assert is_accumulated is False

    def test_extract_anthropic_usage_dict(self):
        """Test extraction from dict style usage."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": 250, "output_tokens": 125}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 250, "output_tokens": 125}
        assert is_accumulated is False


class TestOpenAIStyleUsage:
    """Test OpenAI style usage extraction (prompt_tokens/completion_tokens)."""

    def test_extract_openai_prompt_completion_tokens_object(self):
        """Test extraction from OpenAI style object."""
        extractor = UsageExtractor()

        class Usage:
            prompt_tokens = 300
            completion_tokens = 150

        class Response:
            usage = Usage()

        result = extractor.extract_token_usage(Response())
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 300, "output_tokens": 150}
        assert is_accumulated is False

    def test_extract_openai_prompt_completion_tokens_dict(self):
        """Test extraction from OpenAI style dict."""
        extractor = UsageExtractor()

        response = {"usage": {"prompt_tokens": 400, "completion_tokens": 200}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 400, "output_tokens": 200}
        assert is_accumulated is False


class TestMetadataUsage:
    """Test usage extraction from metadata."""

    def test_extract_metadata_usage(self):
        """Test extraction from response.metadata.usage."""
        extractor = UsageExtractor()

        class Usage:
            input_tokens = 100
            output_tokens = 50

        class Metadata:
            usage = Usage()

        class Response:
            metadata = Metadata()

        result = extractor.extract_token_usage(Response())
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 100, "output_tokens": 50}
        assert is_accumulated is False


class TestStreamingEventUsage:
    """Test usage extraction from streaming events."""

    def test_extract_streaming_event_data_usage_object(self):
        """Test extraction from streaming event with data.usage."""
        extractor = UsageExtractor()

        class Usage:
            input_tokens = 80
            output_tokens = 40

        class Data:
            usage = Usage()

        class Event:
            data = Data()

        result = extractor.extract_token_usage(Event())
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 80, "output_tokens": 40}
        assert is_accumulated is False

    def test_extract_streaming_event_data_usage_dict(self):
        """Test extraction from streaming event with data['usage']."""
        extractor = UsageExtractor()

        class Data:
            pass

        class Event:
            data = {"usage": {"input_tokens": 120, "output_tokens": 60}}

        result = extractor.extract_token_usage(Event())
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 120, "output_tokens": 60}
        assert is_accumulated is False


class TestTokenFieldVariations:
    """Test different token field name variations."""

    def test_extract_mixed_field_names(self):
        """Test extraction with mixed field names (inputTokens vs output_tokens)."""
        extractor = UsageExtractor()

        # Bedrock uses camelCase, others use snake_case
        response = {"usage": {"inputTokens": 100, "output_tokens": 50}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 100, "output_tokens": 50}
        assert is_accumulated is False

    def test_extract_with_zero_tokens(self):
        """Test extraction when tokens are zero."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": 0, "output_tokens": 0}}

        result = extractor.extract_token_usage(response)
        # Should return None when all tokens are zero
        assert result is None

    def test_extract_with_only_input_tokens(self):
        """Test extraction with only input tokens."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": 100, "output_tokens": 0}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 100, "output_tokens": 0}

    def test_extract_with_only_output_tokens(self):
        """Test extraction with only output tokens."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": 0, "output_tokens": 75}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 0, "output_tokens": 75}


class TestInvalidTokenValues:
    """Test handling of invalid token values."""

    def test_extract_with_none_tokens(self):
        """Test extraction when token values are None."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": None, "output_tokens": None}}

        result = extractor.extract_token_usage(response)
        assert result is None

    def test_extract_with_string_tokens(self):
        """Test extraction when token values are strings."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": "100", "output_tokens": "50"}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 100, "output_tokens": 50}

    def test_extract_with_invalid_token_types(self):
        """Test extraction when token values cannot be converted to int."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": "invalid", "output_tokens": []}}

        result = extractor.extract_token_usage(response)
        assert result is None


class TestCycleCountExtraction:
    """Test cycle count extraction."""

    def test_extract_cycle_count_valid(self):
        """Test extraction of cycle count from metrics."""
        extractor = UsageExtractor()

        class Metrics:
            cycle_count = 5

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        cycle_count = extractor.extract_cycle_count(response)
        assert cycle_count == 5

    def test_extract_cycle_count_missing_result(self):
        """Test cycle count extraction when result is missing."""
        extractor = UsageExtractor()

        response = {}
        cycle_count = extractor.extract_cycle_count(response)
        assert cycle_count is None

    def test_extract_cycle_count_missing_metrics(self):
        """Test cycle count extraction when metrics is missing."""
        extractor = UsageExtractor()

        class Result:
            pass

        response = {"result": Result()}

        cycle_count = extractor.extract_cycle_count(response)
        assert cycle_count is None

    def test_extract_cycle_count_missing_cycle_count(self):
        """Test cycle count extraction when cycle_count is missing."""
        extractor = UsageExtractor()

        class Metrics:
            pass

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        cycle_count = extractor.extract_cycle_count(response)
        assert cycle_count is None

    def test_extract_cycle_count_non_dict_response(self):
        """Test cycle count extraction from non-dict response."""
        extractor = UsageExtractor()

        class Response:
            pass

        cycle_count = extractor.extract_cycle_count(Response())
        assert cycle_count is None


class TestToolCountExtraction:
    """Test tool usage count extraction."""

    def test_extract_tool_count_dict_format(self):
        """Test extraction from dict format tool_metrics."""
        extractor = UsageExtractor()

        class Metrics:
            tool_metrics = {
                "tool1": ["call1", "call2", "call3"],
                "tool2": ["call1"],
                "tool3": ["call1", "call2"],
            }

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count == 6  # 3 + 1 + 2

    def test_extract_tool_count_list_format(self):
        """Test extraction from list format tool_metrics."""
        extractor = UsageExtractor()

        class Metrics:
            tool_metrics = ["call1", "call2", "call3", "call4"]

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count == 4

    def test_extract_tool_count_object_format(self):
        """Test extraction from object format tool_metrics."""
        extractor = UsageExtractor()

        class ToolMetrics:
            tool1 = "call1"
            tool2 = "call2"
            _private = "should_ignore"

        class Metrics:
            tool_metrics = ToolMetrics()

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count == 2  # Only non-private attributes

    def test_extract_tool_count_empty_dict(self):
        """Test extraction when tool_metrics is empty dict."""
        extractor = UsageExtractor()

        class Metrics:
            tool_metrics = {}

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count is None  # Empty tool_metrics returns None

    def test_extract_tool_count_none(self):
        """Test extraction when tool_metrics is None."""
        extractor = UsageExtractor()

        class Metrics:
            tool_metrics = None

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count is None

    def test_extract_tool_count_missing_metrics(self):
        """Test extraction when metrics is missing."""
        extractor = UsageExtractor()

        class Result:
            pass

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count is None

    def test_extract_tool_count_missing_tool_metrics(self):
        """Test extraction when tool_metrics is missing."""
        extractor = UsageExtractor()

        class Metrics:
            pass

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count is None

    def test_extract_tool_count_exception_handling(self):
        """Test that exceptions during extraction are handled gracefully."""
        extractor = UsageExtractor()

        class BrokenToolMetrics:
            def __len__(self):
                raise RuntimeError("Broken length")

        class Metrics:
            tool_metrics = BrokenToolMetrics()

        class Result:
            metrics = Metrics()

        response = {"result": Result()}

        tool_count = extractor.extract_tool_count(response)
        assert tool_count is None


class TestExtractorPriority:
    """Test extraction priority order."""

    def test_bedrock_takes_priority_over_standard(self):
        """Test that Bedrock accumulated usage is tried first."""
        extractor = UsageExtractor()

        class AccumulatedUsage:
            inputTokens = 100
            outputTokens = 50

        class Metrics:
            accumulated_usage = AccumulatedUsage()

        class Result:
            metrics = Metrics()

        # Response has both Bedrock and standard usage
        response = {
            "result": Result(),
            "usage": {"input_tokens": 999, "output_tokens": 999},
        }

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        # Should use Bedrock values, not standard
        assert usage_dict == {"input_tokens": 100, "output_tokens": 50}
        assert is_accumulated is True


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_extract_with_float_tokens(self):
        """Test extraction with float token values."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": 100.7, "output_tokens": 50.3}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        # Should convert floats to ints
        assert usage_dict == {"input_tokens": 100, "output_tokens": 50}

    def test_extract_with_large_token_counts(self):
        """Test extraction with very large token counts."""
        extractor = UsageExtractor()

        response = {"usage": {"input_tokens": 1000000, "output_tokens": 500000}}

        result = extractor.extract_token_usage(response)
        assert result is not None
        usage_dict, is_accumulated = result
        assert usage_dict == {"input_tokens": 1000000, "output_tokens": 500000}

    def test_extract_multiple_calls_independent(self):
        """Test that multiple extraction calls are independent."""
        extractor = UsageExtractor()

        response1 = {"usage": {"input_tokens": 100, "output_tokens": 50}}
        response2 = {"usage": {"input_tokens": 200, "output_tokens": 100}}

        result1 = extractor.extract_token_usage(response1)
        result2 = extractor.extract_token_usage(response2)

        assert result1 is not None
        assert result2 is not None
        usage1, _ = result1
        usage2, _ = result2
        assert usage1 == {"input_tokens": 100, "output_tokens": 50}
        assert usage2 == {"input_tokens": 200, "output_tokens": 100}
