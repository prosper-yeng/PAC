SHELL := /bin/bash
PY := python3

SEED ?= 1337
RELEASE_ID ?= r1
ENVIRONMENT_ID ?= dev
N ?= 5000
CONC ?= 50
POLICY_COMPLEXITY ?= med
BASELINE ?= 0
USE_MIDV500 ?= 0

.PHONY: venv up down restart build-bundle ci exp_rq1 exp_rq2 exp_rq3 analyze figures clean

venv:
	$(PY) -m venv .venv
	. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

build-bundle:
	. .venv/bin/activate && $(PY) scripts/build_bundle.py --complexity $(POLICY_COMPLEXITY)

up:
	RELEASE_ID=$(RELEASE_ID) ENVIRONMENT_ID=$(ENVIRONMENT_ID) docker compose up -d --build

down:
	docker compose down -v

restart:
	docker compose restart opa identity-api collector

ci:
	. .venv/bin/activate && $(PY) scripts/run_ci_checks.py

exp_rq1:
	. .venv/bin/activate && SEED=$(SEED) USE_MIDV500=$(USE_MIDV500) $(PY) scripts/experiments/exp_rq1.py

exp_rq2:
	. .venv/bin/activate && $(PY) scripts/experiments/exp_rq2.py

exp_rq3:
	. .venv/bin/activate && SEED=$(SEED) N=$(N) CONC=$(CONC) POLICY_COMPLEXITY=$(POLICY_COMPLEXITY) BASELINE=$(BASELINE) $(PY) scripts/experiments/exp_rq3.py

analyze:
	. .venv/bin/activate && $(PY) scripts/analyze/all_metrics.py

figures:
	. .venv/bin/activate && $(PY) scripts/analyze/make_figures.py

clean:
	rm -rf out .pytest_cache __pycache__
