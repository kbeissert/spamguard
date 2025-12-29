"""
Hilfsfunktionen für Spam-Guard
"""

import email
import email.header
import logging


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
                if encoding == "unknown-8bit":
                    encoding = "utf-8"

                try:
                    decoded_str += part.decode(encoding or "utf-8", errors="ignore")
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
