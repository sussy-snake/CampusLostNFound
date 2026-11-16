"""
screens/notifications_screen.py
────────────────────────────────
NotificationsScreen — shows unread/read in-app notifications.
Each notification has a "Connect with Finder" button that opens ChatScreen.
"""

import tkinter as tk
import customtkinter as ctk
from utils.theme import GlassmorphicFrame, GlowButton, SectionLabel, Toast
from config import GLASS, FONT


class NotificationsScreen(ctk.CTkFrame):
    """
    Lists all notifications for *current_user*.

    Parameters
    ----------
    on_open_chat(match_id, finder_id)  : callback to open the ChatScreen
    on_back                            : callback to go back to portal
    """

    def __init__(self, master, current_user: dict, db,
                 on_open_chat=None, on_back=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.current_user = current_user
        self.db           = db
        self.on_open_chat = on_open_chat
        self.on_back      = on_back
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 8))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            hdr, text="← Back",
            command=self.on_back,
            fg_color="transparent", hover_color=GLASS["sidebar_hover"],
            text_color=GLASS["text_dim"], font=FONT["small"],
            width=80, height=28,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            hdr, text="🔔  Notifications",
            font=FONT["title"], text_color=GLASS["text_bright"],
        ).grid(row=0, column=1, sticky="w", padx=12)

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=GLASS["border"],
            scrollbar_button_hover_color=GLASS["accent"],
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.scroll.grid_columnconfigure(0, weight=1)

        self._load()
        self.db.mark_notifications_read(self.current_user["user_id"])

    def _load(self):
        """Fetch and render all notifications."""
        for w in self.scroll.winfo_children():
            w.destroy()

        notifs = self.db.get_notifications(self.current_user["user_id"])

        if not notifs:
            ctk.CTkLabel(
                self.scroll,
                text="🎉  You're all caught up!\n\nNo notifications yet.",
                font=FONT["body"], text_color=GLASS["text_dim"],
                justify="center",
            ).pack(pady=60)
            return

        for n in notifs:
            self._render_notif(n)

    def _render_notif(self, n: dict):
        is_new = not n["is_read"]
        border = GLASS["accent"] if is_new else GLASS["border"]

        card = GlassmorphicFrame(self.scroll, border_color=border)
        card.pack(fill="x", padx=8, pady=6, ipadx=12, ipady=10)
        card.grid_columnconfigure(0, weight=1)

        # Timestamp + unread dot
        ts_row = ctk.CTkFrame(card, fg_color="transparent")
        ts_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 2))

        if is_new:
            ctk.CTkLabel(ts_row, text="● NEW",
                         font=FONT["caption"],
                         text_color=GLASS["accent"]).pack(side="left")

        ctk.CTkLabel(
            ts_row,
            text=n.get("created_at", "")[:16],
            font=FONT["caption"], text_color=GLASS["text_dim"],
        ).pack(side="right")

        # Message text
        ctk.CTkLabel(
            card,
            text=n["message"],
            font=FONT["body"], text_color=GLASS["text"],
            wraplength=520, justify="left", anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(4, 10))

        # "Connect with Finder" button — only if match_id exists
        if n.get("match_id"):
            match_id = n["match_id"]
            match    = self.db.get_match_by_id(match_id)
            if match:
                finder_id = self._get_finder_id(match)
                GlowButton(
                    card,
                    text="💬  Connect with Finder",
                    command=lambda mid=match_id, fid=finder_id:
                        self._open_chat(mid, fid),
                    width=200, height=36,
                ).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 10))

                # Resolve button
                ctk.CTkButton(
                    card,
                    text="✅  Mark Resolved",
                    command=lambda mid=match_id, c=card: self._resolve(mid, c),
                    fg_color=GLASS["fill_hover"],
                    hover_color=GLASS["success"],
                    text_color=GLASS["text"],
                    font=FONT["small"],
                    width=140, height=36,
                    border_width=1, border_color=GLASS["border"],
                    corner_radius=8,
                ).grid(row=2, column=1, sticky="w", padx=4, pady=(0, 10))

    def _get_finder_id(self, match: dict) -> int:
        """Return the user_id of the person who found the item."""
        found_item = self.db.get_item_by_id(match["found_item_id"])
        return found_item["user_id"] if found_item else 0

    def _open_chat(self, match_id: int, finder_id: int):
        if callable(self.on_open_chat):
            self.on_open_chat(match_id, finder_id)

    def _resolve(self, match_id: int, card: ctk.CTkFrame):
        self.db.resolve_match(match_id)
        # Update both items to 'returned'
        match = self.db.get_match_by_id(match_id)
        if match:
            self.db.update_item_status(match["lost_item_id"],  "returned")
            self.db.update_item_status(match["found_item_id"], "returned")
        Toast.show(self, "✅  Item marked as returned!", kind="success")
        card.configure(border_color=GLASS["success"])
