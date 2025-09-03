.PHONY: install format lint typecheck test run coverage

install:
	poetry install

format:
	poetry run black --line-length 100 src tests

lint:
	poetry run ruff check src tests

typecheck:
	poetry run mypy src

test:
	poetry run pytest tests --cov=src --cov-report=term-missing --cov-fail-under=70

coverage:
	poetry run pytest tests --cov=src --cov-report=html --cov-fail-under=70

run:
	PYTHONPATH=src/ poetry run streamlit run src/app/main.py --server.address=0.0.0.0 --server.port=7860

docker-build:
	docker buildx build -f Dockerfile.prod -t jurisperu-front:0.1.0 .

docker-run:
	docker run -d -p 7860:7860 --name front jurisperu-front:0.1.0

all: install format lint typecheck test
