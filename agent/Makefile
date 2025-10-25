.PHONY: clean run

clean:
	find app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find app -name "*.pyc" -delete 2>/dev/null || true
	@echo "🧹 Cleaned __pycache__ and .pyc files"

run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload