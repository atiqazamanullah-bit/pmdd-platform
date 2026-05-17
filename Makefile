install:
	uv pip install -r requirements.txt

run:
	uvicorn backend.main:app --reload --port 8000

test:
	pytest tests/
