"""
config.py
─────────
Central configuration: colours, fonts, sizing constants.
All theme values live here so a single edit reshapes the whole app.
"""

# ── Application Metadata ───────────────────────────────────────────────────────
APP_TITLE   = "Campus Lost and Found"
APP_VERSION = "1.0.0"
DB_PATH     = "campus_laf.db"
WIN_SIZE    = "1200x720"
MIN_SIZE    = (1000, 650)

# ── Team Members (Splash Screen) ──────────────────────────────────────────────
TEAM_MEMBERS = [
    ("Priyanshu Mishra",           "RA2511026010716"),
    ("Argha Atta",                 "RA2511026010711"),
    ("Kumar Harshvardhan Jaytri",  "RA2511026010681"),
]

# ── Matching Engine Thresholds ─────────────────────────────────────────────────
FUZZY_THRESHOLD = 0.80          # 80 % similarity → considered a match
MATCH_WEIGHTS   = {             # relative importance of each field
    "category": 0.40,
    "color":    0.35,
    "brand":    0.25,
}

# ── Gradient Background Colours (top → bottom) ────────────────────────────────
BG_TOP    = (10,  15,  40)      # deep navy
BG_BOTTOM = (30,  10,  60)      # deep violet

# ── Glassmorphism Palette ──────────────────────────────────────────────────────
GLASS = {
    "fill":          "#1a1a3a",   # panel background  (semi-dark)
    "fill_hover":    "#252550",   # panel hover tint
    "border":        "#4a4a8a",   # subtle violet border
    "border_accent": "#7b68ee",   # medium-slate-blue accent
    "text":          "#e8e8ff",   # primary text (near-white lavender)
    "text_dim":      "#9090c0",   # secondary / placeholder text
    "text_bright":   "#ffffff",   # headings
    "accent":        "#7b68ee",   # MediumSlateBlue  — primary accent
    "accent_glow":   "#a08fff",   # lighter glow tint
    "success":       "#2ecc71",
    "danger":        "#e74c3c",
    "warning":       "#f39c12",
    "info":          "#3498db",
    "sidebar_bg":    "#0f0f28",
    "sidebar_hover": "#1e1e45",
    "input_bg":      "#0d0d2b",
    "input_border":  "#5555aa",
}

# ── Typography ─────────────────────────────────────────────────────────────────
FONT = {
    "hero":    ("Segoe UI", 36, "bold"),
    "title":   ("Segoe UI", 22, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "body":    ("Segoe UI", 12),
    "small":   ("Segoe UI", 10),
    "mono":    ("Consolas", 11),
    "label":   ("Segoe UI", 11, "bold"),
    "caption": ("Segoe UI",  9),
}

# ── Widget Sizing ──────────────────────────────────────────────────────────────
CORNER_RADIUS   = 14
BTN_CORNER      = 10
ENTRY_CORNER    = 8
SIDEBAR_WIDTH   = 220
CONTENT_PAD     = 24
ANIMATION_STEPS = 20          # frames used for slide / fade transitions
ANIMATION_MS    = 12          # ms between frames  (~60 fps feel)

# ── Item Categories ────────────────────────────────────────────────────────────
CATEGORIES = [
    "Bottle", "Bag / Backpack", "Laptop", "Mobile Phone",
    "ID Card / Student Card", "Keys", "Wallet / Purse",
    "Earphones / Headphones", "Glasses / Sunglasses",
    "Clothing", "Stationery", "Umbrella", "Watch",
    "Calculator", "Charger / Cable", "Other",
]

# ── Item Status Labels ─────────────────────────────────────────────────────────
STATUS_LABELS = {
    "pending":  "🔍  Searching",
    "matched":  "✅  Match Found",
    "returned": "🏠  Returned",
    "closed":   "🔒  Closed",
}

# ── Timeline Steps ─────────────────────────────────────────────────────────────
TIMELINE_STEPS = [
    ("Reported",        "📋"),
    ("Match Found",     "🔗"),
    ("In Negotiation",  "💬"),
    ("Returned",        "🏠"),
]
