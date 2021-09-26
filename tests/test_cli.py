"""Tests the clap.cli module."""

from clap.cli import main


def test_main() -> None:
    """Tests main() function."""
    assert main([""]) == 0
