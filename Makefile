# ============================================
# Spam Guard - Makefile
# ============================================

.PHONY: help start spam unspam unspam-newsletter whitelist show-lists status install clean test benchmark benchmark-quick export-spam export-ham train train-stats import-starter train-with-starter

# Virtual Environment Settings
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Standard-Target
help:
	@echo "╔════════════════════════════════════════════╗"
	@echo "║        Spam Guard - Befehlsübersicht       ║"
	@echo "╚════════════════════════════════════════════╝"
	@echo ""
	@echo "  make start              - Spam-Filter starten"
	@echo "  make start DRYRUN=1     - Dry-Run (nur anzeigen, nichts verschieben)"
	@echo ""
	@echo "  Listen verwalten:"
	@echo "  make spam <adresse>     - Als Spam markieren (Blacklist)"
	@echo "                            z.B. make spam werbung@nervig.de"
	@echo "                            z.B. make spam nervig.de"
	@echo ""
	@echo "  make unspam <adresse>   - Kein Spam (Whitelist + Wiederherstellen → Posteingang)"
	@echo "                            z.B. make unspam freund@gut.de"
	@echo ""
	@echo "  make unspam-newsletter <adresse> - Newsletter aus Spam → Newsletter-Ordner"
	@echo "                            z.B. make unspam-newsletter news@substack.com"
	@echo "                            z.B. make unspam-newsletter substack.com"
	@echo ""
	@echo "  make whitelist <adresse>- Nur zur Whitelist hinzufügen (ohne Restore)"
	@echo "  make show-lists         - Alle Listen anzeigen"
	@echo ""
	@echo "  Bayesian Training:"
	@echo "  make train              - Trainiere Modell aus data/training/{spam,ham}/"
	@echo "  make train-stats        - Zeige Training-Statistiken"
	@echo "  make export-spam        - Exportiere Spam-Mails aus IMAP"
	@echo "  make export-ham         - Exportiere HAM-Mails aus IMAP (Sent+INBOX)"
	@echo "  make train-with-starter - Schnellstart mit Starter-Samples"
	@echo ""
	@echo "  Benchmark:"
	@echo "  make benchmark          - Interaktiver Modell-Vergleich"
	@echo "  make benchmark-quick    - Schneller Test (5 Mails)"
	@echo ""
	@echo "  Wartung:"
	@echo "  make status             - System-Status prüfen"
	@echo "  make install            - Installation / Update"
	@echo "  make clean              - Aufräumen"
	@echo "  make test               - Verbindungstest"
	@echo ""

# --------------------------------------------
# Hauptbefehle
# --------------------------------------------

start:
	@echo "🛡️  Starte Spam-Filter..."
	@$(PYTHON) src/spam_filter.py $(if $(DRYRUN),--dry-run,)

# Als Spam markieren (Blacklist)
spam:
	@$(PYTHON) scripts/manage_lists.py blacklist add "$(filter-out $@,$(MAKECMDGOALS))"

# Kein Spam (Whitelist + Restore → Posteingang)
unspam:
	@$(PYTHON) scripts/unspam.py $(filter-out $@,$(MAKECMDGOALS)) --auto

# Newsletter aus Spam → Newsletter-Ordner
unspam-newsletter:
	@$(PYTHON) scripts/unspam_newsletter.py "$(filter-out $@,$(MAKECMDGOALS))"

# Zur Whitelist hinzufügen
whitelist:
	@$(PYTHON) scripts/manage_lists.py whitelist add "$(filter-out $@,$(MAKECMDGOALS))"

# Listen anzeigen
show-lists:
	@echo "\n📋 --- BLACKLIST ---"
	@$(PYTHON) scripts/manage_lists.py blacklist show
	@echo "\n📋 --- WHITELIST ---"
	@$(PYTHON) scripts/manage_lists.py whitelist show

# --------------------------------------------
# Bayesian Training
# --------------------------------------------

# Exportiere Spam-Mails aus IMAP Spam-Ordner
export-spam:
	@echo "📦 Exportiere Spam-Mails (Account 0)..."
	@$(PYTHON) scripts/export_training_data.py spam --account 0 --limit 500
	@echo "   → Gespeichert in: data/training/spam/"

# Exportiere HAM-Mails aus Sent-Ordner + INBOX
export-ham:
	@echo "📦 Exportiere HAM-Mails (Account 0)..."
	@$(PYTHON) scripts/export_training_data.py ham --account 0 --limit 200
	@echo "   → Gespeichert in: data/training/ham/"

# Trainiere Bayesian-Modell aus .eml Dateien
train:
	@$(PYTHON) scripts/clean_training.py
	@echo "🤖 Training Bayesian Filter..."
	@$(PYTHON) scripts/train_bayesian.py
	@echo ""
	@echo "✅ Training abgeschlossen! Jetzt: make start"

# Zeige Training-Statistiken
train-stats:
	@$(PYTHON) scripts/train_bayesian.py --stats

# Importiere Starter-Samples
import-starter:
	@echo "📦 Importiere Starter-Samples..."
	@if [ -d "data/training/starter/spam" ]; then \
		cp data/training/starter/spam/*.eml data/training/spam/ 2>/dev/null || true; \
		cp data/training/starter/ham/*.eml data/training/ham/ 2>/dev/null || true; \
		echo "✅ Import abgeschlossen"; \
		echo "   → $(shell ls data/training/spam/*.eml 2>/dev/null | wc -l | xargs) Spam"; \
		echo "   → $(shell ls data/training/ham/*.eml 2>/dev/null | wc -l | xargs) HAM"; \
		echo ""; \
		echo "   Jetzt: make train"; \
	else \
		echo "⚠️  Keine Starter-Samples gefunden in data/training/starter/"; \
		echo "   Nutze stattdessen: make export-spam && make export-ham"; \
	fi

# Schnellstart: Starter-Samples importieren + trainieren
train-with-starter:
	@make import-starter
	@make train

# --------------------------------------------
# Benchmark
# --------------------------------------------

# Benchmark starten (Interaktiv)
benchmark:
	@$(PYTHON) scripts/benchmark/start_benchmark.py

# Benchmark Quick-Test (5 Mails)
benchmark-quick:
	@$(PYTHON) scripts/benchmark/start_benchmark.py --quick

# --------------------------------------------
# Wartung & Setup
# --------------------------------------------

status:
	@echo "📊 Projekt-Status:"
	@$(PYTHON) --version
	@echo "Git:" && git status -s || echo "  (kein git)"
	@test -f .env && echo "✅ .env vorhanden" || echo "❌ .env fehlt"

install:
	@echo "📦 Installiere Dependencies..."
	@python3 -m venv $(VENV)
	@$(PIP) install -e .
	@echo "✅ Fertig!"

clean:
	@echo "🧹 Räume auf..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .mypy_cache .ruff_cache
	@echo "✅ Sauber!"

test:
	@echo "🔍 Verbindungstest..."
	@$(PYTHON) scripts/test_connection.py

# Catch-all für Argumente
%:
	@:
