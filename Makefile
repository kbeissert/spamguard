# ============================================
# Ollama Spam Guard - Makefile
# ============================================

.PHONY: help start spam unspam whitelist show-lists status install clean test benchmark benchmark-quick

# Virtual Environment Settings
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Standard-Target
help:
	@echo "╔════════════════════════════════════════════╗"
	@echo "║    Ollama Spam Guard - Befehlsübersicht    ║"
	@echo "╚════════════════════════════════════════════╝"
	@echo ""
	@echo "  make start              - Spam-Filter starten"
	@echo ""
	@echo "  Listen verwalten:"
	@echo "  make spam <adresse>     - Als Spam markieren (Blacklist)"
	@echo "                            z.B. make spam werbung@nervig.de"
	@echo "                            z.B. make spam nervig.de"
	@echo ""
	@echo "  make unspam <adresse>   - Kein Spam (Whitelist + Wiederherstellen)"
	@echo "                            z.B. make unspam freund@gut.de"
	@echo ""
	@echo "  make whitelist <adresse>- Nur zur Whitelist hinzufügen (ohne Restore)"
	@echo "  make show-lists         - Alle Listen anzeigen"
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
	@$(PYTHON) src/spam_filter.py

# Als Spam markieren (Blacklist)
spam:
	@$(PYTHON) scripts/manage_lists.py blacklist add "$(filter-out $@,$(MAKECMDGOALS))"

# Kein Spam (Whitelist + Restore)
unspam:
	@$(PYTHON) scripts/unspam.py $(filter-out $@,$(MAKECMDGOALS)) --auto

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
	@$(PIP) install -r requirements.txt
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
