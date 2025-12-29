"""Tests for AudioNotifier component."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from basic_agent_chat_loop.components.audio_notifier import AudioNotifier


@pytest.fixture
def temp_wav_file(tmp_path):
    """Create a temporary WAV file for testing."""
    wav_file = tmp_path / "test_notification.wav"
    wav_file.write_bytes(b"RIFF" + b"\x00" * 40)  # Minimal WAV header
    return wav_file


@pytest.fixture
def mock_notification_wav(tmp_path, monkeypatch):
    """Mock the bundled notification.wav file location."""
    # Create a fake module directory structure
    fake_module_dir = tmp_path / "basic_agent_chat_loop"
    fake_module_dir.mkdir(parents=True)
    fake_components_dir = fake_module_dir / "components"
    fake_components_dir.mkdir()

    # Create the notification.wav file
    wav_file = fake_module_dir / "notification.wav"
    wav_file.write_bytes(b"RIFF" + b"\x00" * 40)

    # Mock Path(__file__).parent.parent to return our fake structure
    with patch("basic_agent_chat_loop.components.audio_notifier.Path") as mock_path:
        mock_file = MagicMock()
        mock_file.parent.parent = fake_module_dir
        mock_path.return_value = mock_file
        mock_path.side_effect = lambda x: Path(x) if isinstance(x, str) else mock_file
        yield fake_module_dir


class TestAudioNotifierInitialization:
    """Test AudioNotifier initialization."""

    def test_initialization_enabled_by_default(self, temp_wav_file):
        """Test that audio is enabled by default."""
        notifier = AudioNotifier(sound_file=str(temp_wav_file))
        assert notifier.enabled is True

    def test_initialization_can_be_disabled(self, temp_wav_file):
        """Test that audio can be disabled during initialization."""
        notifier = AudioNotifier(enabled=False, sound_file=str(temp_wav_file))
        assert notifier.enabled is False

    def test_initialization_with_custom_sound_file(self, temp_wav_file):
        """Test initialization with custom sound file path."""
        notifier = AudioNotifier(sound_file=str(temp_wav_file))
        assert notifier.sound_file == temp_wav_file
        assert notifier.enabled is True

    def test_initialization_with_nonexistent_file_disables_audio(
        self, tmp_path, capsys
    ):
        """Test that nonexistent sound file disables audio and prints warning."""
        nonexistent_file = tmp_path / "nonexistent.wav"
        notifier = AudioNotifier(sound_file=str(nonexistent_file))

        assert notifier.enabled is False
        captured = capsys.readouterr()
        assert "Warning: Audio file not found" in captured.out
        assert str(nonexistent_file) in captured.out

    def test_initialization_detects_platform(self, temp_wav_file):
        """Test that platform is detected during initialization."""
        notifier = AudioNotifier(sound_file=str(temp_wav_file))
        assert notifier.system in ["Darwin", "Linux", "Windows", "Java"]


class TestAudioNotifierPlayMacOS:
    """Test AudioNotifier.play() on macOS."""

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    @patch("basic_agent_chat_loop.components.audio_notifier.subprocess.run")
    def test_play_on_macos_success(self, mock_run, mock_platform, temp_wav_file):
        """Test successful audio playback on macOS."""
        mock_platform.return_value = "Darwin"
        notifier = AudioNotifier(sound_file=str(temp_wav_file))

        result = notifier.play()

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["afplay", str(temp_wav_file)]
        assert call_args[1]["check"] is False

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    def test_play_on_macos_returns_false_when_disabled(
        self, mock_platform, temp_wav_file
    ):
        """Test that play returns False when audio is disabled."""
        mock_platform.return_value = "Darwin"
        notifier = AudioNotifier(enabled=False, sound_file=str(temp_wav_file))

        result = notifier.play()

        assert result is False

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    @patch("basic_agent_chat_loop.components.audio_notifier.subprocess.run")
    def test_play_on_macos_handles_exception(
        self, mock_run, mock_platform, temp_wav_file
    ):
        """Test that exceptions during playback are handled gracefully."""
        mock_platform.return_value = "Darwin"
        mock_run.side_effect = Exception("Playback failed")
        notifier = AudioNotifier(sound_file=str(temp_wav_file))

        result = notifier.play()

        assert result is False


class TestAudioNotifierPlayLinux:
    """Test AudioNotifier.play() on Linux."""

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    @patch("basic_agent_chat_loop.components.audio_notifier.subprocess.run")
    def test_play_on_linux_with_aplay(self, mock_run, mock_platform, temp_wav_file):
        """Test successful audio playback on Linux with aplay."""
        mock_platform.return_value = "Linux"
        notifier = AudioNotifier(sound_file=str(temp_wav_file))

        result = notifier.play()

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["aplay", str(temp_wav_file)]

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    @patch("basic_agent_chat_loop.components.audio_notifier.subprocess.run")
    def test_play_on_linux_falls_back_to_paplay(
        self, mock_run, mock_platform, temp_wav_file
    ):
        """Test that Linux falls back to paplay if aplay fails."""
        mock_platform.return_value = "Linux"

        # First call (aplay) raises FileNotFoundError, second call (paplay) succeeds
        mock_run.side_effect = [FileNotFoundError(), None]
        notifier = AudioNotifier(sound_file=str(temp_wav_file))

        result = notifier.play()

        assert result is True
        assert mock_run.call_count == 2
        # Check first call was aplay
        assert mock_run.call_args_list[0][0][0] == ["aplay", str(temp_wav_file)]
        # Check second call was paplay
        assert mock_run.call_args_list[1][0][0] == ["paplay", str(temp_wav_file)]

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    @patch("basic_agent_chat_loop.components.audio_notifier.subprocess.run")
    def test_play_on_linux_returns_false_when_both_commands_missing(
        self, mock_run, mock_platform, temp_wav_file
    ):
        """Test that play returns False when both aplay and paplay are missing."""
        mock_platform.return_value = "Linux"
        mock_run.side_effect = FileNotFoundError()
        notifier = AudioNotifier(sound_file=str(temp_wav_file))

        result = notifier.play()

        assert result is False
        assert mock_run.call_count == 2  # Tried both aplay and paplay


class TestAudioNotifierPlayWindows:
    """Test AudioNotifier.play() on Windows."""

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    def test_play_on_windows_success(self, mock_platform, temp_wav_file):
        """Test successful audio playback on Windows."""
        mock_platform.return_value = "Windows"

        # Mock the winsound module
        mock_winsound = MagicMock()
        mock_winsound.SND_FILENAME = 0x00020000
        mock_winsound.SND_ASYNC = 0x0001

        with patch.dict("sys.modules", {"winsound": mock_winsound}):
            notifier = AudioNotifier(sound_file=str(temp_wav_file))
            result = notifier.play()

            assert result is True
            mock_winsound.PlaySound.assert_called_once()

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    def test_play_on_windows_handles_exception(self, mock_platform, temp_wav_file):
        """Test that Windows playback handles exceptions gracefully."""
        mock_platform.return_value = "Windows"

        # Mock winsound to raise an exception
        mock_winsound = MagicMock()
        mock_winsound.PlaySound.side_effect = Exception("Playback failed")
        mock_winsound.SND_FILENAME = 0x00020000
        mock_winsound.SND_ASYNC = 0x0001

        with patch.dict("sys.modules", {"winsound": mock_winsound}):
            notifier = AudioNotifier(sound_file=str(temp_wav_file))
            result = notifier.play()

            assert result is False


class TestAudioNotifierUnsupportedPlatform:
    """Test AudioNotifier on unsupported platforms."""

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    def test_play_on_unsupported_platform_returns_false(
        self, mock_platform, temp_wav_file
    ):
        """Test that play returns False on unsupported platforms."""
        mock_platform.return_value = "UnknownOS"
        notifier = AudioNotifier(sound_file=str(temp_wav_file))

        result = notifier.play()

        assert result is False


class TestAudioNotifierEdgeCases:
    """Test edge cases and error handling."""

    def test_play_when_disabled_does_not_attempt_playback(self, temp_wav_file):
        """Test that playback is not attempted when audio is disabled."""
        with patch(
            "basic_agent_chat_loop.components.audio_notifier.subprocess.run"
        ) as mock_run:
            notifier = AudioNotifier(enabled=False, sound_file=str(temp_wav_file))
            notifier.play()

            # subprocess.run should never be called
            mock_run.assert_not_called()

    def test_sound_file_path_conversion(self, temp_wav_file):
        """Test that sound file path is converted to Path object."""
        notifier = AudioNotifier(sound_file=str(temp_wav_file))
        assert isinstance(notifier.sound_file, Path)
        assert notifier.sound_file == temp_wav_file

    @patch("basic_agent_chat_loop.components.audio_notifier.platform.system")
    @patch("basic_agent_chat_loop.components.audio_notifier.subprocess.run")
    def test_subprocess_uses_devnull_for_output(
        self, mock_run, mock_platform, temp_wav_file
    ):
        """Test that subprocess output is redirected to DEVNULL."""
        mock_platform.return_value = "Darwin"
        notifier = AudioNotifier(sound_file=str(temp_wav_file))
        notifier.play()

        call_kwargs = mock_run.call_args[1]
        # Verify output is suppressed
        assert "stdout" in call_kwargs
        assert "stderr" in call_kwargs
