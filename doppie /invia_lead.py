#!/usr/bin/env python3
"""
Script per inviare lead doppie a Squidbomb API.
Legge lead da leadinviare.md, invia a Squidbomb, aggiorna status nel file.
"""

import requests
import random
import time
import os

# ============ CONFIG ============
API_URL = "https://offers.squidbomb.net/forms/api/"
UID = "019c4347-d9b5-7b2b-8fcc-23443e24b76c"
KEY = "38b4aea53d4c8a50135870"
OFFER = "258"
LP = "279"

LEAD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leadinviare.md")

# ============ ITALIAN IP RANGES ============
# Common Italian ISP IP ranges (Telecom Italia, Vodafone IT, Wind, Fastweb)
ITALIAN_IP_RANGES = [
    ("2.32.", 0, 255),      # Vodafone IT
    ("2.34.", 0, 255),      # Vodafone IT
    ("5.90.", 0, 255),      # Fastweb
    ("5.94.", 0, 255),      # Fastweb
    ("37.160.", 0, 255),    # Telecom Italia
    ("37.161.", 0, 255),    # Telecom Italia
    ("37.162.", 0, 255),    # Telecom Italia
    ("79.18.", 0, 255),     # Telecom Italia
    ("79.20.", 0, 255),     # Telecom Italia
    ("79.22.", 0, 255),     # Telecom Italia
    ("80.180.", 0, 255),    # Telecom Italia
    ("80.181.", 0, 255),    # Telecom Italia
    ("82.48.", 0, 255),     # Telecom Italia
    ("82.50.", 0, 255),     # Telecom Italia
    ("82.52.", 0, 255),     # Telecom Italia
    ("87.1.", 0, 255),      # Fastweb
    ("87.5.", 0, 255),      # Fastweb
    ("93.34.", 0, 255),     # Telecom Italia
    ("93.36.", 0, 255),     # Telecom Italia
    ("93.38.", 0, 255),     # Telecom Italia
    ("151.24.", 0, 255),    # Telecom Italia
    ("151.26.", 0, 255),    # Telecom Italia
    ("151.28.", 0, 255),    # Telecom Italia
    ("176.200.", 0, 255),   # Vodafone IT
    ("176.202.", 0, 255),   # Vodafone IT
    ("188.152.", 0, 255),   # Wind
    ("188.153.", 0, 255),   # Wind
]


def generate_italian_ip():
    """Generate a random Italian IP address."""
    prefix, low, high = random.choice(ITALIAN_IP_RANGES)
    octet3 = random.randint(low, high)
    octet4 = random.randint(1, 254)
    return f"{prefix}{octet3}.{octet4}"


# ============ USER AGENTS ============
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.178 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


def generate_user_agent():
    """Pick a random realistic user agent."""
    return random.choice(USER_AGENTS)


def parse_leads(filepath):
    """Parse leads from the markdown file."""
    leads = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if i == 0:  # Skip header
            continue
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 4:
            leads.append({
                "line_num": i,
                "data": parts[0].strip(),
                "name": parts[1].strip(),
                "phone": parts[2].strip(),
                "address": parts[3].strip(),
            })
    return leads, lines


def send_lead(lead):
    """Send a single lead to Squidbomb API."""
    ip = generate_italian_ip()
    ua = generate_user_agent()

    payload = {
        "uid": UID,
        "key": KEY,
        "offer": OFFER,
        "lp": LP,
        "name": lead["name"],
        "tel": lead["phone"],
        "street-address": lead["address"],
        "ip": ip,
        "ua": ua,
    }

    print(f"\n📤 Invio: {lead['name']} | {lead['phone']} | {lead['address']}")
    print(f"   IP: {ip} | UA: {ua[:50]}...")

    try:
        response = requests.post(API_URL, data=payload, timeout=30)
        print(f"   Status: {response.status_code} | Response: {response.text}")
        return {
            "status_code": response.status_code,
            "message": response.text.strip(),
            "ip": ip,
        }
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return {
            "status_code": 0,
            "message": f"ERROR: {e}",
            "ip": ip,
        }


def update_lead_file(filepath, leads, results):
    """Update the lead file with send status."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Rebuild with status column
    new_lines = []
    header = lines[0].strip()
    if "status" not in header.lower():
        new_lines.append(header + "\tstatus\n")
    else:
        new_lines.append(lines[0])

    result_map = {lead["line_num"]: results[i] for i, lead in enumerate(leads) if i < len(results)}

    for i, line in enumerate(lines):
        if i == 0:
            continue
        stripped = line.strip()
        if not stripped:
            continue

        if i in result_map:
            r = result_map[i]
            status = f"✅ {r['status_code']} - {r['message']}" if r["status_code"] == 200 else f"❌ {r['status_code']} - {r['message']}"
            # Remove old status if present (5th column)
            parts = stripped.split("\t")
            base = "\t".join(parts[:4])
            new_lines.append(f"{base}\t{status}\n")
        else:
            new_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def main():
    print("=" * 60)
    print("🚀 INVIO LEAD A SQUIDBOMB")
    print("=" * 60)

    leads, original_lines = parse_leads(LEAD_FILE)
    print(f"\n📋 Trovate {len(leads)} lead da inviare\n")

    if not leads:
        print("Nessuna lead trovata!")
        return

    results = []
    for i, lead in enumerate(leads):
        print(f"\n--- Lead {i+1}/{len(leads)} ---")
        result = send_lead(lead)
        results.append(result)
        # Pausa tra invii per non sembrare bot
        if i < len(leads) - 1:
            delay = random.uniform(2, 5)
            print(f"   ⏳ Attendo {delay:.1f}s...")
            time.sleep(delay)

    # Aggiorna file con status
    update_lead_file(LEAD_FILE, leads, results)

    # Riepilogo
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO")
    print("=" * 60)
    ok = sum(1 for r in results if r["status_code"] == 200)
    fail = len(results) - ok
    print(f"   ✅ Successo: {ok}")
    print(f"   ❌ Falliti:  {fail}")
    print(f"   📝 File aggiornato: {LEAD_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
