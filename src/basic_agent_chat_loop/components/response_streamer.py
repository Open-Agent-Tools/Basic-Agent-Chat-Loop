"""Response streaming component for handling agent interactions.

Manages the complete lifecycle of streaming agent responses:
- Stream/call agent with query
- Process events through parsers (event parser, harmony processor)
- Render output via ResponseRenderer
- Track metrics (tokens, duration, cycles, tools)
- Save to session state
- Play audio notifications

Extracted from chat_loop.py to reduce file size and improve modularity.
"""

import asyncio
import io
import logging
import sys
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from .response_renderer import ResponseRenderer
from .streaming_event_parser import StreamingEventParser
from .token_tracker import TokenTracker
from .usage_extractor import UsageExtractor

if TYPE_CHECKING:
    from .audio_notifier import AudioNotifier
    from .harmony_processor import HarmonyProcessor
    from .session_state import SessionState
    from .status_bar import StatusBar
    from .ui_components import Colors

logger = logging.getLogger(__name__)


def _serialize_for_logging(obj: Any) -> str:
    """Safely serialize objects for logging.

    Args:
        obj: Object to serialize

    Returns:
        String representation safe for logging
    """
    try:
        # Try direct string conversion first
        return str(obj)
    except Exception:
        return f"<{type(obj).__name__} object (non-serializable)>"


class ResponseStreamer:
    """Handles streaming agent responses and processing output.

    Coordinates multiple components to:
    - Stream responses from agent
    - Parse streaming events
    - Process through Harmony (if enabled)
    - Render to terminal
    - Track tokens and metrics
    - Save conversation history
    """

    def __init__(
        self,
        agent: Any,
        agent_name: str,
        response_renderer: ResponseRenderer,
        event_parser: StreamingEventParser,
        session_state: "SessionState",
        usage_extractor: UsageExtractor,
        token_tracker: TokenTracker,
        audio_notifier: "AudioNotifier",
        colors_module: type["Colors"],
        show_thinking: bool = True,
        show_duration: bool = True,
        show_tokens: bool = True,
        harmony_processor: Optional["HarmonyProcessor"] = None,
        status_bar: Optional["StatusBar"] = None,
        suppress_agent_stdout: bool = True,
    ):
        """Initialize the response streamer.

        Args:
            agent: The agent instance to query
            agent_name: Name of the agent for display
            response_renderer: Renderer for displaying responses
            event_parser: Parser for streaming events
            session_state: Session state for tracking conversation
            usage_extractor: Extractor for token usage from responses
            token_tracker: Tracker for cumulative token usage
            audio_notifier: Audio notification player
            colors_module: Colors class for terminal colorization
            show_thinking: Whether to show thinking indicator
            show_duration: Whether to show query duration
            show_tokens: Whether to show token usage
            harmony_processor: Optional Harmony processor for OpenAI format
            status_bar: Optional status bar for real-time updates
            suppress_agent_stdout: Whether to suppress agent library stdout during streaming
        """
        self.agent = agent
        self.agent_name = agent_name
        self.response_renderer = response_renderer
        self.event_parser = event_parser
        self.session_state = session_state
        self.usage_extractor = usage_extractor
        self.token_tracker = token_tracker
        self.audio_notifier = audio_notifier
        self.colors: type[Colors] = colors_module
        self.show_thinking = show_thinking
        self.show_duration = show_duration
        self.show_tokens = show_tokens
        self.harmony_processor = harmony_processor
        self.status_bar = status_bar
        self.suppress_agent_stdout = suppress_agent_stdout

        # Token tracking for session (matches chat_loop.py behavior)
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        logger.debug("ResponseStreamer initialized")
        logger.debug(f"  agent_name: {agent_name}")
        logger.debug(f"  show_thinking: {show_thinking}")
        logger.debug(f"  show_duration: {show_duration}")
        logger.debug(f"  show_tokens: {show_tokens}")
        logger.debug(f"  harmony: {harmony_processor is not None}")
        logger.debug(f"  status_bar: {status_bar is not None}")

    async def _show_thinking_indicator(self, stop_event: asyncio.Event) -> None:
        """Display animated thinking indicator while waiting for response.

        Args:
            stop_event: Event to signal when to stop the indicator
        """
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0

        while not stop_event.is_set():
            print(
                f"\r{self.colors.DIM}{frames[i]} Thinking...{self.colors.RESET}",
                end="",
                flush=True,
            )
            i = (i + 1) % len(frames)
            await asyncio.sleep(0.1)

        # Clear the thinking indicator line
        print("\r" + " " * 20 + "\r", end="", flush=True)

    async def stream_agent_response(
        self, query: str, save_conversation_callback: Optional[Any] = None
    ) -> dict[str, Any]:
        """Stream agent response asynchronously.

        Args:
            query: User query to send to agent
            save_conversation_callback: Optional async callback to save conversation

        Returns:
            Dict with 'duration' and optional 'usage' (input_tokens, output_tokens)
        """
        start_time = time.time()
        response_text = []  # Collect response for rich rendering
        response_obj = None  # Store the response object for token extraction

        # Render agent name header
        self.response_renderer.render_agent_header()

        # Setup thinking indicator
        stop_thinking = asyncio.Event()
        thinking_task = None

        try:
            # Start thinking indicator if enabled
            if self.show_thinking:
                thinking_task = asyncio.create_task(
                    self._show_thinking_indicator(stop_thinking)
                )

            first_token_received = False

            # Log request payload sent to agent
            logger.debug("=" * 60)
            logger.debug("REQUEST TO AGENT:")
            logger.debug(f"Query: {_serialize_for_logging(query)}")
            logger.debug("=" * 60)

            # Check if agent supports streaming
            if hasattr(self.agent, "stream_async"):
                print(f"\n[DEBUG] MAIN LOOP: Starting stream_async iteration", file=sys.stderr)

                # WORKAROUND: Suppress stdout during streaming to prevent agent libraries
                # from printing accumulated response text as a side effect
                # (Discovered in beta.8 diagnostics - text appears between event loop iterations)
                # NOTE: Suppression is only active BETWEEN iterations (during yield back to
                # stream_async). During our event processing, stdout is restored so tool calls
                # and logging work normally.
                old_stdout = None
                if self.suppress_agent_stdout:
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()

                try:
                    async for event in self.agent.stream_async(query):
                        # Restore stdout for our controlled output and logging
                        if self.suppress_agent_stdout:
                            sys.stdout = old_stdout

                        print(f"\n[DEBUG] MAIN LOOP: Received event from stream_async", file=sys.stderr)
                        # Store last event for token extraction
                        response_obj = event

                        # Log streaming event received from agent
                        logger.debug("STREAMING EVENT FROM AGENT:")
                        logger.debug(_serialize_for_logging(event))

                        # Stop thinking indicator on first token
                        if not first_token_received:
                            stop_thinking.set()
                            if thinking_task:
                                await thinking_task
                            first_token_received = True

                        # Extract text from streaming event using event parser
                        text_to_add = self.event_parser.parse_event(event)

                        # DIAGNOSTIC: Log text extraction
                        if text_to_add:
                            print(f"\n[DEBUG] STREAM LOOP: Got text chunk, length={len(text_to_add)}", file=sys.stderr)
                            print(f"[DEBUG] STREAM LOOP: About to call render_streaming_text()", file=sys.stderr)

                        # Append text if found and display it
                        if text_to_add:
                            response_text.append(text_to_add)
                            # Display streaming text (renderer handles skip logic)
                            self.response_renderer.render_streaming_text(text_to_add)
                            print(f"[DEBUG] STREAM LOOP: Returned from render_streaming_text()", file=sys.stderr)

                        print(f"[DEBUG] MAIN LOOP: End of iteration, about to yield back to stream_async", file=sys.stderr)

                        # Suppress stdout again before yielding back to stream_async
                        if self.suppress_agent_stdout:
                            sys.stdout = io.StringIO()
                finally:
                    # Always restore stdout
                    if self.suppress_agent_stdout and old_stdout is not None:
                        sys.stdout = old_stdout
            else:
                # Fallback to non-streaming call if streaming not supported
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.agent, query
                )
                response_obj = response  # Store for token extraction

                # Log response received from agent
                logger.debug("RESPONSE FROM AGENT:")
                logger.debug(_serialize_for_logging(response))
                logger.debug("=" * 60)

                # Stop thinking indicator
                stop_thinking.set()
                if thinking_task:
                    await thinking_task

                # Format and display response
                if hasattr(response, "message"):
                    message = response.message
                    if isinstance(message, dict) and "content" in message:
                        content = message["content"]
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and "text" in block:
                                    response_text.append(block["text"])
                        else:
                            response_text.append(str(content))
                    else:
                        response_text.append(str(message))
                elif isinstance(response, str):
                    response_text.append(response)
                else:
                    response_text.append(str(response))

            # Log final response object (for streaming, this is the last event)
            if hasattr(self.agent, "stream_async"):
                logger.debug("FINAL RESPONSE OBJECT (last streaming event):")
                logger.debug(_serialize_for_logging(response_obj))
                logger.debug("=" * 60)

            # Render collected response
            # Concatenate streaming chunks directly (they may break mid-word)
            full_response = "".join(response_text)

            # Track if we already printed during streaming (to prevent duplicates)
            # Use renderer's method to determine if streaming was skipped
            # (skipped means we need to print in final response)
            already_printed_streaming = (
                first_token_received
                and not self.response_renderer.should_skip_streaming_display()
            )

            # Process through Harmony if available
            display_text = full_response
            if self.harmony_processor:
                # Debug: Log response object structure
                # (safely handle mocks/test objects)
                try:
                    logger.debug(f"Response object type: {type(response_obj)}")
                    logger.debug(f"Response object attrs: {dir(response_obj)[:20]}")
                    if response_obj and hasattr(response_obj, "choices"):
                        try:
                            logger.debug(
                                f"Response has choices: {len(response_obj.choices)}"
                            )
                        except TypeError:
                            logger.debug(
                                "Response has choices attribute (non-sequence)"
                            )

                        if response_obj.choices:
                            choice = response_obj.choices[0]
                            logger.debug(f"Choice type: {type(choice)}")
                            logger.debug(f"Choice attrs: {dir(choice)[:20]}")
                            if hasattr(choice, "logprobs"):
                                logger.debug(
                                    f"Has logprobs: {choice.logprobs is not None}"
                                )
                            if hasattr(choice, "message"):
                                logger.debug(f"Message type: {type(choice.message)}")
                except Exception as e:
                    logger.debug(
                        f"Error logging response structure (safe to ignore): {e}"
                    )

                processed = self.harmony_processor.process_response(
                    full_response, metadata=response_obj
                )
                display_text = self.harmony_processor.format_for_display(processed)

                # Log if Harmony-specific features detected
                if processed.get("has_reasoning"):
                    logger.debug("Harmony response contains reasoning")
                if processed.get("has_tools"):
                    logger.debug("Harmony response contains tool calls")

            # Store last response for copy commands (what user sees)
            self.session_state.update_last_response(display_text)

            #  Render final response (only if not already printed during streaming)
            if not already_printed_streaming:
                self.response_renderer.render_final_response(
                    display_text=display_text, first_token_received=first_token_received
                )

            duration = time.time() - start_time

            # Extract token usage and metrics if available
            usage_result = self.usage_extractor.extract_token_usage(response_obj)
            cycle_count = self.usage_extractor.extract_cycle_count(response_obj)
            tool_count = self.usage_extractor.extract_tool_count(response_obj)

            # Track tokens (always, for session summary)
            usage_info = None
            if usage_result:
                usage_info, is_accumulated = usage_result

                if is_accumulated:
                    # AWS Strands accumulated_usage is cumulative across session
                    # Calculate delta from last query
                    current_input = usage_info["input_tokens"]
                    current_output = usage_info["output_tokens"]

                    (
                        delta_input,
                        delta_output,
                    ) = self.session_state.update_accumulated_usage(
                        current_input, current_output
                    )

                    # Add only the delta
                    if delta_input > 0 or delta_output > 0:
                        self.token_tracker.add_usage(delta_input, delta_output)
                else:
                    # Non-accumulated usage - add directly
                    self.token_tracker.add_usage(
                        usage_info["input_tokens"], usage_info["output_tokens"]
                    )

                # Update status bar
                if self.status_bar:
                    self.status_bar.update_tokens(self.token_tracker.get_total_tokens())

            # Display duration and token info
            # Determine what to show
            show_info_line = (
                self.show_duration
                or (self.show_tokens and usage_info)
                or cycle_count
                or tool_count
            )

            if show_info_line:
                print(f"\n{self.colors.DIM}{'-' * 60}{self.colors.RESET}")

                info_parts = []
                if self.show_duration:
                    info_parts.append(f"Time: {duration:.1f}s")

                # Show agent metrics (cycles, tools) - always show if available
                if cycle_count is not None and cycle_count > 0:
                    cycle_word = "cycle" if cycle_count == 1 else "cycles"
                    info_parts.append(f"{cycle_count} {cycle_word}")

                if tool_count is not None and tool_count > 0:
                    tool_word = "tool" if tool_count == 1 else "tools"
                    info_parts.append(f"{tool_count} {tool_word}")

                # Only show tokens if show_tokens is enabled
                if self.show_tokens and usage_info:
                    input_tok = usage_info["input_tokens"]
                    output_tok = usage_info["output_tokens"]
                    total_tok = input_tok + output_tok

                    # Format tokens
                    token_str = (
                        f"Tokens: {self.token_tracker.format_tokens(total_tok)} "
                    )
                    token_str += f"(in: {self.token_tracker.format_tokens(input_tok)}, "
                    token_str += f"out: {self.token_tracker.format_tokens(output_tok)})"
                    info_parts.append(token_str)

                if info_parts:  # Only print if we have something to show
                    print(self.colors.system(" │ ".join(info_parts)))

            logger.info(f"Query completed successfully in {duration:.1f}s")

            # Track conversation as markdown for saving
            query_num = self.session_state.increment_query_count()
            entry_timestamp = datetime.now().strftime("%H:%M:%S")

            # Build markdown entry
            md_entry = [
                f"\n## Query {query_num} ({entry_timestamp})\n",
                f"**You:** {query}\n\n",
                f"**{self.agent_name}:** {display_text}\n\n",
            ]

            # Add metadata
            metadata_parts = [f"Time: {duration:.1f}s"]
            if usage_info:
                input_tok = usage_info.get("input_tokens", 0)
                output_tok = usage_info.get("output_tokens", 0)
                total_tok = input_tok + output_tok
                self.total_input_tokens += input_tok
                self.total_output_tokens += output_tok
                if total_tok > 0:
                    tok_str = (
                        f"Tokens: {total_tok:,} "
                        f"(in: {input_tok:,}, out: {output_tok:,})"
                    )
                    metadata_parts.append(tok_str)

            md_entry.append(f"*{' | '.join(metadata_parts)}*\n\n")
            md_entry.append("---\n")

            self.session_state.conversation_markdown.extend(md_entry)

            # Save conversation incrementally after each query-response
            if save_conversation_callback:
                await save_conversation_callback()

            # Play audio notification on agent turn completion
            self.audio_notifier.play()

            return {"duration": duration, "usage": usage_info}

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n{self.colors.DIM}{'-' * 60}{self.colors.RESET}")
            print(self.colors.error(f"{self.agent_name}: Query failed - {e}"))
            print(
                self.colors.system(
                    "Try rephrasing your question or check the logs for details."
                )
            )
            logger.error(
                f"Agent query failed after {duration:.1f}s: {e}", exc_info=True
            )

            return {"duration": duration, "usage": None}

        finally:
            # Always cleanup thinking indicator, even on KeyboardInterrupt
            stop_thinking.set()
            if thinking_task and not thinking_task.done():
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling
