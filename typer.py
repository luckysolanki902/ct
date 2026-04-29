"""Typer: type sync.txt content when cursor touches bottom-right corner.

Controls:
- Move cursor to bottom-right corner to start typing.
- After 3 seconds of typing, moving cursor to bottom-right again stops typing.
"""
import os
import time
import traceback

from common import setup_logger

log = setup_logger("typer")

CORNER_THRESHOLD_PX = 25
POLL_INTERVAL = 0.05
STOP_GUARD_SECONDS = 3.0


def _read_sync_text() -> str:
    local_path = os.path.join(os.path.dirname(__file__), "sync.txt")
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"sync.txt not found at {local_path}")
    with open(local_path, "r", encoding="utf-8") as f:
        return f.read()


def _in_bottom_right(x: int, y: int, screen_w: int, screen_h: int) -> bool:
    return (x >= screen_w - 1 - CORNER_THRESHOLD_PX) and (y >= screen_h - 1 - CORNER_THRESHOLD_PX)


def _type_with_stop(text: str, pyautogui, screen_w: int, screen_h: int) -> bool:
    started = time.monotonic()
    typed = 0

    for ch in text:
        pyautogui.write(ch, interval=0)
        typed += 1

        if time.monotonic() - started >= STOP_GUARD_SECONDS:
            p = pyautogui.position()
            if _in_bottom_right(int(p.x), int(p.y), screen_w, screen_h):
                log.info("Stop trigger detected after %.1fs. Typed %d chars.", STOP_GUARD_SECONDS, typed)
                return False

    log.info("Completed typing %d chars.", typed)
    return True


def run():
    try:
        import pyautogui
    except Exception as e:
        log.error("pyautogui import failed: %s", e)
        return

    try:
        text = _read_sync_text()
    except Exception as e:
        log.error("Failed to load sync text: %s", e)
        return

    if not text:
        log.warning("sync.txt is empty. Nothing to type.")
        return

    # Disable pyautogui's top-left failsafe; we use custom bottom-right triggers.
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    try:
        screen_w, screen_h = pyautogui.size()
    except Exception as e:
        log.error("Failed to read screen size: %s", e)
        return

    log.info(
        "Typer ready. Move cursor to bottom-right to start. "
        "After %.1fs of typing, move to bottom-right again to stop. Ctrl+C to exit.",
        STOP_GUARD_SECONDS,
    )

    armed = True
    while True:
        try:
            p = pyautogui.position()
            x, y = int(p.x), int(p.y)
            in_corner = _in_bottom_right(x, y, screen_w, screen_h)

            if not in_corner:
                armed = True
            elif in_corner and armed:
                log.info("Start trigger at (%d,%d). Typing sync.txt...", x, y)
                _type_with_stop(text, pyautogui, screen_w, screen_h)
                armed = False

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            log.info("Stopping typer (Ctrl+C).")
            return
        except Exception as e:
            log.error("Loop error: %s\n%s", e, traceback.format_exc())
            time.sleep(0.5)


if __name__ == "__main__":
    run()
