#!/usr/bin/env python3
"""
Undo Restore - Verschiebt fälschlich wiederhergestellte Mails zurück in den Spam-Ordner.
"""

import imaplib
import email
from typing import Dict

from config import EMAIL_ACCOUNTS
from imap_utils import imap_connection

# Liste der fälschlich wiederhergestellten Absender (aus dem Log extrahiert)
TARGET_SENDERS = [
    "info@bindymorris.com",
    "info@sinhalavoiceover.lk",
    "contact@roonlabs.com",
    "Noreply@kidneycentre.com",
    "info@bobsbonsai.com",
    "Unbekannt",
    "EiwnAZY@sumyvnctsfm.com",
    "123-ownership@services.secureserver.net",
    "no-reply@notify.incogni.com",
    "Marcel.Eichenseher@jobcenter-ge.de",
    "noreply@service.dpd.de",
    "advertise-noreply@global.metamail.com",
    "hello@tradingview.com",
    "info@kartepepalet.com",
    "Contact@7407.de",
    "support@ezpztrading.com",
    "info@sandmaik.com",
    "jochen.krah@t-online.de",
    "info@getquin.com",
    "mail@news.dasunglaublichesangebot.de",
    "promotion5@amazon.de",
    "marketplace-messages@amazon.de",
    "noreply@apac.ph.mc.philips.com",
    "info@geassessoria.com.br",
    "mail@mt.hotelairportguayaquil.com",
    "office@pulxsoftsolutions.com",
    "gemma@cherrypickpeople.com",
    "no.replyauth.delivery556256346@admin9999.com",
    "news@mackenzie-childs.com",
    "info@pip.rfn.mybluehost.me",
    "eveho@acquis08.com",
    "info@mannativf.com",
    "no-reply@mail.nordvpn.com",
    "arreza.akbar@tepianteknologi.com",
    "info@oikovosconsultores.com.mx",
    "tm@dkmc24.com",
    "mail@lottonews-service.com",
    "broligarchy@substack.com",
    "info@ranchodasviolasfm.com.br",
    "info@serviciosdecontrol.com",
    "reset@jmbb.gatmoxjadpnfilhr.top",
    "verify@4jfvk.fgkhnegomhpz.top",
    "onlinebank@dko.mvpiycnszrewnx.top",
    "jimmy@quantumteknologi.com",
    "geli.kraut@t-online.de",
    "f.jamil@bic.com.bh",
    "picostore@email.picoxr.com",
    "info@alt205.com",
    "mailtest@touchgame.net",
    "banking@a2ofz.pt588.cc",
    "sales@clouding.io",
    "reset@5160i.73mei.cc",
    "info@weddingvideosrilanka.lk",
    "info@howtomeasurecobb.com",
    "nicht-antworten@forum.szas.org",
    "noreply@tradingview.com",
    "info@equinestar.net",
    "noreply@gobuyside.com",
    "onlineshop@mediamarkt.de",
    "hello@email.tidal.com",
    "mailmagazine@mail3.lifeinsuraunce.it.com",
    "Zahlung-Abgelehnt@resend.dev",
    "CloudSpeicher@resend.dev",
    "kontakt@fetisch.de",
    "ADAC-Mitgliedschaft@resend.dev",
    "info-CloudSpeicher@resend.dev",
    "noreply-CloudSpeicher@resend.dev",
    "streamswave@amatrans.com",
    "Cloud-Speicher@amatrans.com",
    "info-Cloud-Speicher@amatrans.com",
    "support-Cloud-Speicher@amatrans.com",
    "alert-Cloud-Speicher@academie-ent.com",
    "ADAC-Mitgliedschaft@amatrans.com",
    "cassouad@pinterest.com",
    "lschulte@pinterest.com"
]

# Diese NICHT zurückschieben (Google Ads)
WHITELISTED = [
    "ads-noreply@google.com",
    "payments-noreply@google.com"
]

def _try_move_email(
    mail: imaplib.IMAP4_SSL,
    email_id: bytes,
    account: Dict[str, str],
) -> int:
    """Fetch one email and move it back to spam if it matches. Returns 1 if moved, 0 otherwise."""
    status, msg_data = mail.fetch(email_id, "(RFC822.HEADER)")
    if status != "OK":
        return 0

    msg = email.message_from_bytes(msg_data[0][1])
    sender = email.utils.parseaddr(msg.get("From", ""))[1]

    if sender not in TARGET_SENDERS or sender in WHITELISTED:
        return 0

    print(f"   🔙 Verschiebe zurück in Spam: {sender}")
    res, _ = mail.copy(email_id, account["spam_folder"])
    if res == "OK":
        mail.store(email_id, "+FLAGS", "\\Deleted")
        return 1

    print(f"   ❌ Fehler beim Verschieben von {sender}")
    return 0


def undo_restore():
    print("🛡️  Starte Undo-Restore...")
    print(f"ℹ️  Suche nach {len(TARGET_SENDERS)} Absendern im Posteingang...")

    for account in EMAIL_ACCOUNTS:
        print(f"\n📬 Account: {account['name']}")
        try:
            with imap_connection(account, "INBOX") as mail:
                status, data = mail.search(None, "ALL")
                if status != "OK" or not data[0]:
                    print("   Posteingang leer oder Fehler.")
                    continue

                email_ids = data[0].split()
                print(f"   Prüfe {len(email_ids)} E-Mails im Posteingang...")

                moved_count = 0
                for email_id in email_ids:
                    try:
                        moved_count += _try_move_email(mail, email_id, account)
                    except Exception as e:
                        print(f"   Fehler bei Mail-ID {email_id}: {e}")

            print(f"   ✅ {moved_count} E-Mails zurück in Spam verschoben.")

        except Exception as e:
            print(f"   ❌ Fehler bei Account {account['name']}: {e}")

if __name__ == "__main__":
    undo_restore()
