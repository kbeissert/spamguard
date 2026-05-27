# ============================================
# Spam Guard - Makefile
# ============================================

.PHONY: help start spam unspam unspam-newsletter show-lists audit \
        export-spam export-ham train train-stats train-with-starter \
        load-blacklists benchmark benchmark-quick benchmark-real \
        install clean test status \
        whitelist audit-whitelist audit-blacklist import-starter

# Virtual Environment Settings
VENV   = .venv
PYTHON = $(VENV)/bin/python
PIP    = $(VENV)/bin/pip

# Standard-Target
help:
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║           Spam Guard — Befehlsübersicht              ║"
	@echo "╚══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  ─── Filter ──────────────────────────────────────────"
	@echo "  make start              Spam-Filter starten"
	@echo "  make start DRYRUN=1     Dry-Run (nur anzeigen, nichts verschieben)"
	@echo "  make test               Verbindungstest (Ollama + IMAP)"
	@echo ""
	@echo "  ─── Listen ──────────────────────────────────────────"
	@echo "  make spam <adresse>     Zur Blacklist hinzufügen"
	@echo "  make unspam <adresse>   Zur Whitelist + Mails zurückholen → Posteingang"
	@echo "  make unspam-newsletter <adresse>"
	@echo "                          Spam-Ordner → Newsletter-Ordner (kein Whitelist-Eintrag)"
	@echo "  make show-lists         Whitelist + Blacklist anzeigen"
	@echo "  make audit              Interaktiver Listen-Audit"
	@echo ""
	@echo "  ─── Bayesian Training ───────────────────────────────"
	@echo "  make export-spam        Spam-Mails aus IMAP exportieren"
	@echo "  make export-ham         HAM-Mails aus IMAP exportieren (Sent + INBOX)"
	@echo "  make train              Modell trainieren (data/training/)"
	@echo "  make train-stats        Training-Statistiken anzeigen"
	@echo ""
	@echo "  ─── Blacklists ──────────────────────────────────────"
	@echo "  make load-blacklists    Externe Blacklists herunterladen"
	@echo ""
	@echo "  ─── Benchmark ───────────────────────────────────────"
	@echo "  make benchmark                         Interaktiver Modell-Vergleich (synth.)"
	@echo "  make benchmark-quick                   Schnelltest (5 Mails)"
	@echo "  make benchmark-real                    Real-Mail-Benchmark (Training-Daten)"
	@echo "  make benchmark-real MODEL=gemma3:12b   Direkt mit Modell testen"
	@echo ""
	@echo "  ─── Setup & Wartung ─────────────────────────────────"
	@echo "  make install            Dependencies installieren (.venv)"
	@echo "  make status             Projekt-Status prüfen"
	@echo "  make clean              Cache-Dateien löschen"
	@echo ""

# ============================================
# Filter
# ============================================

start:
	@echo "🛡️  Starte Spam-Filter..."
	@$(PYTHON) src/spam_filter.py $(if $(DRYRUN),--dry-run,)

test:
	@echo "🔍 Verbindungstest..."
	@$(PYTHON) scripts/test_connection.py

# ============================================
# Listen
# ============================================

spam:
	@$(PYTHON) scripts/manage_lists.py blacklist add "$(filter-out $@,$(MAKECMDGOALS))"

unspam:
	@$(PYTHON) scripts/unspam.py $(filter-out $@,$(MAKECMDGOALS)) --auto

unspam-newsletter:
	@$(PYTHON) scripts/unspam_newsletter.py "$(filter-out $@,$(MAKECMDGOALS))"

show-lists:
	@echo "\n📋 --- BLACKLIST ---"
	@$(PYTHON) scripts/manage_lists.py blacklist show
	@echo "\n📋 --- WHITELIST ---"
	@$(PYTHON) scripts/manage_lists.py whitelist show

audit:
	@$(PYTHON) scripts/audit_lists.py

# Versteckte Shortcuts (funktionieren, erscheinen nicht in make help)
whitelist:
	@$(PYTHON) scripts/manage_lists.py whitelist add "$(filter-out $@,$(MAKECMDGOALS))"

audit-whitelist:
	@$(PYTHON) scripts/audit_lists.py --whitelist

audit-blacklist:
	@$(PYTHON) scripts/audit_lists.py --blacklist

# ============================================
# Bayesian Training
# ============================================

export-spam:
	@echo "📦 Exportiere Spam-Mails (Account 0)..."
	@$(PYTHON) scripts/export_training_data.py spam --account 0 --limit 500
	@echo "   → Gespeichert in: data/training/spam/"

export-ham:
	@echo "📦 Exportiere HAM-Mails (Account 0)..."
	@$(PYTHON) scripts/export_training_data.py ham --account 0 --limit 200
	@echo "   → Gespeichert in: data/training/ham/"

train:
	@$(PYTHON) scripts/clean_training.py
	@echo "🤖 Training Bayesian Filter..."
	@$(PYTHON) scripts/train_bayesian.py
	@echo ""
	@echo "✅ Training abgeschlossen! Jetzt: make start"

train-stats:
	@$(PYTHON) scripts/train_bayesian.py --stats

# Versteckter Shortcut: Starter-Samples importieren + trainieren (siehe SETUP.md)
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

train-with-starter:
	@make import-starter
	@make train

# ============================================
# Blacklists
# ============================================

load-blacklists:
	@echo "🌐 Lade externe Blacklists..."
	@$(PYTHON) scripts/load_blacklists.py

# ============================================
# Benchmark
# ============================================

benchmark:
	@$(PYTHON) scripts/benchmark/start_benchmark.py

benchmark-quick:
	@$(PYTHON) scripts/benchmark/start_benchmark.py --quick

benchmark-real:
	@$(PYTHON) scripts/benchmark/real_benchmark.py $(if $(MODEL),--model $(MODEL),) $(if $(LABEL),--label $(LABEL),)

# ============================================
# Setup & Wartung
# ============================================

install:
	@echo "📦 Installiere Dependencies..."
	@python3 -m venv $(VENV)
	@$(PIP) install -e .
	@echo "✅ Fertig!"

status:
	@echo "📊 Projekt-Status:"
	@$(PYTHON) --version
	@echo "Git:" && git status -s || echo "  (kein git)"
	@test -f .env && echo "✅ .env vorhanden" || echo "❌ .env fehlt"

clean:
	@echo "🧹 Räume auf..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .mypy_cache .ruff_cache
	@echo "✅ Sauber!"

# Catch-all für Argumente (z.B. make spam addr@domain.de)
%:
	@:
