#!/usr/bin/env python3
"""
Test-Modus: Verbindungstest für Ollama, LLM und E-Mail-Accounts
Prüft alle Komponenten ohne E-Mails zu verarbeiten
"""

import sys
from pathlib import Path

# Füge src/ zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
import imaplib
from config import EMAIL_ACCOUNTS, SPAM_MODEL


def print_header(text):
    """Formatierte Überschrift"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_test(name, success, details=""):
    """Formatierte Test-Ausgabe"""
    icon = "✅" if success else "❌"
    status = "OK" if success else "FEHLER"
    print(f"{icon} {name}: {status}")
    if details:
        print(f"   {details}")


def test_ollama_connection():
    """Test 1: Ollama-Verbindung"""
    print_header("Test 1: Ollama-Verbindung")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == requests.codes.ok:
            print_test("Ollama erreichbar", True, "http://localhost:11434")
            return True
        print_test(
            "Ollama erreichbar", False, f"Status Code: {response.status_code}"
        )
        print("\n💡 Lösung:")
        print("   - Starte Ollama: ollama serve")
        print("   - Oder als Dienst: brew services start ollama")
        return False
    except requests.ConnectionError:
        print_test("Ollama erreichbar", False, "Verbindung fehlgeschlagen")
        print("\n💡 Lösung:")
        print("   - Ollama ist nicht gestartet")
        print("   - Starte in neuem Terminal: ollama serve")
        print("   - Oder installiere Ollama: brew install ollama")
        return False
    except Exception as e:
        print_test("Ollama erreichbar", False, str(e))
        return False


def test_ollama_model():
    """Test 2: LLM-Modell verfügbar"""
    print_header(f"Test 2: LLM-Modell '{SPAM_MODEL}'")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != requests.codes.ok:
            print_test("Modell-Liste abrufen", False, "Ollama antwortet nicht")
            return False

        data = response.json()
        models = data.get("models", [])
        model_names = [m["name"] for m in models]

        # Prüfe ob Modell vorhanden (mit und ohne :latest Tag)
        model_found = False
        for model_name in model_names:
            if SPAM_MODEL in model_name or model_name in SPAM_MODEL:
                model_found = True
                break

        if model_found:
            print_test(f"Modell '{SPAM_MODEL}' verfügbar", True)
            print(f"\n📋 Installierte Modelle ({len(models)}):")
            MAX_DISPLAY_MODELS = 5
            for model in models[:MAX_DISPLAY_MODELS]:  # Zeige max 5
                print(f"   - {model['name']}")
            if len(models) > MAX_DISPLAY_MODELS:
                print(f"   ... und {len(models) - MAX_DISPLAY_MODELS} weitere")
            return True
        print_test(f"Modell '{SPAM_MODEL}' verfügbar", False, "Nicht gefunden")
        print("\n💡 Lösung:")
        print(f"   - Installiere Modell: ollama pull {SPAM_MODEL}")
        print("\n📋 Verfügbare Modelle:")
        for model in models[:10]:
            print(f"   - {model['name']}")
        return False

    except Exception as e:
        print_test("Modell-Prüfung", False, str(e))
        return False


def test_email_accounts():
    """Test 3: E-Mail-Account-Verbindungen"""
    print_header(f"Test 3: E-Mail-Accounts ({len(EMAIL_ACCOUNTS)} konfiguriert)")

    all_success = True

    for idx, account in enumerate(EMAIL_ACCOUNTS, 1):
        print(f"\n📬 Account {idx}/{len(EMAIL_ACCOUNTS)}: {account['name']}")
        print(f"   User: {account['user']}")
        print(f"   Server: {account['server']}:{account['port']}")

        try:
            # IMAP-Verbindung
            mail = imaplib.IMAP4_SSL(account["server"], int(account["port"]), timeout=10)
            print_test("SSL-Verbindung", True)

            # Login
            mail.login(account["user"], account["password"])
            print_test("Login", True)

            # INBOX öffnen
            status, data = mail.select("INBOX")
            if status == "OK":
                msg_count = data[0].decode() if data[0] else "0"
                print_test("INBOX", True, f"{msg_count} Nachrichten")
            else:
                print_test("INBOX", False, "Konnte nicht geöffnet werden")
                all_success = False

            # Spam-Ordner prüfen
            try:
                status, data = mail.select(account["spam_folder"])
                if status == "OK":
                    print_test(f"Spam-Ordner '{account['spam_folder']}'", True)
                else:
                    print_test(
                        f"Spam-Ordner '{account['spam_folder']}'",
                        False,
                        "Nicht gefunden",
                    )
                    print("\n💡 Lösung:")
                    print(
                        f"   - Erstelle Ordner '{account['spam_folder']}' im E-Mail-Client"
                    )
                    print("   - Oder passe 'spam_folder' in accounts.yaml an")
                    all_success = False
            except Exception as e:
                print_test(f"Spam-Ordner '{account['spam_folder']}'", False, str(e))
                all_success = False

            mail.logout()

        except imaplib.IMAP4.error as e:
            print_test("IMAP-Verbindung", False, str(e))
            print("\n💡 Lösung:")
            print("   - Prüfe Benutzername und Passwort in accounts.yaml")
            if "gmail" in account["server"].lower():
                print("   - Gmail: Nutze App-Passwort (nicht normales Passwort!)")
                print("   - Erstelle unter: https://myaccount.google.com/apppasswords")
            print("   - Prüfe ob IMAP beim Provider aktiviert ist")
            all_success = False

        except Exception as e:
            print_test("Verbindung", False, str(e))
            print("\n💡 Lösung:")
            print(f"   - Prüfe Server-Adresse: {account['server']}")
            print(f"   - Prüfe Port: {account['port']}")
            print("   - Prüfe Internetverbindung")
            all_success = False

    return all_success


def main():
    """Hauptfunktion: Führe alle Tests aus"""
    print("\n" + "🔍 " + "=" * 58)
    print("  IMAP Spam-Filter: Verbindungstest")
    print("=" * 60)
    print("\nDieser Test prüft alle Verbindungen ohne E-Mails zu verarbeiten.\n")

    results = {"ollama": False, "model": False, "accounts": False}

    # Test 1: Ollama
    results["ollama"] = test_ollama_connection()

    # Test 2: LLM-Modell (nur wenn Ollama läuft)
    if results["ollama"]:
        results["model"] = test_ollama_model()
    else:
        print_header(f"Test 2: LLM-Modell '{SPAM_MODEL}'")
        print("⏭️  Übersprungen (Ollama nicht erreichbar)")

    # Test 3: E-Mail-Accounts
    results["accounts"] = test_email_accounts()

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("  Zusammenfassung")
    print("=" * 60)

    all_passed = all(results.values())

    print_test("Ollama-Verbindung", results["ollama"])
    print_test("LLM-Modell verfügbar", results["model"])
    print_test("E-Mail-Accounts", results["accounts"])

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ Alle Tests erfolgreich!")
        print("   Du kannst jetzt das Spam-Filter-Script ausführen:")
        print("   python src/spam_filter.py")
    else:
        print("❌ Einige Tests sind fehlgeschlagen!")
        print("   Behebe die Probleme und führe den Test erneut aus:")
        print("   python test_connection.py")
    print("=" * 60 + "\n")

    # Exit Code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
