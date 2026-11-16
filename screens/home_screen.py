"""
screens/home_screen.py
──────────────────────
HomeScreen — the first screen the user sees.
Displays the project title, animated glowing subtitle, and the team-
members card, plus an "Enter the Portal" button that fires the
app-controller's navigate callback.
"""

import tkinter as tk
import customtkinter as ctk
from utils.theme import (
    GlassmorphicFrame, GlowButton, SectionLabel, FieldLabel
)
from config import GLASS, FONT, TEAM_MEMBERS, CORNER_RADIUS


class HomeScreen(ctk.CTkFrame):
    """
    Full-window home/splash frame.

    Parameters
    ----------
    master      : parent widget (the main app canvas container)
    on_enter    : callback invoked when the user clicks "Enter the Portal"
    """

    def __init__(self, master, on_enter=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.on_enter = on_enter
        self._glow_alpha = 0
        self._glow_dir   = 1          # +1 growing, -1 shrinking
        self._build_ui()
        self.after(300, self._start_glow)

    # ── Build UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Center-column layout via grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Outer centering wrapper
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0)

        # ── Project Title ──────────────────────────────────────────────────────
        title_lbl = ctk.CTkLabel(
            center,
            text="🎓 Campus Lost & Found",
            font=("Segoe UI", 42, "bold"),
            text_color=GLASS["text_bright"],
        )
        title_lbl.pack(pady=(0, 4))

        subtitle_lbl = ctk.CTkLabel(
            center,
            text="Your smart campus item recovery system",
            font=FONT["body"],
            text_color=GLASS["text_dim"],
        )
        subtitle_lbl.pack(pady=(0, 36))

        # ── Team Members Card ──────────────────────────────────────────────────
        card = GlassmorphicFrame(
            center,
            border_color=GLASS["border_accent"],
            width=460,
        )
        card.pack(pady=(0, 36), ipadx=20, ipady=16)

        team_title = ctk.CTkLabel(
            card,
            text="👥  Project Team",
            font=FONT["heading"],
            text_color=GLASS["accent_glow"],
        )
        team_title.pack(pady=(12, 10))

        separator = ctk.CTkFrame(card, height=1,
                                 fg_color=GLASS["border"], corner_radius=0)
        separator.pack(fill="x", padx=24, pady=(0, 12))

        for name, reg in TEAM_MEMBERS:
            row_frame = ctk.CTkFrame(card, fg_color="transparent")
            row_frame.pack(fill="x", padx=24, pady=4)

            ctk.CTkLabel(
                row_frame,
                text=f"  {name}",
                font=FONT["body"],
                text_color=GLASS["text"],
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                row_frame,
                text=reg,
                font=FONT["mono"],
                text_color=GLASS["text_dim"],
                anchor="e",
            ).pack(side="right")

        separator2 = ctk.CTkFrame(card, height=1,
                                  fg_color=GLASS["border"], corner_radius=0)
        separator2.pack(fill="x", padx=24, pady=(12, 8))

        ctk.CTkLabel(
            card,
            text="SRM Institute of Science and Technology",
            font=FONT["caption"],
            text_color=GLASS["text_dim"],
        ).pack(pady=(0, 12))

        # ── Enter Portal Button ────────────────────────────────────────────────
        self.enter_btn = GlowButton(
            center,
            text="✨  Enter the Portal",
            command=self._on_enter_clicked,
            width=240, height=52,
        )
        self.enter_btn.pack(pady=(0, 20))

        self.hint_lbl = ctk.CTkLabel(
            center,
            text="Click above to login or register",
            font=FONT["caption"],
            text_color=GLASS["text_dim"],
        )
        self.hint_lbl.pack()

    # ── Pulsing Glow Animation ─────────────────────────────────────────────────

    def _start_glow(self):
        """Oscillate the button border colour to simulate a glow pulse."""
        self._animate_glow()

    def _animate_glow(self):
        """Cycle border_color between accent and accent_glow."""
        self._glow_alpha += self._glow_dir * 0.05
        if self._glow_alpha >= 1.0:
            self._glow_alpha = 1.0
            self._glow_dir   = -1
        elif self._glow_alpha <= 0.0:
            self._glow_alpha = 0.0
            self._glow_dir   = 1

        # Interpolate between two colours
        c = _lerp_color(GLASS["accent"], GLASS["accent_glow"], self._glow_alpha)
        try:
            self.enter_btn.configure(border_color=c)
        except Exception:
            pass
        self.after(40, self._animate_glow)

    # ── Callback ───────────────────────────────────────────────────────────────

    def _on_enter_clicked(self):
        if callable(self.on_enter):
            self.on_enter()


# ── Colour Interpolation Helper ────────────────────────────────────────────────

def _lerp_color(hex_a: str, hex_b: str, t: float) -> str:
    """Linear interpolation between two hex colours."""
    ra, ga, ba = _hex_to_rgb(hex_a)
    rb, gb, bb = _hex_to_rgb(hex_b)
    r = int(ra + (rb - ra) * t)
    g = int(ga + (gb - ga) * t)
    b = int(ba + (bb - ba) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
