# Makefile for Know Tool Installation

PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
LIBDIR = $(PREFIX)/lib/know
MANDIR = $(PREFIX)/share/man/man1
COMPLETIONDIR_BASH = /etc/bash_completion.d
COMPLETIONDIR_ZSH = /usr/share/zsh/site-functions

PYTHON := python3
PIP := pip3

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
NC := \033[0m

.PHONY: all install uninstall test clean user-install dev help

help:
	@echo "Know Tool Installation"
	@echo "======================"
	@echo ""
	@echo "Available targets:"
	@echo "  make install       - Install system-wide (requires sudo)"
	@echo "  make user-install  - Install for current user only"
	@echo "  make dev           - Install in development mode"
	@echo "  make test          - Run test suite"
	@echo "  make uninstall     - Remove installation"
	@echo "  make clean         - Clean build artifacts"
	@echo ""
	@echo "Options:"
	@echo "  PREFIX=/path       - Change installation prefix (default: /usr/local)"

all: install

check-python:
	@which $(PYTHON) > /dev/null || (echo "$(RED)Python 3 is required$(NC)" && exit 1)
	@echo "$(GREEN)✓ Python 3 found$(NC)"

check-root:
	@if [ "$$(id -u)" != "0" ]; then \
		echo "$(RED)This target requires root access. Use 'sudo make install'$(NC)"; \
		exit 1; \
	fi

install: check-python check-root
	@echo "Installing Know Tool to $(PREFIX)..."

	# Create directories
	@mkdir -p $(LIBDIR)
	@mkdir -p $(BINDIR)
	@mkdir -p $(MANDIR)
	@mkdir -p $(COMPLETIONDIR_BASH)

	# Copy library files
	@cp -r src $(LIBDIR)/
	@cp know.py $(LIBDIR)/know.py

	# Create executable
	@echo '#!/usr/bin/env bash' > $(BINDIR)/know
	@echo 'exec python3 $(LIBDIR)/know.py "$$@"' >> $(BINDIR)/know
	@chmod +x $(BINDIR)/know

	# Install completions
	@cp completions/know.bash $(COMPLETIONDIR_BASH)/know 2>/dev/null || true
	@cp completions/know.zsh $(COMPLETIONDIR_ZSH)/_know 2>/dev/null || true

	@echo "$(GREEN)✓ Installation complete$(NC)"
	@echo "Run 'know --help' to get started"

user-install: check-python
	@echo "Installing Know Tool for user..."

	# Create user directories
	@mkdir -p ~/.local/lib/know
	@mkdir -p ~/.local/bin
	@mkdir -p ~/.local/venvs

	# Create user venv
	@$(PYTHON) -m venv ~/.local/venvs/know 2>/dev/null || true
	@~/.local/venvs/know/bin/pip install --quiet click pydantic networkx rich aiofiles python-dotenv 2>/dev/null || true

	# Copy files
	@cp -r src ~/.local/lib/know/
	@cp know.py ~/.local/lib/know/know.py

	# Create user executable that uses the venv
	@echo '#!/usr/bin/env bash' > ~/.local/bin/know
	@echo 'VENV_PYTHON="$$HOME/.local/venvs/know/bin/python3"' >> ~/.local/bin/know
	@echo 'if [ -f "$$VENV_PYTHON" ]; then' >> ~/.local/bin/know
	@echo '    exec "$$VENV_PYTHON" ~/.local/lib/know/know.py "$$@"' >> ~/.local/bin/know
	@echo 'else' >> ~/.local/bin/know
	@echo '    exec python3 ~/.local/lib/know/know.py "$$@"' >> ~/.local/bin/know
	@echo 'fi' >> ~/.local/bin/know
	@chmod +x ~/.local/bin/know

	# Setup completions for user
	@mkdir -p ~/.config/bash_completion.d
	@cp completions/know.bash ~/.config/bash_completion.d/know 2>/dev/null || true

	@echo "$(GREEN)✓ User installation complete$(NC)"
	@echo ""
	@echo "Add to your shell configuration:"
	@echo "  export PATH=~/.local/bin:\$$PATH"
	@echo ""
	@echo "For bash completions, add:"
	@echo "  source ~/.config/bash_completion.d/know"

dev: check-python
	@echo "Setting up development environment..."

	# Create virtual environment
	@$(PYTHON) -m venv venv || true

	# Install in editable mode
	@echo '#!/usr/bin/env bash' > know-dev
	@echo 'exec python3 know.py "$$@"' >> know-dev
	@chmod +x know-dev

	# Try to install dependencies
	@$(PIP) install -r requirements.txt 2>/dev/null || \
		echo "$(YELLOW)Optional dependencies not installed$(NC)"

	@echo "$(GREEN)✓ Development setup complete$(NC)"
	@echo "Use './know-dev' for testing"

test: check-python
	@echo "Running test suite..."
	@$(PYTHON) -m pytest tests/ -v || $(PYTHON) tests/test_graph.py

uninstall: check-root
	@echo "Uninstalling Know Tool..."
	@rm -rf $(LIBDIR)
	@rm -f $(BINDIR)/know
	@rm -f $(COMPLETIONDIR_BASH)/know
	@rm -f $(COMPLETIONDIR_ZSH)/_know
	@rm -f $(MANDIR)/know.1
	@echo "$(GREEN)✓ Uninstalled$(NC)"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf venv
	@rm -f know-dev
	@rm -rf __pycache__
	@rm -rf src/__pycache__
	@rm -rf tests/__pycache__
	@rm -rf .pytest_cache
	@find . -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleaned$(NC)"

.PHONY: package
package:
	@echo "Creating distribution package..."
	@tar -czf know-tool.tar.gz \
		src/ \
		tests/ \
		know.py \
		requirements.txt \
		Makefile \
		install.sh \
		README.md
	@echo "$(GREEN)✓ Package created: know-tool.tar.gz$(NC)"