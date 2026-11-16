# 🎓 Campus Lost & Found

A fully-featured, modern desktop application built with **Python**, **CustomTkinter**, and **SQLite** for managing lost and found items on a university campus.

---

## 👥 Team

| Name | Registration No. |
|------|----------------|
| Priyanshu Mishra | RA2511026010716 |
| Argha Atta | RA2511026010711 |
| Kumar Harshvardhan Jaytri | RA2511026010681 |

> SRM Institute of Science and Technology

---

## ✨ Features

- **Glassmorphism UI** — dark gradient background with frosted-glass card panels
- **Smooth Animations** — cubic-eased slide transitions between screens
- **Secure Auth** — SHA-256 + per-user salt password hashing, security Q&A recovery
- **Smart Matching Engine** — `difflib` fuzzy matching (category 40% + colour 35% + brand 25%) with 80% threshold catches typos like `"miltton"` → `"milton"`
- **In-app Notifications** — real-time badge, match alerts sent only to the item owner
- **WhatsApp-style Chat** — per-match conversation between owner and finder, polled every 2.5 s
- **Status Timeline** — visual 4-step lifecycle: Reported → Match Found → In Negotiation → Returned
- **Image Attachment** — file-picker stores image path alongside each report

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install customtkinter Pillow
```
> `sqlite3` ships with the Python standard library — no extra install needed.

### 2. Run the app
```bash
python main.py
```

---

## 🗂 Project Structure

```
campus-lost-and-found/
├── main.py                        # App controller, root window, navigation
├── config.py                      # Colours, fonts, constants (single source of truth)
├── database.py                    # DatabaseManager — all SQL centralised here
│
├── logic/
│   └── matching_engine.py         # Weighted fuzzy matching with difflib
│
├── utils/
│   ├── theme.py                   # GlassmorphicFrame, GlowButton, Toast, Timeline
│   └── animations.py              # AnimationManager — slide/fade transitions
│
└── screens/
    ├── home_screen.py             # Splash screen + team card + glow animation
    ├── auth_screen.py             # Login / Register / Password Recovery
    ├── portal_screen.py           # Main dashboard + sidebar + My Reports
    ├── report_screen.py           # Lost & Found submission form
    ├── notifications_screen.py    # Notification centre
    └── chat_screen.py             # iMessage-style chat UI
```

---

## 🗄 Database Schema

| Table | Key Columns |
|-------|------------|
| `users` | `user_id`, `username`, `password` (hashed), `salt`, `sec_q`, `sec_a` |
| `items` | `item_id`, `type` (lost/found), `category`, `color`, `brand`, `date_lost`, `location`, `image_path`, `user_id`, `status` |
| `matches` | `match_id`, `lost_item_id`, `found_item_id`, `score`, `status` |
| `notifications` | `notif_id`, `user_id`, `match_id`, `message`, `is_read` |
| `messages` | `msg_id`, `match_id`, `sender_id`, `receiver_id`, `message_text`, `timestamp` |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI Framework | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Image Processing | [Pillow](https://python-pillow.org/) |
| Database | SQLite 3 (built-in) |
| Fuzzy Matching | `difflib.SequenceMatcher` (built-in) |
| Security | `hashlib` SHA-256 + `secrets` (built-in) |

---

## 📄 License

MIT License — feel free to use and adapt for academic projects.
