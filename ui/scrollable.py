"""
ui/scrollable.py

Shared scrollable container used by every module screen. Build your
widgets inside .body instead of directly on the Frame passed to your
class, and the whole screen becomes scrollable BOTH vertically and
horizontally - needed whenever content is taller or wider than the
visible window (e.g. 200+ students, or a window that's smaller than
expected on a particular screen).
"""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        self.body = ttk.Frame(canvas)

        self.body.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # If the visible area is WIDER than the content needs, stretch
        # the body to fill it (so fill="x" widgets look normal). If the
        # content is wider than the visible area, leave the body at its
        # natural width so horizontal scrolling actually has something
        # to scroll to, instead of clipping content.
        def _resize_body(event):
            content_width = self.body.winfo_reqwidth()
            if content_width < event.width:
                canvas.itemconfig(canvas_window, width=event.width)
            else:
                canvas.itemconfig(canvas_window, width=content_width)
        canvas.bind("<Configure>", _resize_body)

        # Grid layout so both scrollbars fit alongside the canvas
        # cleanly, without fighting pack().
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)

        def _unbind_wheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Shift-MouseWheel>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)