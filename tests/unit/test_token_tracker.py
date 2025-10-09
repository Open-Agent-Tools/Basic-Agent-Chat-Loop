"""Tests for TokenTracker component."""
import pytest
from basic_agent_chat_loop.components.token_tracker import TokenTracker


def test_token_tracker_initialization():
    """Test TokenTracker initializes correctly."""
    tracker = TokenTracker("Claude Sonnet 4.5")
    assert tracker.model_name == "Claude Sonnet 4.5"
    assert tracker.total_input_tokens == 0
    assert tracker.total_output_tokens == 0


def test_add_usage():
    """Test adding token usage."""
    tracker = TokenTracker("Claude Sonnet 4.5")
    tracker.add_usage(100, 50)
    assert tracker.total_input_tokens == 100
    assert tracker.total_output_tokens == 50
    assert tracker.get_total_tokens() == 150


def test_cost_calculation():
    """Test cost calculation for known model."""
    tracker = TokenTracker("Claude Sonnet 4.5")
    tracker.add_usage(1_000_000, 1_000_000)  # 1M tokens each
    cost = tracker.get_cost()
    assert cost == 18.0  # $3 input + $15 output


def test_format_tokens():
    """Test token formatting with K/M suffixes."""
    tracker = TokenTracker()
    assert tracker.format_tokens(500) == "500"
    assert tracker.format_tokens(1_500) == "1.5K"
    assert tracker.format_tokens(2_500_000) == "2.5M"
