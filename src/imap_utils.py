"""
IMAP Connection Utilities for SpamGuard

Provides context manager and helper functions for safe IMAP connections
with guaranteed cleanup even on exceptions.

Centralized IMAP handling to eliminate code duplication and prevent
connection leaks across the codebase.
"""

import imaplib
import logging
from typing import Dict, Optional
from contextlib import contextmanager


@contextmanager
def imap_connection(account: Dict[str, str], select_folder: Optional[str] = "INBOX"):
    """
    Context manager for IMAP connections.

    Guarantees proper cleanup (expunge, close, logout) even if exceptions occur.
    Automatically handles connection setup, login, and folder selection.

    Args:
        account: Account configuration dict with keys:
            - server: IMAP server hostname
            - port: IMAP server port (usually 993)
            - user: Email username/address
            - password: Email password
            - name: Display name for logging
        select_folder: Folder to open after login. None to skip selection.

    Yields:
        IMAP4_SSL: Connected mail object ready for operations

    Raises:
        imaplib.IMAP4.error: If login or folder selection fails
        Exception: Any other connection errors

    Example:
        >>> account = {"server": "imap.gmail.com", "port": 993, ...}
        >>> with imap_connection(account, "INBOX") as mail:
        ...     status, data = mail.search(None, "ALL")
        ...     # Connection automatically cleaned up, even if error occurs
    """
    mail = None
    try:
        # Step 1: Connect
        print(f"🔌 Verbinde zu {account['server']}:{account['port']}...")
        mail = imaplib.IMAP4_SSL(account["server"], int(account["port"]))
        logging.debug(f"SSL connection established to {account['server']}")

        # Step 2: Login
        print(f"🔐 Login {account['name']}...")
        mail.login(account["user"], account["password"])
        logging.info(f"Successfully logged in: {account['name']}")

        # Step 3: Select folder (optional)
        if select_folder:
            print(f"📁 Öffne '{select_folder}'...")
            status = mail.select(select_folder)
            if status[0] != "OK":
                raise RuntimeError(f"Cannot open folder: {select_folder}")
            logging.debug(f"Folder selected: {select_folder}")

        yield mail

    except imaplib.IMAP4.error as e:
        # IMAP-specific errors (login failed, bad credentials, etc.)
        logging.error(f"IMAP-Fehler für {account['user']}: {e}", exc_info=True)
        print(f"❌ IMAP-Fehler: {e}")
        raise

    finally:
        # Cleanup: Always executed, even on exception
        if mail:
            try:
                print("🧹 Räume auf...")
                try:
                    mail.expunge()  # Delete marked emails
                    logging.debug("Emails expunged")
                except Exception as e:
                    logging.warning(f"Expunge failed: {e}")

                try:
                    mail.close()  # Close folder
                    logging.debug("Folder closed")
                except Exception as e:
                    logging.warning(f"Close failed: {e}")

                try:
                    mail.logout()  # Logout
                    print("✅ IMAP-Verbindung geschlossen")
                    logging.info("IMAP connection closed")
                except Exception as e:
                    logging.warning(f"Logout failed: {e}")

            except Exception as cleanup_error:
                # Even cleanup can fail - log it but don't raise
                logging.error(f"Cleanup error: {cleanup_error}", exc_info=True)


def safe_connect_imap(account: Dict[str, str]) -> imaplib.IMAP4_SSL:
    """
    Simple IMAP connection without folder selection (legacy support).

    This is a simpler version for scripts that manage their own folder selection.
    Consider using imap_connection() context manager for safety.

    Args:
        account: Account configuration dict

    Returns:
        Connected IMAP4_SSL object

    Raises:
        imaplib.IMAP4.error: Connection or login failed
    """
    try:
        print(f"🔌 Verbinde zu {account['server']}:{account['port']}...")
        mail = imaplib.IMAP4_SSL(account["server"], int(account["port"]))
        logging.debug(f"Connected to {account['server']}")

        print(f"🔐 Login {account['name']}...")
        mail.login(account["user"], account["password"])
        logging.info(f"Logged in: {account['name']}")

        return mail

    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP-Fehler für {account['user']}: {e}", exc_info=True)
        print(f"❌ IMAP-Fehler: {e}")
        raise
    except Exception as e:
        logging.error(f"Verbindungsfehler zu {account['server']}:{account['port']}: {e}", exc_info=True)
        print(f"❌ Verbindungsfehler: {e}")
        raise
