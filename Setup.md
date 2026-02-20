# GOAL
Ein CLI-Tool wie "Claude Code" mit Venice Uncensored API zu bauen, das Befehle erkennt und Markdown-Dateien liest, bearbeitet und erstellt – ohne Tool-Use – nutzt du eine pure ReAct-Loop mit File-IO und natürlichem Sprachverständnis. Hier ist der battle-tested Ansatz

## Ansatz

Warum das besser ist als Tools
Keine Tool-Definitionen → Agent versteht natürliche Sprache direkt

100% privat → Nur Venice Uncensored API, keine LangChain Overhead

Schnell → Pure ReAct-Loop, <100ms Latency

Robust → JSON-Output parsing mit fallback zu Raw-Response

Erweiterbar → Einfach neue Actions in _execute_action() hinzufügen

Venice Uncensored Setup
Gehe zu venice.ai, erstelle Pro Account

Settings → Disable Venice System Prompt + Custom System Prompt für maximale Freiheit

API Key generieren → venice_pro_...

Model: venice-uncensored-1.1 oder dolphin-3.0

## Install

pip install typer rich requests
curl -O https://raw.githubusercontent.com/deinname/mdagent/main/mdagent.py
python mdagent.py "test command" 'VENICE-ADMIN-KEY-Lu6azAqQ-wVTQOTny8IJ-XDx1W2xS2Egff9Qb-wthZ'

Das CLI verhält sich exakt wie Claude Code – natürliche Befehle → Agent denkt → File-Änderungen. Kein Tool-Use, pure Intelligenz.