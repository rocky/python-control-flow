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
check: check-pytest check_examples

#: Run integration test examples
check-examples:
	python test/test-all-examples.py


#: Clean up temporary files and .pyc files
clean: clean_pyc
	$(PYTHON) ./setup.py $@
	find . -name __pycache__ -exec rm -fr {} \; || true
	(cd test && $(MAKE) clean)
	(cd test_unit && $(MAKE) clean)

#: Create source (tarball) and wheel distribution
dist: clean
	$(PYTHON) ./setup.py sdist bdist_egg
