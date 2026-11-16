"""
screens/portal_screen.py
────────────────────────
PortalScreen — the main dashboard shown after successful login.

Layout
──────
┌──────────────┬────────────────────────────────────────┐
│   Sidebar    │            Content Area                 │
│  (220 px)    │   (switches between sub-screens)        │
└──────────────┴────────────────────────────────────────┘

Sidebar links: Dashboard, Report Lost, Report Found,
               My Reports, Notifications, Logout
"""

import tkinter as tk
import customtkinter as ctk
from datetime import datetime

from utils.theme import (
    GlassmorphicFrame, GlowButton, SectionLabel,
    StatusTimeline, Toast, NotifBadge
)
from config import GLASS, FONT, TIMELINE_STEPS, SIDEBAR_WIDTH, STATUS_LABELS
from screens.report_screen        import ReportScreen
from screens.notifications_screen import NotificationsScreen
from screens.chat_screen          import ChatScreen


class PortalScreen(ctk.CTkFrame):
    """
    Main application shell after login.

    Parameters
    ----------
    current_user : dict returned by db.login_user
    db           : DatabaseManager
    on_logout    : callback to return to auth/home
    """

    def __init__(self, master, current_user: dict, db,
                 on_logout=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.current_user = current_user
        self.db           = db
        self.on_logout    = on_logout
        self._active_btn  = None
        self._build_shell()
        self._show_dashboard()
        self._start_notif_poll()

    # ── Shell Layout ───────────────────────────────────────────────────────────

    def _build_shell(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ────────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH,
            fg_color=GLASS["sidebar_bg"],
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # App logo / name
        logo_frame = ctk.CTkFrame(self.sidebar,
                                  fg_color=GLASS["fill"],
                                  corner_radius=0, height=72)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame,
                     text="🎓  L&F Portal",
                     font=("Segoe UI", 15, "bold"),
                     text_color=GLASS["text_bright"]).place(relx=0.5, rely=0.5,
                                                             anchor="center")

        # User card
        user_card = ctk.CTkFrame(self.sidebar,
                                  fg_color=GLASS["fill"],
                                  corner_radius=10)
        user_card.pack(fill="x", padx=12, pady=(12, 8), ipady=8)

        ctk.CTkLabel(user_card,
                     text=f"👤  {self.current_user['username']}",
                     font=FONT["label"],
                     text_color=GLASS["text_bright"]).pack(padx=10, pady=(6, 2))
        ctk.CTkLabel(user_card,
                     text=f"ID #{self.current_user['user_id']}",
                     font=FONT["caption"],
                     text_color=GLASS["text_dim"]).pack(padx=10, pady=(0, 6))

        ctk.CTkFrame(self.sidebar, height=1,
                     fg_color=GLASS["border"],
                     corner_radius=0).pack(fill="x", padx=16, pady=4)

        # ── Nav Buttons ────────────────────────────────────────────────────────
        nav_items = [
            ("🏠  Dashboard",        self._show_dashboard),
            ("🔍  Report Lost Item", lambda: self._show_report("lost")),
            ("📦  Report Found Item",lambda: self._show_report("found")),
            ("📋  My Reports",       self._show_my_reports),
            ("🔔  Notifications",    self._show_notifications),
        ]
        self._nav_btns = {}
        for label, cmd in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                command=cmd,
                anchor="w",
                fg_color="transparent",
                hover_color=GLASS["sidebar_hover"],
                text_color=GLASS["text_dim"],
                font=FONT["body"],
                width=SIDEBAR_WIDTH - 16,
                height=42,
                corner_radius=8,
                border_width=0,
            )
            btn.pack(padx=8, pady=2)
            self._nav_btns[label] = btn

        # Notification badge on the notifications button
        notif_btn = self._nav_btns["🔔  Notifications"]
        self._notif_badge = NotifBadge(notif_btn, 0)

        # ── Logout at bottom ───────────────────────────────────────────────────
        ctk.CTkFrame(self.sidebar, height=1,
                     fg_color=GLASS["border"],
                     corner_radius=0).pack(fill="x", padx=16, pady=8,
                                           side="bottom")
        ctk.CTkButton(
            self.sidebar,
            text="🚪  Logout",
            command=self._logout,
            anchor="w",
            fg_color="transparent",
            hover_color=GLASS["danger"],
            text_color=GLASS["text_dim"],
            font=FONT["body"],
            width=SIDEBAR_WIDTH - 16,
            height=40,
            corner_radius=8,
        ).pack(side="bottom", padx=8, pady=(0, 12))

        # ── Content Area ───────────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self,
                                     fg_color="transparent",
                                     corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    # ── Sidebar Active State ───────────────────────────────────────────────────

    def _set_active(self, label: str):
        for lbl, btn in self._nav_btns.items():
            if lbl == label:
                btn.configure(fg_color=GLASS["fill"],
                              text_color=GLASS["accent_glow"])
            else:
                btn.configure(fg_color="transparent",
                              text_color=GLASS["text_dim"])

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── Sub-screens ────────────────────────────────────────────────────────────

    def _show_dashboard(self):
        self._set_active("🏠  Dashboard")
        self._clear_content()
        DashboardView(
            self.content,
            current_user=self.current_user,
            db=self.db,
            on_report_lost=lambda: self._show_report("lost"),
            on_report_found=lambda: self._show_report("found"),
            on_my_reports=self._show_my_reports,
            on_notifications=self._show_notifications,
        ).grid(row=0, column=0, sticky="nsew")

    def _show_report(self, item_type: str):
        label = ("🔍  Report Lost Item" if item_type == "lost"
                 else "📦  Report Found Item")
        self._set_active(label)
        self._clear_content()
        ReportScreen(
            self.content,
            item_type=item_type,
            current_user=self.current_user,
            db=self.db,
            on_done=lambda _: self._show_dashboard(),
            on_back=self._show_dashboard,
        ).grid(row=0, column=0, sticky="nsew")

    def _show_my_reports(self):
        self._set_active("📋  My Reports")
        self._clear_content()
        MyReportsView(
            self.content,
            current_user=self.current_user,
            db=self.db,
            on_back=self._show_dashboard,
            on_open_chat=self._open_chat,
        ).grid(row=0, column=0, sticky="nsew")

    def _show_notifications(self):
        self._set_active("🔔  Notifications")
        self._clear_content()
        NotificationsScreen(
            self.content,
            current_user=self.current_user,
            db=self.db,
            on_open_chat=self._open_chat,
            on_back=self._show_dashboard,
        ).grid(row=0, column=0, sticky="nsew")
        # Reset badge
        self._notif_badge.update_count(0)

    def _open_chat(self, match_id: int, finder_id: int):
        self._clear_content()
        ChatScreen(
            self.content,
            match_id=match_id,
            current_user=self.current_user,
            other_user_id=finder_id,
            db=self.db,
            on_back=self._show_notifications,
        ).grid(row=0, column=0, sticky="nsew")

    # ── Notification Polling ───────────────────────────────────────────────────

    def _start_notif_poll(self):
        self._poll_notifications()

    def _poll_notifications(self):
        try:
            count = self.db.unread_count(self.current_user["user_id"])
            self._notif_badge.update_count(count)
        except Exception:
            pass
        self.after(5000, self._poll_notifications)

    # ── Logout ─────────────────────────────────────────────────────────────────

    def _logout(self):
        if callable(self.on_logout):
            self.on_logout()


# ══════════════════════════════════════════════════════════════════════════════
# DashboardView
# ══════════════════════════════════════════════════════════════════════════════

class DashboardView(ctk.CTkFrame):
    """The home dashboard inside the portal."""

    def __init__(self, master, current_user, db,
                 on_report_lost, on_report_found,
                 on_my_reports, on_notifications, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.current_user    = current_user
        self.db              = db
        self.on_report_lost  = on_report_lost
        self.on_report_found = on_report_found
        self.on_my_reports   = on_my_reports
        self.on_notifs       = on_notifications
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        # Greeting header
        hour = datetime.now().hour
        greeting = ("Good morning" if hour < 12
                    else "Good afternoon" if hour < 18 else "Good evening")
        ctk.CTkLabel(
            self,
            text=f"{greeting}, {self.current_user['username']}! 👋",
            font=("Segoe UI", 24, "bold"),
            text_color=GLASS["text_bright"],
        ).grid(row=0, column=0, columnspan=4, sticky="w",
               padx=28, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text="Here's your Lost & Found overview",
            font=FONT["small"], text_color=GLASS["text_dim"],
        ).grid(row=1, column=0, columnspan=4, sticky="w", padx=28, pady=(0, 20))

        # ── Stats Row ──────────────────────────────────────────────────────────
        items = self.db.get_items_by_user(self.current_user["user_id"])
        total  = len(items)
        lost   = sum(1 for i in items if i["type"] == "lost")
        found  = sum(1 for i in items if i["type"] == "found")
        matched= sum(1 for i in items if i["status"] == "matched")

        stats = [
            ("📋", "Total Reports", total,  GLASS["accent"]),
            ("🔍", "Lost Items",    lost,   GLASS["danger"]),
            ("📦", "Found Items",   found,  GLASS["success"]),
            ("🔗", "Matches",       matched,GLASS["warning"]),
        ]

        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for col, (icon, label, val, color) in enumerate(stats):
            card = GlassmorphicFrame(self, border_color=color)
            card.grid(row=2, column=col, padx=(28 if col==0 else 8, 8 if col<3 else 28),
                      pady=(0, 20), sticky="ew", ipadx=12, ipady=12)
            ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 26)).pack()
            ctk.CTkLabel(card, text=str(val),
                         font=("Segoe UI", 28, "bold"),
                         text_color=color).pack()
            ctk.CTkLabel(card, text=label,
                         font=FONT["small"],
                         text_color=GLASS["text_dim"]).pack()

        # ── Quick Actions ──────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Quick Actions",
                     font=FONT["heading"],
                     text_color=GLASS["text_bright"]).grid(
            row=3, column=0, columnspan=4, sticky="w", padx=28, pady=(0, 12))

        actions = [
            ("🔍  Report Lost Item",  self.on_report_lost,  False),
            ("📦  Report Found Item", self.on_report_found, False),
            ("📋  My Reports",        self.on_my_reports,   True),
            ("🔔  Notifications",     self.on_notifs,       True),
        ]

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=4, column=0, columnspan=4, sticky="w", padx=24)

        for text, cmd, secondary in actions:
            GlowButton(btn_row, text=text, command=cmd,
                       width=180, height=44,
                       is_secondary=secondary).pack(side="left", padx=4)

        # ── Recent Items ───────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Recent Reports",
                     font=FONT["heading"],
                     text_color=GLASS["text_bright"]).grid(
            row=5, column=0, columnspan=4, sticky="w", padx=28, pady=(24, 8))

        recent = items[:5]
        if not recent:
            ctk.CTkLabel(self,
                         text="No reports yet. Use the buttons above to get started!",
                         font=FONT["body"], text_color=GLASS["text_dim"]).grid(
                row=6, column=0, columnspan=4, sticky="w", padx=28)
        else:
            for i, item in enumerate(recent):
                self._render_recent_item(item, row=6 + i)

    def _render_recent_item(self, item: dict, row: int):
        status_color = {
            "pending":  GLASS["warning"],
            "matched":  GLASS["success"],
            "returned": GLASS["info"],
            "closed":   GLASS["text_dim"],
        }.get(item["status"], GLASS["text_dim"])

        icon = "🔍" if item["type"] == "lost" else "📦"
        card = ctk.CTkFrame(self, fg_color=GLASS["fill"],
                            corner_radius=8, border_width=1,
                            border_color=GLASS["border"])
        card.grid(row=row, column=0, columnspan=4, sticky="ew",
                  padx=28, pady=3)
        card.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 18),
                     width=36).grid(row=0, column=0, padx=(12, 4), pady=8)
        ctk.CTkLabel(card, text=item["category"],
                     font=FONT["label"],
                     text_color=GLASS["text"]).grid(row=0, column=1, padx=4, pady=8)
        ctk.CTkLabel(card,
                     text=f"{item['color']}  •  {item['brand'] or 'No brand'}",
                     font=FONT["small"],
                     text_color=GLASS["text_dim"]).grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(card,
                     text=STATUS_LABELS.get(item["status"], item["status"]),
                     font=FONT["small"],
                     text_color=status_color).grid(row=0, column=3, padx=12, pady=8)


# ══════════════════════════════════════════════════════════════════════════════
# MyReportsView
# ══════════════════════════════════════════════════════════════════════════════

class MyReportsView(ctk.CTkFrame):
    """Shows a user's submitted items with a status timeline for each."""

    def __init__(self, master, current_user, db, on_back,
                 on_open_chat=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.current_user = current_user
        self.db           = db
        self.on_back      = on_back
        self.on_open_chat = on_open_chat   # callback(match_id, other_user_id)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 8))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(hdr, text="← Back",
                      command=self.on_back,
                      fg_color="transparent",
                      hover_color=GLASS["sidebar_hover"],
                      text_color=GLASS["text_dim"],
                      font=FONT["small"], width=80, height=28
                      ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(hdr, text="📋  My Reports",
                     font=FONT["title"],
                     text_color=GLASS["text_bright"]
                     ).grid(row=0, column=1, sticky="w", padx=12)

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=GLASS["border"],
            scrollbar_button_hover_color=GLASS["accent"],
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        scroll.grid_columnconfigure(0, weight=1)

        items = self.db.get_items_by_user(self.current_user["user_id"])
        if not items:
            ctk.CTkLabel(scroll,
                         text="🗒️  No items reported yet.",
                         font=FONT["body"],
                         text_color=GLASS["text_dim"]).pack(pady=60)
            return

        for item in items:
            self._render_item_card(scroll, item)

    def _render_item_card(self, parent, item: dict):
        # Determine timeline step from status
        step_map = {"pending": 0, "matched": 1, "returned": 3, "closed": 3}
        active = step_map.get(item["status"], 0)
        # If matched AND messages exist, show step 2 (In Negotiation)
        if item["status"] == "matched":
            active = 2

        type_icon  = "🔍" if item["type"] == "lost" else "📦"
        type_label = "Lost" if item["type"] == "lost" else "Found"
        status_clr = {
            "pending":  GLASS["warning"],
            "matched":  GLASS["success"],
            "returned": GLASS["info"],
        }.get(item["status"], GLASS["text_dim"])

        card = GlassmorphicFrame(parent)
        card.pack(fill="x", padx=8, pady=8, ipadx=16, ipady=12)

        # Title row
        hdr_row = ctk.CTkFrame(card, fg_color="transparent")
        hdr_row.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(hdr_row,
                     text=f"{type_icon}  {type_label} — {item['category']}",
                     font=FONT["heading"],
                     text_color=GLASS["text_bright"]).pack(side="left")

        ctk.CTkLabel(hdr_row,
                     text=STATUS_LABELS.get(item["status"], item["status"]),
                     font=FONT["small"],
                     text_color=status_clr).pack(side="right")

        # Detail row
        details = (f"Color: {item['color']}  •  "
                   f"Brand: {item['brand'] or 'N/A'}  •  "
                   f"Location: {item['location'] or 'N/A'}  •  "
                   f"Date: {item['date_lost'] or 'N/A'}")
        ctk.CTkLabel(card, text=details,
                     font=FONT["small"],
                     text_color=GLASS["text_dim"],
                     anchor="w").pack(anchor="w", padx=12, pady=(0, 8))

        # Description
        if item.get("description"):
            ctk.CTkLabel(card,
                         text=item["description"],
                         font=FONT["small"],
                         text_color=GLASS["text"],
                         wraplength=540,
                         anchor="w").pack(anchor="w", padx=12, pady=(0, 8))

        # Timeline
        tl = StatusTimeline(card, steps=TIMELINE_STEPS,
                            active_step=active,
                            height=80)
        tl.pack(fill="x", padx=12, pady=(4, 4))

        # ── Chat button — visible for matched/returned items ───────────────────
        if item["status"] in ("matched", "returned"):
            self._add_chat_button(card, item)

        # Image path indicator
        if item.get("image_path"):
            ctk.CTkLabel(card,
                         text=f"📎  {item['image_path']}",
                         font=FONT["caption"],
                         text_color=GLASS["text_dim"]).pack(anchor="w", padx=12, pady=(0, 8))

    def _add_chat_button(self, card: ctk.CTkFrame, item: dict):
        """
        Look up the match for this item and add a glowing Chat button.
        Works for both the item owner (lost) and the finder (found).
        """
        match = self.db.get_match_for_item(item["item_id"])
        if not match:
            return  # match not yet created (shouldn't happen for status=matched)

        # Determine who the OTHER person is
        lost_item  = self.db.get_item_by_id(match["lost_item_id"])
        found_item = self.db.get_item_by_id(match["found_item_id"])
        my_id      = self.current_user["user_id"]

        if lost_item and lost_item["user_id"] == my_id:
            # I am the owner → chat with finder
            other_id   = found_item["user_id"] if found_item else None
            other_role = "Finder"
        else:
            # I am the finder → chat with owner
            other_id   = lost_item["user_id"] if lost_item else None
            other_role = "Owner"

        if not other_id:
            return

        other_user = self.db.get_user_by_id(other_id)
        other_name = other_user["username"] if other_user else "the other party"
        pct        = int((match.get("score") or 0) * 100)

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(anchor="w", padx=12, pady=(4, 12))

        GlowButton(
            btn_row,
            text=f"💬  Chat with {other_role}  ({other_name})",
            command=lambda mid=match["match_id"], oid=other_id:
                self._open_chat(mid, oid),
            width=280, height=38,
        ).pack(side="left")

        ctk.CTkLabel(
            btn_row,
            text=f"  {pct}% match confidence",
            font=FONT["caption"],
            text_color=GLASS["text_dim"],
        ).pack(side="left", padx=8)

    def _open_chat(self, match_id: int, other_user_id: int):
        if callable(self.on_open_chat):
            self.on_open_chat(match_id, other_user_id)
