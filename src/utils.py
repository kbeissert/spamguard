"""
Hilfsfunktionen für Spam-Guard
"""

import email
import email.header
import logging
import re
import socket
from typing import Dict, Optional


def decode_header_safe(header_value: str) -> str:
    """
    Dekodiert E-Mail-Header sicher (mit Fallback).

    Args:
        header_value: Roh-Header-Wert

    Returns:
        str: Dekodierter String
    """
    if not header_value:
        return "Kein Wert"

    try:
        decoded_parts = email.header.decode_header(header_value)
        decoded_str = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                # Fix für "unknown-8bit" Encoding Fehler
                current_encoding = encoding
                if current_encoding == "unknown-8bit":
                    current_encoding = "utf-8"

                try:
                    decoded_part = part.decode(current_encoding or "utf-8", errors="replace")
                    decoded_str += decoded_part
                except LookupError:
                    # Fallback für andere unbekannte Encodings
                    decoded_str += part.decode("utf-8", errors="ignore")
            else:
                decoded_str += str(part)

        return decoded_str
    except Exception as e:
        logging.warning(f"Header-Dekodierung fehlgeschlagen: {e}")
        return str(header_value)


def extract_body_preview(msg: email.message.Message) -> str:
    """
    Extrahiert Body-Vorschau aus E-Mail (max 500 Zeichen).

    Args:
        msg: E-Mail-Message-Objekt

    Returns:
        str: Body-Preview (text/plain bevorzugt)
    """
    body = ""

    try:
        if msg.is_multipart():
            # Durchsuche Teile nach text/plain
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode("utf-8", errors="ignore")[:500]
                        break
        else:
            # Einfache Nachricht
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                body = payload.decode("utf-8", errors="ignore")[:500]
    except Exception as e:
        logging.warning(f"Body-Extraktion fehlgeschlagen: {e}")
        body = "[Body konnte nicht dekodiert werden]"

    return body if body else "[Leerer Body]"


# ============================================
# E-Mail-Authentifizierungs-Analyse
# ============================================

# Bekannte lokale/vertrauenswürdige IP-Ranges, die beim Received-Parsen übersprungen werden
_PRIVATE_IP_PREFIXES = (
    "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.",
    "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
    "172.29.", "172.30.", "172.31.", "192.168.", "127.", "::1", "localhost",
)

_AUTH_RESULT_RE = re.compile(
    r"(?:^|\s)(spf|dkim|dmarc)\s*=\s*(\w+)", re.IGNORECASE
)
_RECEIVED_IP_RE = re.compile(
    r"\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]"
)


def extract_auth_results(msg: email.message.Message) -> Dict[str, str]:
    """
    Liest SPF/DKIM/DMARC-Ergebnisse aus dem Authentication-Results Header.

    E-Mail-Provider wie GMX, Web.de und T-Online fügen diesen Header
    beim Empfang ein. Die Ergebnisse können direkt als Spam-Indikator genutzt
    werden, ohne den Body zu analysieren.

    Args:
        msg: Geparste E-Mail

    Returns:
        Dict mit keys 'spf', 'dkim', 'dmarc' → Wert z.B. 'pass', 'fail', 'none'
        Fehlende Einträge werden als 'none' zurückgegeben.
    """
    results: Dict[str, str] = {"spf": "none", "dkim": "none", "dmarc": "none"}

    # Es kann mehrere Authentication-Results Header geben (einer pro Hop)
    for header_value in msg.get_all("Authentication-Results", []):
        for match in _AUTH_RESULT_RE.finditer(header_value):
            key = match.group(1).lower()
            value = match.group(2).lower()
            if key in results:
                # Einmal "fail" bleibt "fail" – höchste Priorität
                if results[key] in ("none", "pass") or value == "fail":
                    results[key] = value

    return results


def extract_sender_ip(msg: email.message.Message) -> Optional[str]:
    """
    Extrahiert die erste externe (nicht-private) Absender-IP aus Received-Headern.

    Die äußersten (letzten eingefügten) Received-Header kommen vom MTA
    des Empfängers. Die erste externe IP ist die des eigentlichen Senders.

    Args:
        msg: Geparste E-Mail

    Returns:
        IP-Adresse als String oder None falls keine externe IP gefunden
    """
    received_headers = msg.get_all("Received", [])

    for header in received_headers:
        for match in _RECEIVED_IP_RE.finditer(header):
            ip = match.group(1)
            if not any(ip.startswith(prefix) for prefix in _PRIVATE_IP_PREFIXES):
                return ip

    return None


# ============================================
# DNSBL-Lookup
# ============================================

# DNSBLs die abgefragt werden (in dieser Reihenfolge, erster Treffer gewinnt)
_DNSBL_SERVERS = [
    ("zen.spamhaus.org", "Spamhaus ZEN (SBL+XBL+PBL)"),
    ("bl.spamcop.net", "SpamCop"),
]
_DNSBL_TIMEOUT_SECONDS = 2


def check_dnsbl(ip: str) -> Optional[str]:
    """
    Prüft eine IP-Adresse in Echtzeit gegen bekannte DNS-Blocklisten (DNSBL).

    Dieser Lookup ist schneller und aktueller als statische Listen, da die
    DNSBL-Server kontinuierlich aktualisiert werden. Kein extra Paket nötig
    – nutzt nur das Python-Standard-socket-Modul.

    Args:
        ip: IPv4-Adresse (z.B. "1.2.3.4")

    Returns:
        Name der DNSBL bei Treffer, None wenn sauber oder Fehler
    """
    try:
        # IP umkehren für DNSBL-Lookup: "1.2.3.4" → "4.3.2.1"
        reversed_ip = ".".join(reversed(ip.split(".")))
    except Exception:
        return None

    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(_DNSBL_TIMEOUT_SECONDS)
    try:
        for dnsbl_host, dnsbl_name in _DNSBL_SERVERS:
            query = f"{reversed_ip}.{dnsbl_host}"
            try:
                socket.gethostbyname(query)
                # DNS-Auflösung erfolgreich → IP ist in der Liste
                logging.debug(f"DNSBL-Treffer: {ip} in {dnsbl_name}")
                return dnsbl_name
            except socket.gaierror:
                # NXDOMAIN = nicht gelistet → weiter zur nächsten DNSBL
                continue
    except Exception as e:
        logging.debug(f"DNSBL-Lookup fehlgeschlagen für {ip}: {e}")
    finally:
        socket.setdefaulttimeout(original_timeout)

    return None
