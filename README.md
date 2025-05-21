# 📜 The Vigil of Origins

> *A mystical Discord bot that watches the birth of nations in NationStates and alerts your server when a new banner is unfurled.*

---

## ✨ What Is This?

**The Vigil of Origins** is a real-time NationStates founding monitor. It listens to the official NationStates founding event stream and sends alerts to a Discord channel when new nations are founded — complete with links, flags, and telegram templates.

You can customize the bot to:
- Ping a specific role (to rally recruiters, greeters, etc.)
- Blacklist certain regions
- Attach telegram templates for quick follow-up
- Deliver beautifully themed, lore-inspired embeds

---

## 🚀 Setup Instructions

### 1. 📦 Install Requirements

First, install the required Python packages:

```bash
pip install aiohttp sseclient requests
```

> Python 3.8+ recommended.

---

### 2. 📁 Run the Bot

Download or clone the script and run it:

```bash
python vigil_of_origins.py
```

On first run, the bot will guide you through a setup wizard:

- **Webhook URL** — Create a webhook in your Discord channel and paste it here.
- **User-Agent** — Set a NationStates user-agent (e.g. `my-nation - by discord-user`).
- **Blacklisted Regions** — Comma-separated names of regions to ignore (e.g. `test region, my puppet zone`).
- **Telegram Templates** — Add optional telegram templates using this format:  
  ```
  35972625:Welcome,12345678:Recruitment
  ```
- **Role to Ping** — Paste a Discord **role ID** to ping for new foundings (leave blank if you don’t want pings).

The bot saves this config in a local `config.json` file and remembers it for future runs.

---

## 🧪 Example Output

The bot will post something like this when a nation is founded:

> <@&123456789012345678>  
> 📜 A Banner Unfurled — *new_nation* was founded in *The North Pacific*  
> 🧭 **Nations Welcomed by the Realms**: new_nation  
> 📨 **Ritual Telegram Paths:**  
> • [Welcome Invocation](...)  
> 🖋️ [Commune with the Newborn Realms](...)

---

## 🛠 Editing the Config Later

You can:
- Open `config.json` in a text editor.
- Delete the file to trigger the setup wizard again.
- Or let the bot prompt you for missing values next time it runs.

---

## 🎨 Customization Ideas

Want to extend it?
- Send summary digests instead of live posts
- Add different ping roles for specific regions
- Only ping on *refoundings*
- Filter based on name patterns or nation tags

---

## ❤️ Credits & Notes

Created for NationStates by players who love worldbuilding and good vibes.  
Inspired by the need to watch the horizon — for what banners rise next.
