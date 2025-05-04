# Makefile

VENV_PATH := .venv
PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
ACTIVATE := $(VENV_PATH)/bin/activate

.PHONY: init venv install run clean

init: venv install activate

activate:
	chmod +x $(ACTIVATE)

venv:
	python3 -m venv $(VENV_PATH)

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m uvicorn src.app.gateway:app --reload --host 0.0.0.0 --port 5000

clean:
	rm -rf $(VENV_PATH)
