import asyncio
import aiohttp
import json
import os
import re
import time
from datetime import datetime
import requests
from sseclient import SSEClient
import random

CONFIG_FILE = "config.json"
SCRIPT_NAME = "The_Vigil_of_Origins"


def log_debug(message):
    print(f"[DEBUG {datetime.now()}] {message}")


def get_human_time(ts=None):
    return datetime.fromtimestamp(ts or time.time()).strftime("%B %d, %Y at %H:%M:%S")


def load_config():
    return json.load(open(CONFIG_FILE)) if os.path.exists(CONFIG_FILE) else {}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def prompt_if_missing(config, key, prompt):
    if key not in config or not config[key]:
        config[key] = input(prompt).strip()
    return config[key]


def setup_config():
    config = load_config()

    prompt_if_missing(config, "webhook", "Enter your Discord Webhook URL: ")
    prompt_if_missing(config, "user_agent", "Enter your NationStates User Agent: ")
    if "blacklist" not in config:
        regions = input("Enter region names to blacklist (comma-separated): ")
        config["blacklist"] = [
            r.strip().lower().replace(" ", "_") for r in regions.split(",")
        ]
    if "templates" not in config:
        print(
            "Enter template:name pairs (comma-separated, format = templateID:Button Name)"
        )
        print(
            "Example: 35972625:Welcome,12345678:Recruitment — or leave blank for no templates"
        )
        templates_input = input("Templates: ").strip()
        template_map = {}
        if templates_input:
            for pair in templates_input.split(","):
                tid, label = pair.split(":", 1)
                template_map[label.strip()] = tid.strip()
        config["templates"] = template_map
    prompt_if_missing(
        config,
        "role_to_ping",
        "Enter the Discord Role ID to ping on new foundings (or leave blank for none): ",
    )

    save_config(config)
    return config


def extract_target_name(found_str):
    match = re.search(r"@@(.*?)@@", found_str)
    return match.group(1) if match else None


def extract_flag_url(event):
    match = re.search(r'<img src="(/images/flags/[^\"]+)"', event.get("htmlStr", ""))
    if match:
        return "https://www.nationstates.net" + match.group(1).replace(".svg", ".png")
    return "https://www.nationstates.net/images/flags/Default.png"


def is_valid_event(event, blacklist):
    if "str" not in event:
        log_debug("No STR in event")
        return False
    nation = extract_target_name(event["str"])
    if not nation or nation[-1].isdigit():
        log_debug(f"Ignoring puppet or invalid nation: {nation}")
        return False
    for region in blacklist:
        if f"%%{region.strip()}%%" in event["str"].lower():
            log_debug(f"Ignoring blacklisted region founding: {region}")
            return False
    return True


def build_title_and_url(event_str):
    nation = extract_target_name(event_str)
    region_match = re.search(r"%%(.*?)%%", event_str)
    region = (
        region_match.group(1).replace("_", " ").title()
        if region_match
        else "an unknown region"
    )
    verb = "refounded" if "refounded" in event_str else "founded"
    title_text = f"{nation} was {verb} in {region}"
    nation_url = f"https://www.nationstates.net/nation={nation}"
    return title_text, nation_url


def build_link(nations, ua, template_id):
    targets = ",".join(nations)
    return f"https://www.nationstates.net/page=compose_telegram?tgto={targets}&message={template_id}&generated_by={SCRIPT_NAME},used_by={ua}"


async def send_to_discord(webhook_url, display_str, nations, config, flag_url=None):
    title_text, nation_url = build_title_and_url(display_str)
    embed = {
        "title": f"📜 A Banner Unfurled — {title_text}",
        "url": nation_url,
        "color": 0x4B0082,
        "thumbnail": {"url": flag_url} if flag_url else {},
        "footer": {
            "text": f"The Vigil of Origins • Chronicle recorded {get_human_time()}"
        },
    }

    description_lines = [
        f"🧭 **Nations Welcomed by the Realms**: {', '.join(nations)}",
        "",
    ]

    if config.get("templates"):
        description_lines.append("📨 **Ritual Telegram Paths:**")
        for name, tid in config["templates"].items():
            link = build_link(nations, config["user_agent"], tid)
            description_lines.append(f"• [{name} Invocation]({link})")

    tgto = ",".join(nations)
    generic_link = f"https://www.nationstates.net/page=compose_telegram?tgto={tgto}&generated_by={SCRIPT_NAME},used_by={config['user_agent']}"
    description_lines.append("")
    description_lines.append(f"🖋️ [Commune with the Newborn Realms]({generic_link})")

    embed["description"] = "\n".join(description_lines)

    # Mention role outside the embed to trigger real pings
    content = f"<@&{config['role_to_ping']}>" if config.get("role_to_ping") else ""

    payload = {
        "content": content,
        "embeds": [embed],
    }

    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)


async def send_info_embed(config):
    template_lines = [
        f"• **{name}** (ID: `{tid}`)"
        for name, tid in config.get("templates", {}).items()
    ]
    if not template_lines:
        template_lines.append("• _No templates provided_")

    embed = {
        "title": "✨ The Vigil of Origins Stirs",
        "color": 0x4B0082,
        "fields": [
            {"name": "User-Agent", "value": config["user_agent"], "inline": True},
            {
                "name": "Watched Realms (Blacklisted)",
                "value": ", ".join(config["blacklist"]) or "_None_",
                "inline": False,
            },
            {
                "name": "📜 Templates of Initiation",
                "value": "\n".join(template_lines),
                "inline": False,
            },
        ],
        "footer": {"text": f"The Vigil Awakens — {get_human_time()}"},
    }

    async with aiohttp.ClientSession() as session:
        await session.post(config["webhook"], json={"embeds": [embed]})


def get_sse_stream(url, headers):
    return SSEClient(requests.get(url, stream=True, headers=headers))


async def run_listener(config):
    headers = {"User-Agent": config["user_agent"]}
    while True:
        try:
            log_debug("Connecting to SSE stream...")
            response = await asyncio.to_thread(
                get_sse_stream, "https://www.nationstates.net/api/founding", headers
            )
            log_debug("Connected to stream.")
            for raw_event in response.events():
                if raw_event.event != "message" or not raw_event.data:
                    continue
                try:
                    event_data = json.loads(raw_event.data)
                except json.JSONDecodeError:
                    continue
                if not is_valid_event(event_data, config["blacklist"]):
                    continue
                log_debug(f"Valid founding event: {event_data.get('str', '')}")
                nation = extract_target_name(event_data["str"])
                flag_url = extract_flag_url(event_data)
                await send_to_discord(
                    config["webhook"], event_data["str"], [nation], config, flag_url
                )
        except Exception as e:
            log_debug(f"Connection lost: {e}")
            time.sleep(5)


async def main():
    config = setup_config()
    await send_info_embed(config)
    await run_listener(config)


if __name__ == "__main__":
    asyncio.run(main())
