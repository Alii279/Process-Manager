"""
Squish test suite for ProcessTab — kill Discord button.

Run from Squish IDE:  right-click tst_kill_process > Run Test Case
Run from CLI:
    squishrunner --testsuite suite_sysmanager --testcase tst_kill_process
"""

import os
import sys
import squishtest as st
from squish import (
    findObject,
    waitForObject,
    clickButton,
    waitForObjectItem,
    snooze,
    test,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_button():
    """Return the killDiscordButton widget, waiting up to 5 s for it."""
    return waitForObject(":killDiscordButton", 5000)


def get_status_label():
    """Return the statusLabel widget."""
    return waitForObject(":statusLabel", 5000)


def wait_for_status_change(initial_text: str, timeout_ms: int = 6000):
    """
    Block until statusLabel text differs from initial_text.
    Used to wait for the background QThread to finish.
    """
    import time
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        label = get_status_label()
        if label.text != initial_text:
            return label.text
        snooze(0.2)
    return get_status_label().text


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_window_appears():
    """
    Verify the main window and the Processes tab are visible on startup.
    This is a smoke test!
    """
    window = waitForObject(":MainWindow", 5000)
    test.verify(window.visible, "MainWindow should be visible")

    tab_widget = waitForObject(":tabWidget", 5000)
    test.compare(tab_widget.currentIndex, 0, "Processes tab should be selected by default")


def test_kill_discord_button_exists():
    """
    Verify the kill button is present, enabled, and correctly labelled.
    Checks that objectName wiring works end-to-end.
    """
    btn = get_button()
    test.verify(btn.visible, "Kill button should be visible")
    test.verify(btn.enabled, "Kill button should be enabled before clicking")
    test.compare(btn.text, "Close Discord", "Button label should match spec")


def test_kill_discord_when_not_running():
    """
    Click the kill button when Discord is NOT running.
    Expected: status label reports 'not found' — not an unhandled crash.

    This test is safe to run on any machine regardless of whether Discord
    is installed, because we expect a graceful 'not found' result.
    """
    # Precondition: Discord is not running on the CI/test machine.
    # If Discord happens to be running, this test should be skipped manually.

    btn = get_button()
    initial_status = get_status_label().text

    clickButton(btn)

    # Button should be disabled while the worker thread runs.
    test.verify(not btn.enabled, "Button should be disabled during operation")

    # Wait for the worker thread to complete and status to update.
    final_status = wait_for_status_change(initial_status)

    # After completion, button must be re-enabled.
    test.verify(btn.enabled, "Button should be re-enabled after operation completes")

    # Status must contain some meaningful feedback — not be empty.
    test.verify(len(final_status) > 0, "Status label should not be empty after operation")

    # When Discord is not running, we expect a 'Not found' message.
    test.verify(
        "Not found" in final_status or "not running" in final_status.lower(),
        f"Status should indicate Discord was not found, got: '{final_status}'"
    )


def test_kill_discord_button_resets_after_use():
    """
    Verify the button returns to 'Close Discord' text after completing.
    Regression guard: early versions left the button stuck on 'Closing…'.
    """
    btn = get_button()
    clickButton(btn)

    # Wait for operation to finish.
    snooze(3)

    test.compare(btn.text, "Close Discord", "Button text should reset after operation")
    test.verify(btn.enabled, "Button should be clickable again after operation")


def test_status_label_clears_on_reuse():
    """
    Click the button twice in sequence.
    The status label from the first click should be replaced by the second.
    Ensures there's no stale state between operations.
    """
    btn = get_button()

    # First click
    clickButton(btn)
    snooze(3)
    first_status = get_status_label().text

    # Second click
    clickButton(btn)
    snooze(3)
    second_status = get_status_label().text

    # Both statuses should be non-empty and equal (same expected outcome).
    test.verify(len(second_status) > 0, "Status should be set after second click")
    test.compare(
        first_status, second_status,
        "Repeated kills of a non-running process should produce the same status"
    )


# ---------------------------------------------------------------------------
# Squish entry point
# ---------------------------------------------------------------------------

def main():
    """
    Squish calls main() automatically.
    List test cases in the order they should run.
    Squish will report each one individually in its results view.
    """
    test_window_appears()
    test_kill_discord_button_exists()
    test_kill_discord_when_not_running()
    test_kill_discord_button_resets_after_use()
    test_status_label_clears_on_reuse()