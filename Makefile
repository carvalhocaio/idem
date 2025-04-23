run:
	streamlit run __init__.py

lint:
	ruff check . && ruff check . --diff

format:
	ruff check . --fix && ruff format .