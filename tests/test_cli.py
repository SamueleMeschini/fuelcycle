"""Tests for the command-line entry point."""

from openfc.cli import main


def test_info_command(capsys) -> None:
    assert main(["info"]) == 0
    assert "OpenFC" in capsys.readouterr().out
