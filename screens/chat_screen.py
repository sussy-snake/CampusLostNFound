"""
screens/chat_screen.py
──────────────────────
ChatScreen — a WhatsApp/iMessage-style chat interface between the item
owner and the item finder.  Messages are polled from the DB every 2 s.
"""

import tkinter as tk
import customtkinter as ctk
from datetime import datetime
from utils.theme import GlassmorphicFrame, GlowButton, Toast
from config import GLASS, FONT


class ChatScreen(ctk.CTkFrame):
    """
    Chat UI for a specific match conversation.

    Parameters
    ----------
    match_id      : the match row ID in DB
    current_user  : dict  (logged-in user)
    other_user_id : int   (the other participant)
    db            : DatabaseManager
    on_back       : callback to return to notifications
    """

    POLL_MS = 2500       # poll interval for new messages

    def __init__(self, master, match_id: int, current_user: dict,
                 other_user_id: int, db, on_back=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.match_id      = match_id
        self.current_user  = current_user
        self.other_user_id = other_user_id
        self.db            = db
        self.on_back       = on_back
        self._last_msg_id  = -1
        self._poll_job     = None

        self._fetch_other_user()
        self._build_ui()
        self._load_all_messages()
        self._start_polling()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _fetch_other_user(self):
        """Load the other participant's info."""
        other = self.db.get_user_by_id(self.other_user_id)
        self._other_name = other["username"] if other else "Unknown"

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # ── Top Bar ────────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=GLASS["sidebar_bg"],
                           corner_radius=0, height=56)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        top.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            top, text="←",
            command=self._go_back,
            fg_color="transparent", hover_color=GLASS["sidebar_hover"],
            text_color=GLASS["text_dim"], font=FONT["heading"],
            width=40, height=40,
        ).grid(row=0, column=0, padx=(12, 0), pady=8)

        # Avatar circle (canvas)
        av_canvas = tk.Canvas(top, width=36, height=36,
                              bg=GLASS["sidebar_bg"],
                              highlightthickness=0)
        av_canvas.grid(row=0, column=1, padx=(8, 0), pady=10)
        av_canvas.create_oval(2, 2, 34, 34, fill=GLASS["accent"],
                              outline=GLASS["border_accent"])
        av_canvas.create_text(18, 18,
                              text=self._other_name[0].upper(),
                              font=("Segoe UI", 14, "bold"), fill="white")

        # Name + status
        info = ctk.CTkFrame(top, fg_color="transparent")
        info.grid(row=0, column=2, padx=10, sticky="w")
        ctk.CTkLabel(info, text=self._other_name,
                     font=FONT["label"],
                     text_color=GLASS["text_bright"]).pack(anchor="w")
        ctk.CTkLabel(info, text="Online  •  Match conversation",
                     font=FONT["caption"],
                     text_color=GLASS["text_dim"]).pack(anchor="w")

        # Match info button
        ctk.CTkButton(
            top, text="ℹ  Match Info",
            command=self._show_match_info,
            fg_color=GLASS["fill"], hover_color=GLASS["fill_hover"],
            text_color=GLASS["text_dim"], font=FONT["small"],
            border_width=1, border_color=GLASS["border"],
            width=110, height=32, corner_radius=8,
        ).grid(row=0, column=3, padx=16, pady=12)

        # ── Message Area ───────────────────────────────────────────────────────
        msg_container = ctk.CTkFrame(
            self, fg_color=GLASS["input_bg"], corner_radius=0)
        msg_container.grid(row=1, column=0, sticky="nsew")
        msg_container.grid_rowconfigure(0, weight=1)
        msg_container.grid_columnconfigure(0, weight=1)

        self.msg_scroll = ctk.CTkScrollableFrame(
            msg_container,
            fg_color="transparent",
            scrollbar_button_color=GLASS["border"],
            scrollbar_button_hover_color=GLASS["accent"],
        )
        self.msg_scroll.grid(row=0, column=0, sticky="nsew",
                             padx=0, pady=0)
        self.msg_scroll.grid_columnconfigure(0, weight=1)

        # ── Input Bar ──────────────────────────────────────────────────────────
        input_bar = ctk.CTkFrame(self,
                                 fg_color=GLASS["sidebar_bg"],
                                 corner_radius=0, height=64)
        input_bar.grid(row=2, column=0, sticky="ew")
        input_bar.grid_propagate(False)
        input_bar.grid_columnconfigure(0, weight=1)

        self.msg_entry = ctk.CTkEntry(
            input_bar,
            placeholder_text="Type a message…",
            fg_color=GLASS["input_bg"],
            border_color=GLASS["input_border"],
            text_color=GLASS["text"],
            placeholder_text_color=GLASS["text_dim"],
            font=FONT["body"],
            corner_radius=20,
            border_width=1,
            height=40,
        )
        self.msg_entry.grid(row=0, column=0, padx=(16, 8),
                            pady=12, sticky="ew")
        self.msg_entry.bind("<Return>", lambda e: self._send())

        ctk.CTkButton(
            input_bar, text="Send ➤",
            command=self._send,
            fg_color=GLASS["accent"],
            hover_color=GLASS["accent_glow"],
            text_color="white",
            font=FONT["label"],
            width=90, height=40,
            corner_radius=20,
        ).grid(row=0, column=1, padx=(0, 16), pady=12)

    # ── Message Rendering ──────────────────────────────────────────────────────

    def _load_all_messages(self):
        """Clear and redraw all messages."""
        for w in self.msg_scroll.winfo_children():
            w.destroy()
        messages = self.db.get_messages(self.match_id)
        for msg in messages:
            self._render_msg(msg)
            self._last_msg_id = msg["msg_id"]
        self._scroll_to_bottom()

    def _render_msg(self, msg: dict):
        """Render a single message bubble."""
        is_mine = (msg["sender_id"] == self.current_user["user_id"])
        time_str = msg.get("timestamp", "")[:16]

        # Outer row — aligns bubble left or right
        row = ctk.CTkFrame(self.msg_scroll, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=3)

        if is_mine:
            # My bubble: right-aligned, accent colour
            bubble_frame = ctk.CTkFrame(
                row,
                fg_color=GLASS["accent"],
                corner_radius=16, border_width=0,
            )
            bubble_frame.pack(side="right")
        else:
            # Their bubble: left-aligned, dark glass
            bubble_frame = ctk.CTkFrame(
                row,
                fg_color=GLASS["fill_hover"],
                corner_radius=16,
                border_width=1,
                border_color=GLASS["border"],
            )
            bubble_frame.pack(side="left")

        ctk.CTkLabel(
            bubble_frame,
            text=msg["message_text"],
            font=FONT["body"],
            text_color="white",
            wraplength=360,
            justify="left",
            anchor="w",
        ).pack(padx=14, pady=(8, 2), anchor="w")

        ctk.CTkLabel(
            bubble_frame,
            text=time_str,
            font=FONT["caption"],
            text_color="#ffffff80" if is_mine else GLASS["text_dim"],
        ).pack(padx=14, pady=(0, 6), anchor="e")

    def _scroll_to_bottom(self):
        """Scroll the message list to the latest message."""
        self.after(80, lambda: self.msg_scroll._parent_canvas.yview_moveto(1.0))

    # ── Sending ────────────────────────────────────────────────────────────────

    def _send(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        self.db.send_message(
            match_id    = self.match_id,
            sender_id   = self.current_user["user_id"],
            receiver_id = self.other_user_id,
            text        = text,
        )
        self.msg_entry.delete(0, "end")
        self._load_all_messages()

    # ── Polling ────────────────────────────────────────────────────────────────

    def _start_polling(self):
        """Poll for new messages every POLL_MS milliseconds."""
        self._poll_job = self.after(self.POLL_MS, self._poll)

    def _poll(self):
        """Check for messages newer than _last_msg_id."""
        try:
            msgs = self.db.get_messages(self.match_id)
            if msgs and msgs[-1]["msg_id"] != self._last_msg_id:
                self._load_all_messages()
        except Exception:
            pass
        self._poll_job = self.after(self.POLL_MS, self._poll)

    def _stop_polling(self):
        if self._poll_job:
            self.after_cancel(self._poll_job)
            self._poll_job = None

    # ── Match Info Popup ───────────────────────────────────────────────────────

    def _show_match_info(self):
        match = self.db.get_match_by_id(self.match_id)
        if not match:
            return
        lost  = self.db.get_item_by_id(match["lost_item_id"])
        found = self.db.get_item_by_id(match["found_item_id"])

        popup = tk.Toplevel(self)
        popup.title("Match Details")
        popup.configure(bg=GLASS["fill"])
        popup.geometry("420x340")
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text="🔗  Match Details",
                     font=FONT["heading"],
                     text_color=GLASS["text_bright"]).pack(pady=(16, 8))

        pct = int(match["score"] * 100) if match.get("score") else "?"

        info_lines = [
            f"Match Confidence : {pct}%",
            "",
            "── Lost Item ──",
            f"  Category : {lost['category'] if lost else '?'}",
            f"  Color    : {lost['color'] if lost else '?'}",
            f"  Brand    : {lost['brand'] if lost else '?'}",
            f"  Location : {lost['location'] if lost else '?'}",
            "",
            "── Found Item ──",
            f"  Category : {found['category'] if found else '?'}",
            f"  Color    : {found['color'] if found else '?'}",
            f"  Brand    : {found['brand'] if found else '?'}",
            f"  Location : {found['location'] if found else '?'}",
        ]

        txt = ctk.CTkTextbox(popup, width=380, height=200,
                             fg_color=GLASS["input_bg"],
                             text_color=GLASS["text"],
                             font=FONT["mono"])
        txt.pack(padx=20, pady=8)
        txt.insert("1.0", "\n".join(info_lines))
        txt.configure(state="disabled")

        ctk.CTkButton(popup, text="Close",
                      command=popup.destroy,
                      fg_color=GLASS["accent"],
                      text_color="white",
                      font=FONT["body"],
                      width=100).pack(pady=10)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _go_back(self):
        self._stop_polling()
        if callable(self.on_back):
            self.on_back()
