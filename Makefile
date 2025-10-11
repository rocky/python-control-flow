.PHONY: check

GIT2CL ?= git2cl
PYTHON ?= python
PYTHON3 ?= python3
RM      ?= rm
LINT    = flake8

PHONY=all check-pytest check

#: Run pytest tests
check-pytest:
	pytest pytest

#: Run all tests, pytest and integration examples
check: check-pytest check-examples

#: Run integration test examples
check-examples:
	python test/test-all-examples.py


#: Clean up temporary files and .pyc files
clean:
	$(PYTHON) ./setup.py $@
	find . -name __pycache__ -exec rm -fr {} \; || true

rmChangeLog:
	rm ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@
	patch ChangeLog < ChangeLog-spell-corrected.diff

#: Create source (tarball) and wheel distribution
dist: clean
	./admin-tools/make-dist-newest.sh
