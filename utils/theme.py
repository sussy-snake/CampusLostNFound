"""
utils/theme.py
──────────────
Reusable UI helpers that implement the Glassmorphism look on top of
CustomTkinter widgets.

GlassmorphicFrame  — a CTkFrame that draws its own rounded border via
                     a Canvas underlay, giving it a "glass card" look.
GlowButton         — a CTkButton pre-styled with the accent glow palette.
SectionLabel       — bold white section heading.
FieldLabel         — small dim caption above entry fields.
make_gradient_bg   — builds a Pillow PhotoImage gradient for the root window.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from config import GLASS, FONT, CORNER_RADIUS, BTN_CORNER, BG_TOP, BG_BOTTOM


# ── Background Gradient ────────────────────────────────────────────────────────

def make_gradient_image(width: int, height: int) -> Image.Image:
    """
    Create a vertical linear gradient Image from BG_TOP → BG_BOTTOM.
    Stars / noise are added for a space-like campus night feel.
    """
    import random
    img = Image.new("RGB", (width, height))
    pix = img.load()

    r1, g1, b1 = BG_TOP
    r2, g2, b2 = BG_BOTTOM
    for y in range(height):
        t = y / max(height - 1, 1)
        pix[0, y]  # just ensure access
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        for x in range(width):
            pix[x, y] = (r, g, b)

    # Add subtle star specks
    rng = random.Random(42)
    for _ in range(200):
        sx = rng.randint(0, width  - 1)
        sy = rng.randint(0, height - 1)
        brightness = rng.randint(120, 220)
        pix[sx, sy] = (brightness, brightness, min(brightness + 40, 255))

    return img


def apply_gradient_bg(root: ctk.CTk | ctk.CTkToplevel, canvas: tk.Canvas):
    """Draw the gradient on *canvas* and redraw on window resize."""
    _img_ref = []  # keeps reference alive

    def _draw(event=None):
        w = canvas.winfo_width()  or root.winfo_width()
        h = canvas.winfo_height() or root.winfo_height()
        if w < 2 or h < 2:
            return
        img  = make_gradient_image(w, h)
        photo = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, anchor="nw", image=photo, tags="bg")
        canvas.tag_lower("bg")
        _img_ref.clear()
        _img_ref.append(photo)        # prevent GC

    canvas.bind("<Configure>", lambda e: _draw())
    root.after(50, _draw)             # first paint after layout pass


# ── Glass Card Frame ───────────────────────────────────────────────────────────

class GlassmorphicFrame(ctk.CTkFrame):
    """
    A CustomTkinter frame styled to look like a frosted-glass card:
    • dark semi-transparent fill
    • rounded corners provided by CTkFrame
    • a subtle accent-coloured border
    """

    def __init__(self, master, border_color=None, **kwargs):
        kwargs.setdefault("fg_color",      GLASS["fill"])
        kwargs.setdefault("corner_radius", CORNER_RADIUS)
        kwargs.setdefault("border_width",  1)
        kwargs.setdefault("border_color",  border_color or GLASS["border"])
        super().__init__(master, **kwargs)


# ── Glow Button ───────────────────────────────────────────────────────────────

class GlowButton(ctk.CTkButton):
    """
    Pre-styled accent button with a glowing hover effect simulated via
    hover_color / text_color options.
    """

    def __init__(self, master, text="", command=None,
                 width=180, height=42, is_danger=False,
                 is_secondary=False, **kwargs):

        if is_danger:
            fg, hover = GLASS["danger"], "#c0392b"
        elif is_secondary:
            fg, hover = GLASS["fill_hover"], GLASS["sidebar_hover"]
        else:
            fg, hover = GLASS["accent"], GLASS["accent_glow"]

        kwargs.setdefault("fg_color",         fg)
        kwargs.setdefault("hover_color",      hover)
        kwargs.setdefault("text_color",       GLASS["text_bright"])
        kwargs.setdefault("font",             FONT["label"])
        kwargs.setdefault("corner_radius",    BTN_CORNER)
        kwargs.setdefault("border_width",     1)
        kwargs.setdefault("border_color",     GLASS["border_accent"])
        # Pop width/height from kwargs to avoid duplicate-kwarg error
        # (callers may also pass them explicitly via **kwargs)
        kwargs.pop("width",  None)
        kwargs.pop("height", None)
        super().__init__(master, text=text, command=command,
                         width=width, height=height, **kwargs)


# ── Typography Helpers ─────────────────────────────────────────────────────────

class SectionLabel(ctk.CTkLabel):
    """Bold white section heading."""

    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("font",       FONT["heading"])
        kwargs.setdefault("text_color", GLASS["text_bright"])
        super().__init__(master, text=text, **kwargs)


class FieldLabel(ctk.CTkLabel):
    """Small dim label above an entry widget."""

    def __init__(self, master, text="", **kwargs):
        kwargs.setdefault("font",       FONT["small"])
        kwargs.setdefault("text_color", GLASS["text_dim"])
        super().__init__(master, text=text, **kwargs)


class GlassEntry(ctk.CTkEntry):
    """Entry pre-styled with dark background and accent border."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color",        GLASS["input_bg"])
        kwargs.setdefault("border_color",    GLASS["input_border"])
        kwargs.setdefault("text_color",      GLASS["text"])
        kwargs.setdefault("placeholder_text_color", GLASS["text_dim"])
        kwargs.setdefault("font",            FONT["body"])
        kwargs.setdefault("corner_radius",   8)
        kwargs.setdefault("border_width",    1)
        super().__init__(master, **kwargs)


class GlassTextbox(ctk.CTkTextbox):
    """Multi-line textbox pre-styled to match glass palette."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color",     GLASS["input_bg"])
        kwargs.setdefault("border_color", GLASS["input_border"])
        kwargs.setdefault("text_color",   GLASS["text"])
        kwargs.setdefault("font",         FONT["body"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", 8)
        super().__init__(master, **kwargs)


# ── Notification Badge ─────────────────────────────────────────────────────────

class NotifBadge(tk.Label):
    """
    A small red circle badge for showing unread notification count,
    placed over the sidebar button with .place().
    """

    def __init__(self, master, count: int = 0, **kwargs):
        super().__init__(
            master,
            text=str(count),
            bg=GLASS["danger"],
            fg="white",
            font=("Segoe UI", 8, "bold"),
            padx=3, pady=0,
            relief="flat",
            **kwargs,
        )

    def update_count(self, count: int):
        self.configure(text=str(count))
        if count > 0:
            self.place(relx=0.85, rely=0.1)
        else:
            self.place_forget()


# ── Toast Notification Popup ───────────────────────────────────────────────────

class Toast:
    """
    A temporary floating banner that auto-dismisses after `duration_ms`.
    Call Toast.show(parent, message) anywhere.
    """

    @staticmethod
    def show(parent, message: str, kind: str = "info", duration_ms: int = 3000):
        color_map = {
            "info":    GLASS["info"],
            "success": GLASS["success"],
            "warning": GLASS["warning"],
            "error":   GLASS["danger"],
        }
        color = color_map.get(kind, GLASS["accent"])

        top = tk.Toplevel(parent)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        top.configure(bg=color)

        lbl = tk.Label(
            top, text=f"  {message}  ",
            bg=color, fg="white",
            font=FONT["body"], padx=10, pady=8,
            wraplength=380,
        )
        lbl.pack()

        # Position bottom-right of parent
        parent.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        top.update_idletasks()
        tw = top.winfo_reqwidth()
        th = top.winfo_reqheight()
        x  = px + pw - tw - 20
        y  = py + ph - th - 20
        top.geometry(f"+{x}+{y}")

        parent.after(duration_ms, top.destroy)


# ── Status Timeline Widget ─────────────────────────────────────────────────────

class StatusTimeline(tk.Canvas):
    """
    Draws a horizontal step-timeline for an item's lifecycle.

    Steps: Reported → Match Found → In Negotiation → Returned
    *active_step* is 0-indexed.
    """
    STEP_W  = 160
    HEIGHT  = 80
    CIRCLE  = 18

    def __init__(self, master, steps: list[tuple[str, str]],
                 active_step: int = 0, **kwargs):
        total_w = max(self.STEP_W * len(steps), 500)
        # Pop height/width from kwargs to avoid duplicate-kwarg error
        # when callers pass height= explicitly
        h = kwargs.pop("height", self.HEIGHT)
        w = kwargs.pop("width",  total_w)
        kwargs.setdefault("bg",             GLASS["fill"])
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(master, width=w, height=h, **kwargs)
        self._steps  = steps
        self._active = active_step
        self.bind("<Configure>", self._draw)
        self.after(50, self._draw)

    def _draw(self, event=None):
        self.delete("all")
        n       = len(self._steps)
        w       = self.winfo_width()  or self.STEP_W * n
        h       = self.HEIGHT
        step_w  = w / n
        cy      = h // 2 - 8
        r       = self.CIRCLE

        # Connector line
        x0 = step_w / 2
        x1 = w - step_w / 2
        self.create_line(x0, cy, x1, cy, fill=GLASS["border"], width=2)

        for i, (label, icon) in enumerate(self._steps):
            cx = step_w / 2 + i * step_w
            done    = i <  self._active
            current = i == self._active
            fill    = (GLASS["success"]  if done else
                       GLASS["accent"]   if current else
                       GLASS["input_bg"])
            outline = GLASS["accent_glow"] if current else GLASS["border"]

            self.create_oval(cx-r, cy-r, cx+r, cy+r,
                             fill=fill, outline=outline, width=2)
            self.create_text(cx, cy, text=icon,
                             font=("Segoe UI Emoji", 11), fill="white")
            self.create_text(cx, cy + r + 12, text=label,
                             font=FONT["caption"],
                             fill=GLASS["text_bright"] if (done or current)
                                  else GLASS["text_dim"],
                             width=step_w - 10, justify="center")

    def set_step(self, active_step: int):
        self._active = active_step
        self._draw()
