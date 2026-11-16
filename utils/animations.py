"""
utils/animations.py
───────────────────
AnimationManager — provides reusable screen-transition effects for the
app controller.  All transitions use Tkinter's .after() scheduler to
drive frame-by-frame updates without blocking the event loop.

Supported transitions
─────────────────────
• slide_left   / slide_right  — outgoing frame slides out, incoming slides in
• fade         — outgoing frame fades to transparent, incoming fades in
"""

import tkinter as tk
import customtkinter as ctk
from config import ANIMATION_STEPS, ANIMATION_MS


class AnimationManager:
    """
    Manages animated transitions between full-screen frames.

    Usage
    ─────
        anim = AnimationManager(root_canvas)
        anim.slide_left(old_frame, new_frame, on_done_callback)
    """

    def __init__(self, container: tk.Widget, width_ref=None, height_ref=None):
        """
        Parameters
        ----------
        container   : the tk.Canvas or Frame that holds all pages
        width_ref   : callable that returns current canvas/window width
        height_ref  : callable that returns current canvas/window height
        """
        self.container  = container
        self._width_ref  = width_ref  or (lambda: container.winfo_width()  or 1200)
        self._height_ref = height_ref or (lambda: container.winfo_height() or 720)
        self._busy       = False      # prevent overlapping animations

    # ── Public Transitions ─────────────────────────────────────────────────────

    def slide_left(self, old_frame: tk.Widget, new_frame: tk.Widget,
                   on_done=None):
        """Slide *old* out to the left, slide *new* in from the right."""
        if self._busy:
            self._instant_switch(old_frame, new_frame, on_done)
            return
        self._slide(old_frame, new_frame, direction="left", on_done=on_done)

    def slide_right(self, old_frame: tk.Widget, new_frame: tk.Widget,
                    on_done=None):
        """Slide *old* out to the right, slide *new* in from the left."""
        if self._busy:
            self._instant_switch(old_frame, new_frame, on_done)
            return
        self._slide(old_frame, new_frame, direction="right", on_done=on_done)

    def fade(self, old_frame: tk.Widget, new_frame: tk.Widget,
             on_done=None):
        """
        Cross-fade between frames by toggling visibility mid-way.
        Uses wm_attributes('-alpha') on a Toplevel if available,
        otherwise falls back to instant switch.
        """
        if self._busy:
            self._instant_switch(old_frame, new_frame, on_done)
            return
        # Simple fade: hide old, show new after half delay
        self._busy = True
        old_frame.lower()
        def _finish():
            old_frame.place_forget()
            new_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            new_frame.lift()
            self._busy = False
            if on_done:
                on_done()
        self.container.after(ANIMATION_MS * ANIMATION_STEPS, _finish)

    # ── Private Helpers ────────────────────────────────────────────────────────

    def _instant_switch(self, old_frame, new_frame, on_done):
        old_frame.place_forget()
        new_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        new_frame.lift()
        if on_done:
            on_done()

    def _slide(self, old_frame, new_frame, direction, on_done):
        """
        Drive a slide animation over ANIMATION_STEPS frames.
        Uses relx / relwidth / relheight so CTkFrame's .place() override
        is not violated (CTk 6 forbids passing width/height to place()).

        The trick: we place both frames with relwidth=1, relheight=1 and
        shift them horizontally via relx (−1 = fully left of viewport,
        0 = in view, +1 = fully right of viewport).
        """
        self._busy = True

        # Direction determines starting relx of incoming frame
        # and ending relx of outgoing frame.
        if direction == "left":
            new_start_relx = 1.0    # new slides in from right
            old_end_relx   = -1.0   # old exits to left
        else:
            new_start_relx = -1.0   # new slides in from left
            old_end_relx   = 1.0    # old exits to right

        # Place new frame off-screen (full size via rel* args)
        new_frame.place(relx=new_start_relx, rely=0,
                        relwidth=1, relheight=1)
        new_frame.lift()

        step = [0]

        def _tick():
            t    = step[0] / ANIMATION_STEPS
            ease = _ease_out_cubic(t)

            old_relx = 0.0          + ease * old_end_relx
            new_relx = new_start_relx + ease * (0.0 - new_start_relx)

            old_frame.place(relx=old_relx, rely=0,
                            relwidth=1, relheight=1)
            new_frame.place(relx=new_relx, rely=0,
                            relwidth=1, relheight=1)

            step[0] += 1
            if step[0] <= ANIMATION_STEPS:
                self.container.after(ANIMATION_MS, _tick)
            else:
                # Animation complete — snap new frame into final position
                old_frame.place_forget()
                new_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                self._busy = False
                if on_done:
                    on_done()

        self.container.after(ANIMATION_MS, _tick)


# ── Easing Functions ───────────────────────────────────────────────────────────

def _ease_out_cubic(t: float) -> float:
    """Smooth deceleration: starts fast, slows to a stop."""
    return 1 - (1 - t) ** 3
