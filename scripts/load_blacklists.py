#!/usr/bin/env python3
"""
Lädt externe Blacklists herunter und speichert sie in data/lists/external/.

Konfiguration: config/blacklists.yaml
Ziel:          data/lists/external/

Nutzung:
    make load-blacklists
    python scripts/load_blacklists.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from list_manager import ListManager


def main() -> None:
    print("🌐 Lade externe Blacklists herunter...")
    print("   Konfiguration: config/blacklists.yaml")
    print("   Ziel:          data/lists/external/")
    print()

    manager = ListManager()
    manager._load_external_blacklists(force_update=True)

    print()
    ip_count = len(manager.blacklist.ips)
    cidr_count = len(manager.blacklist.cidr_networks)
    domain_count = len(manager.blacklist.domains)
    print(f"✅ Fertig!")
    print(f"   IPs:          {ip_count}")
    print(f"   CIDR-Netze:   {cidr_count}")
    print(f"   Domains:      {domain_count}")


if __name__ == "__main__":
    main()
