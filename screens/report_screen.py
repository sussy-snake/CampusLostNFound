"""
screens/report_screen.py
────────────────────────
ReportScreen — form for submitting a Lost or Found item.

After the user submits a "Found" item, the screen invokes the
MatchingEngine and writes any matches + notifications to the DB.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
from utils.theme import (
    GlassmorphicFrame, GlowButton, SectionLabel, FieldLabel,
    GlassEntry, GlassTextbox, Toast
)
from config import GLASS, FONT, CATEGORIES
from logic.matching_engine import MatchingEngine


class ReportScreen(ctk.CTkFrame):
    """
    Reusable form for reporting a Lost or Found item.

    Parameters
    ----------
    item_type   : "lost" | "found"
    current_user: dict  (from db.login_user)
    db          : DatabaseManager instance
    on_done     : callback(item_id) after successful submission
    on_back     : callback to navigate away
    """

    def __init__(self, master, item_type: str, current_user: dict,
                 db, on_done=None, on_back=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.item_type    = item_type
        self.current_user = current_user
        self.db           = db
        self.on_done      = on_done
        self.on_back      = on_back
        self._image_path  = ""
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Scrollable container
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=GLASS["border"],
            scrollbar_button_hover_color=GLASS["accent"],
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        # Back row
        back_btn = ctk.CTkButton(
            scroll, text="←  Back",
            command=self._go_back,
            fg_color="transparent",
            hover_color=GLASS["sidebar_hover"],
            text_color=GLASS["text_dim"],
            font=FONT["small"], width=90, height=28,
        )
        back_btn.grid(row=0, column=0, sticky="w", padx=24, pady=(16, 0))

        # Title
        icon  = "🔍" if self.item_type == "lost" else "📦"
        label = "Report a Lost Item" if self.item_type == "lost" \
                else "Report a Found Item"
        ctk.CTkLabel(
            scroll, text=f"{icon}  {label}",
            font=FONT["title"], text_color=GLASS["text_bright"],
        ).grid(row=1, column=0, pady=(8, 2))

        ctk.CTkLabel(
            scroll,
            text="Fill in the details below so we can find a match",
            font=FONT["small"], text_color=GLASS["text_dim"],
        ).grid(row=2, column=0, pady=(0, 20))

        # Main card
        card = GlassmorphicFrame(scroll, width=560)
        card.grid(row=3, column=0, padx=40, pady=(0, 30), sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        r = [0]  # mutable row counter

        def next_row():
            r[0] += 1
            return r[0]

        def _lbl(text, row, col=0, colspan=2):
            FieldLabel(card, text=text).grid(
                row=row, column=col, columnspan=colspan,
                sticky="w", padx=(24, 8), pady=(12, 2))

        def _entry(row, col=0, colspan=2, **kw):
            e = GlassEntry(card, width=460 if colspan == 2 else 210, **kw)
            e.grid(row=row, column=col, columnspan=colspan,
                   padx=(24, 24) if colspan == 2 else (24, 8),
                   pady=(0, 4), sticky="ew")
            return e

        # Category
        _lbl("Item Category *", 1)
        self.cat_var = ctk.StringVar(value=CATEGORIES[0])
        ctk.CTkOptionMenu(
            card,
            variable=self.cat_var,
            values=CATEGORIES,
            fg_color=GLASS["input_bg"],
            button_color=GLASS["accent"],
            button_hover_color=GLASS["accent_glow"],
            text_color=GLASS["text"],
            font=FONT["body"],
            width=460,
        ).grid(row=2, column=0, columnspan=2, padx=24, pady=(0, 4), sticky="ew")

        # Color & Brand (side by side)
        _lbl("Color *",  3, col=0, colspan=1)
        _lbl("Brand",    3, col=1, colspan=1)
        self.color_entry = GlassEntry(card, placeholder_text="e.g. Black", width=210)
        self.color_entry.grid(row=4, column=0, padx=(24, 8), pady=(0, 4), sticky="ew")
        self.brand_entry = GlassEntry(card, placeholder_text="e.g. Apple", width=210)
        self.brand_entry.grid(row=4, column=1, padx=(8, 24), pady=(0, 4), sticky="ew")

        # Date & Location (side by side)
        _lbl("Date (DD-MM-YYYY)", 5, col=0, colspan=1)
        _lbl("Approx. Location",  5, col=1, colspan=1)
        today = datetime.now().strftime("%d-%m-%Y")
        self.date_entry = GlassEntry(card, placeholder_text=today, width=210)
        self.date_entry.grid(row=6, column=0, padx=(24, 8), pady=(0, 4), sticky="ew")
        self.date_entry.insert(0, today)
        self.loc_entry = GlassEntry(card,
                                    placeholder_text="e.g. Library Block A",
                                    width=210)
        self.loc_entry.grid(row=6, column=1, padx=(8, 24), pady=(0, 4), sticky="ew")

        # Description
        _lbl("Additional Description", 7)
        self.desc_box = GlassTextbox(card, width=460, height=90)
        self.desc_box.grid(row=8, column=0, columnspan=2,
                           padx=24, pady=(0, 8), sticky="ew")

        # Image upload
        img_row = ctk.CTkFrame(card, fg_color="transparent")
        img_row.grid(row=9, column=0, columnspan=2, padx=24, pady=(4, 12), sticky="w")

        ctk.CTkButton(
            img_row, text="📎  Attach Image (optional)",
            command=self._pick_image,
            fg_color=GLASS["input_bg"],
            hover_color=GLASS["fill_hover"],
            text_color=GLASS["text_dim"],
            border_color=GLASS["border"],
            border_width=1,
            font=FONT["small"],
            width=220, height=32,
        ).pack(side="left")

        self.img_lbl = ctk.CTkLabel(
            img_row, text="  No image selected",
            font=FONT["caption"], text_color=GLASS["text_dim"])
        self.img_lbl.pack(side="left", padx=8)

        # Error label
        self.err_lbl = ctk.CTkLabel(card, text="",
                                    text_color=GLASS["danger"],
                                    font=FONT["small"], wraplength=440)
        self.err_lbl.grid(row=10, column=0, columnspan=2)

        # Submit
        GlowButton(
            card, text="Submit Report  →",
            command=self._submit,
            width=460, height=46,
        ).grid(row=11, column=0, columnspan=2, padx=24, pady=(8, 20))

    # ── Actions ────────────────────────────────────────────────────────────────

    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="Select item image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                       ("All files", "*.*")],
        )
        if path:
            self._image_path = path
            # Truncate long paths for display
            display = path if len(path) <= 40 else "…" + path[-37:]
            self.img_lbl.configure(text=f"  {display}",
                                   text_color=GLASS["success"])

    def _submit(self):
        category = self.cat_var.get()
        color    = self.color_entry.get().strip()
        brand    = self.brand_entry.get().strip()
        date     = self.date_entry.get().strip()
        location = self.loc_entry.get().strip()
        desc     = self.desc_box.get("1.0", "end").strip()

        if not color:
            self.err_lbl.configure(text="⚠  Color is required.")
            return

        # Save to DB
        item_id = self.db.add_item(
            item_type   = self.item_type,
            category    = category,
            color       = color,
            brand       = brand,
            date_lost   = date,
            location    = location,
            description = desc,
            image_path  = self._image_path,
            user_id     = self.current_user["user_id"],
        )

        # ── Run matching engine for FOUND items ────────────────────────────────
        if self.item_type == "found":
            self._run_matching(item_id, {
                "category": category,
                "color":    color,
                "brand":    brand,
                "user_id":  self.current_user["user_id"],
                "item_id":  item_id,
            })

        Toast.show(self, "✅  Report submitted successfully!", kind="success")
        self.after(1200, lambda: self._finish(item_id))

    def _run_matching(self, found_item_id: int, found_dict: dict):
        """
        Query all pending lost items, run fuzzy matching, create match
        records and send notifications to affected owners.
        """
        lost_items = self.db.get_all_lost_items()
        matches    = MatchingEngine.find_matches(found_dict, lost_items)

        for m in matches:
            lost    = m["lost_item"]
            score   = m["score"]
            match_id = self.db.create_match(lost["item_id"], found_item_id, score)

            # Mark both items as matched
            self.db.update_item_status(lost["item_id"],    "matched")
            self.db.update_item_status(found_item_id,      "matched")

            # Notify the owner of the lost item
            finder_name = self.current_user.get("username", "Someone")
            pct         = int(score * 100)
            msg = (
                f"🔗  Match found ({pct}% confidence) for your lost "
                f"{lost['category']} ({lost['color']}, {lost['brand'] or 'unknown brand'})! "
                f"Found by {finder_name}. Tap to connect."
            )
            self.db.add_notification(lost["user_id"], match_id, msg)

    def _finish(self, item_id: int):
        if callable(self.on_done):
            self.on_done(item_id)

    def _go_back(self):
        if callable(self.on_back):
            self.on_back()
