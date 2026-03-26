.PHONY: install api dashboard dev mcp-install

install: api-install mcp-install dashboard-install

api-install:
	cd api && uv venv --python 3.14 .venv && . .venv/bin/activate && uv pip install -r requirements.txt

mcp-install:
	cd mcp_server && uv venv --python 3.14 .venv && . .venv/bin/activate && uv pip install -r requirements.txt

dashboard-install:
	cd dashboard && npm install

api:
	cd api && .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	cd dashboard && npm run dev

dev:
	@trap 'kill 0' EXIT; \
	cd api && .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000 & \
	cd dashboard && npm run dev & \
	wait
