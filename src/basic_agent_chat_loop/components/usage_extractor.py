"""Usage and metrics extraction from agent responses.

Handles extraction of:
- Token usage (input/output tokens) from various response formats
- Cycle count metrics (AWS Strands framework)
- Tool usage metrics (tool call counts)
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class UsageExtractor:
    """Extractor for token usage and metrics from agent responses.

    Supports multiple response formats:
    - AWS Bedrock accumulated usage (cumulative)
    - Anthropic/Claude style usage
    - OpenAI style usage
    - Framework-specific metrics (cycles, tool calls)
    """

    def extract_token_usage(
        self, response_obj: Any
    ) -> Optional[tuple[dict[str, int], bool]]:
        """Extract token usage from response object.

        Args:
            response_obj: Response object from agent

        Returns:
            Tuple of (usage_dict, is_accumulated) where:
            - usage_dict: Dict with 'input_tokens' and 'output_tokens'
            - is_accumulated: True if usage is cumulative across session
            Returns None if no usage info available
        """
        if not response_obj:
            return None

        # Try AWS Bedrock accumulated usage first (cumulative)
        if isinstance(response_obj, dict):
            bedrock_result = self._try_bedrock_token_extraction(response_obj)
            if bedrock_result:
                usage, is_accumulated = bedrock_result
                tokens = self._extract_tokens_from_usage(usage)
                if tokens:
                    return (tokens, is_accumulated)

        # Try standard usage patterns (per-request)
        usage = self._try_standard_usage_extraction(response_obj)
        if usage:
            tokens = self._extract_tokens_from_usage(usage)
            if tokens:
                return (tokens, False)

        return None

    def extract_cycle_count(self, response_obj: Any) -> Optional[int]:
        """Extract cycle count from AWS Strands framework metrics.

        Args:
            response_obj: Response object from agent

        Returns:
            Cycle count if available, None otherwise
        """
        if isinstance(response_obj, dict) and "result" in response_obj:
            result = response_obj["result"]
            if hasattr(result, "metrics") and hasattr(result.metrics, "cycle_count"):
                return result.metrics.cycle_count
        return None

    def extract_tool_count(self, response_obj: Any) -> Optional[int]:
        """Extract tool usage count from framework metrics.

        Handles multiple tool_metrics formats:
        - Dict of tool name to call list
        - List/sequence of tool calls
        - Object with tool attributes

        Args:
            response_obj: Response object from agent

        Returns:
            Total tool call count if available, None otherwise
        """
        if isinstance(response_obj, dict) and "result" in response_obj:
            result = response_obj["result"]
            if hasattr(result, "metrics") and hasattr(result.metrics, "tool_metrics"):
                metrics = result.metrics
                try:
                    # Check if tool_metrics is truthy (can raise exception)
                    if metrics.tool_metrics:
                        # Dict format: {tool_name: [call1, call2, ...]}
                        if isinstance(metrics.tool_metrics, dict):
                            return sum(
                                len(calls) for calls in metrics.tool_metrics.values()
                            )
                        # Sequence format: [call1, call2, ...]
                        elif hasattr(metrics.tool_metrics, "__len__"):
                            return len(metrics.tool_metrics)
                        # Object format: count non-private attributes
                        else:
                            # Use vars() to get both instance and class attributes
                            attrs: list[str] = []
                            # Get instance attributes
                            if hasattr(metrics.tool_metrics, "__dict__"):
                                attrs.extend(
                                    k
                                    for k in metrics.tool_metrics.__dict__.keys()
                                    if not k.startswith("_")
                                )
                            # Get class attributes
                            for cls in type(metrics.tool_metrics).__mro__:
                                if cls is object:
                                    break
                                attrs.extend(
                                    k
                                    for k in cls.__dict__.keys()
                                    if not k.startswith("_") and k not in attrs
                                )
                            return len(attrs) if attrs else None
                except Exception as e:
                    logger.debug(f"Could not extract tool count: {e}")
                    return None
        return None

    def _try_bedrock_token_extraction(
        self, response_obj: dict
    ) -> Optional[tuple[Any, bool]]:
        """Try to extract AWS Bedrock style accumulated usage.

        Args:
            response_obj: Response dict potentially containing Bedrock metrics

        Returns:
            Tuple of (usage_object, is_accumulated) or None if not found
        """
        if "result" in response_obj:
            result = response_obj["result"]
            if hasattr(result, "metrics") and hasattr(
                result.metrics, "accumulated_usage"
            ):
                return (result.metrics.accumulated_usage, True)
        return None

    def _try_standard_usage_extraction(self, response_obj: Any) -> Optional[Any]:
        """Try to extract usage from common patterns.

        Args:
            response_obj: Response object to extract from

        Returns:
            Usage object or None if not found
        """
        # Pattern 1: response.usage (Anthropic/Claude style)
        if hasattr(response_obj, "usage"):
            return response_obj.usage

        # Pattern 2: response['usage'] (dict style)
        if isinstance(response_obj, dict) and "usage" in response_obj:
            return response_obj["usage"]

        # Pattern 3: response.metadata.usage
        if hasattr(response_obj, "metadata") and hasattr(
            response_obj.metadata, "usage"
        ):
            return response_obj.metadata.usage

        # Pattern 4: response.data.usage (streaming event)
        if hasattr(response_obj, "data") and hasattr(response_obj.data, "usage"):
            return response_obj.data.usage

        # Pattern 5: response.data['usage'] (streaming event dict)
        if (
            hasattr(response_obj, "data")
            and isinstance(response_obj.data, dict)
            and "usage" in response_obj.data
        ):
            return response_obj.data["usage"]

        return None

    def _extract_tokens_from_usage(self, usage: Any) -> Optional[dict[str, int]]:
        """Extract input and output tokens from usage object.

        Args:
            usage: Usage object (dict or object with attributes)

        Returns:
            Dict with 'input_tokens' and 'output_tokens', or None if invalid
        """
        input_tokens: int = 0
        output_tokens: int = 0

        # Try different attribute names (check dict keys first, then attributes)
        if isinstance(usage, dict):
            # AWS Bedrock camelCase - explicit or chain with default
            input_tokens = (
                usage.get("inputTokens")
                or usage.get("input_tokens")
                or usage.get("prompt_tokens")
                or 0
            )
            output_tokens = (
                usage.get("outputTokens")
                or usage.get("output_tokens")
                or usage.get("completion_tokens")
                or 0
            )
        else:
            # Object attributes - try both camelCase (Bedrock) and snake_case
            input_tokens = (
                getattr(usage, "inputTokens", None)
                or getattr(usage, "input_tokens", None)
                or getattr(usage, "prompt_tokens", None)
                or 0
            )
            output_tokens = (
                getattr(usage, "outputTokens", None)
                or getattr(usage, "output_tokens", None)
                or getattr(usage, "completion_tokens", None)
                or 0
            )

        # Ensure tokens are integers (handle mocks/test objects)
        try:
            input_tokens = int(input_tokens) if input_tokens is not None else 0
            output_tokens = int(output_tokens) if output_tokens is not None else 0
        except (TypeError, ValueError):
            return None

        if input_tokens > 0 or output_tokens > 0:
            return {"input_tokens": input_tokens, "output_tokens": output_tokens}

        return None
