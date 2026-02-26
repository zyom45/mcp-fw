"""PyObjC-based log viewer window for mcp-fw."""

from __future__ import annotations

import os
from pathlib import Path

import AppKit
import Foundation

from mcp_fw.menubar.i18n import t


class LogViewerWindow:
    """NSWindow-based log viewer with auto-scrolling tail."""

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir
        self._window: AppKit.NSWindow | None = None
        self._text_view: AppKit.NSTextView | None = None
        self._timer: Foundation.NSTimer | None = None
        self._file_positions: dict[str, int] = {}

    def show(self) -> None:
        if self._window is not None and self._window.isVisible():
            self._window.makeKeyAndOrderFront_(None)
            return

        # Window frame
        frame = Foundation.NSMakeRect(200, 200, 800, 500)
        style = (
            AppKit.NSTitledWindowMask
            | AppKit.NSClosableWindowMask
            | AppKit.NSResizableWindowMask
            | AppKit.NSMiniaturizableWindowMask
        )
        self._window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self._window.setTitle_(t("log_window_title"))
        self._window.setReleasedWhenClosed_(False)

        # Scroll view + text view
        scroll_view = AppKit.NSScrollView.alloc().initWithFrame_(
            self._window.contentView().bounds()
        )
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable
        )

        content_size = scroll_view.contentSize()
        self._text_view = AppKit.NSTextView.alloc().initWithFrame_(
            Foundation.NSMakeRect(0, 0, content_size.width, content_size.height)
        )
        self._text_view.setEditable_(False)
        self._text_view.setFont_(
            AppKit.NSFont.monospacedSystemFontOfSize_weight_(11, AppKit.NSFontWeightRegular)
        )
        self._text_view.setAutoresizingMask_(AppKit.NSViewWidthSizable)
        self._text_view.textContainer().setWidthTracksTextView_(False)
        self._text_view.textContainer().setContainerSize_(
            Foundation.NSMakeSize(1e7, 1e7)
        )
        self._text_view.setHorizontallyResizable_(True)

        scroll_view.setDocumentView_(self._text_view)
        self._window.contentView().addSubview_(scroll_view)
        self._window.makeKeyAndOrderFront_(None)

        # Load initial content
        self._file_positions.clear()
        self._poll_logs()

        # Start 1-second polling timer
        self._timer = Foundation.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, "_pollTick:", None, True
        )

    def _pollTick_(self, timer: Foundation.NSTimer) -> None:  # noqa: N802
        self._poll_logs()

    def _poll_logs(self) -> None:
        if self._text_view is None:
            return

        if not self.log_dir.exists():
            return

        new_text = []
        for log_file in sorted(self.log_dir.glob("*.log")):
            try:
                size = log_file.stat().st_size
                prev = self._file_positions.get(str(log_file), 0)
                if size <= prev:
                    continue

                with open(log_file) as f:
                    f.seek(prev)
                    chunk = f.read()
                    if chunk:
                        new_text.append(chunk)
                    self._file_positions[str(log_file)] = f.tell()
            except OSError:
                continue

        if new_text:
            combined = "".join(new_text)
            storage = self._text_view.textStorage()
            attr_str = AppKit.NSAttributedString.alloc().initWithString_attributes_(
                combined,
                {
                    AppKit.NSFontAttributeName: AppKit.NSFont.monospacedSystemFontOfSize_weight_(
                        11, AppKit.NSFontWeightRegular
                    ),
                },
            )
            storage.appendAttributedString_(attr_str)

            # Auto-scroll to bottom
            self._text_view.scrollRangeToVisible_(
                Foundation.NSMakeRange(storage.length(), 0)
            )

    def close(self) -> None:
        if self._timer:
            self._timer.invalidate()
            self._timer = None
        if self._window:
            self._window.close()
            self._window = None
