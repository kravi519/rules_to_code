.PHONY: test score demo verify baseline manifest

REPEAT ?= 1

test:
	python3 -m pytest tests/ -v

score:
	python3 eval/score.py --repeat $(REPEAT)

demo:
	python3 demo.py

verify:
	python3 tools/manifest.py check

manifest:
	python3 tools/manifest.py write

baseline:
	python3 run.py baseline
