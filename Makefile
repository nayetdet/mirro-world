.PHONY: install run

install:
	uv sync --all-groups --all-packages

run:
	uv run python -m mirro-world
