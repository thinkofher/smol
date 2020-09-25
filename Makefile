include Makefile.venv

NAME=smol
LINE_LENGTH=80

clean: clean-pyc clean-build

clean-pyc:
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

isort: $(VENV)/isort
	$(VENV)/isort */**.py

lint: $(VENV)/flake8
	$(VENV)/flake8 */**.py

fmt: $(VENV)/black
	$(VENV)/black -l $(LINE_LENGTH) $(NAME)

mypy: $(VENV)/mypy
	$(VENV)/mypy $(NAME)
