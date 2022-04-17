lint:
	@echo
	isort --diff -c --skip-glob '*.venv' .
	@echo
	blue --check --diff --color .
	@echo
	flake8 .
	@echo
	mypy --ignore-missing-imports .


format_code:
	isort .
	blue .

