from pathlib import Path
import re

ROOT = Path(__file__).parent
checks = []


def add(name: str, ok: bool, hint: str = ""):
    checks.append((name, ok, hint))


def read(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""


dockerfile = read("Dockerfile")
compose = read("docker-compose.yml")
main_py = read("app/main.py")
security_py = read("app/security.py")
settings_py = read("app/settings.py")
dockerignore = read(".dockerignore")
gitignore = read(".gitignore")
railway = read("railway.toml")
render = read("render.yaml")

all_repo_text = "\n".join([dockerfile, compose, main_py, security_py, settings_py, railway, render])

add("Dockerfile exists", bool(dockerfile), "Create Dockerfile at repo root")
add("Dockerfile uses multi-stage build", dockerfile.count("FROM ") >= 2, "Use builder + runtime stages")
add("Dockerfile uses slim base", "slim" in dockerfile.lower(), "Prefer python:*‑slim for small runtime")
add("Dockerfile defines non-root user", "USER app" in dockerfile and "adduser" in dockerfile, "Run app as non-root")
add("Dockerfile has HEALTHCHECK", "HEALTHCHECK" in dockerfile, "Add container healthcheck")
add("App binds to PORT env", "${PORT" in dockerfile or "PORT" in settings_py, "Do not hardcode port")
add(".dockerignore exists", bool(dockerignore), "Add .dockerignore")
add(".dockerignore excludes .env", ".env" in dockerignore, "Never copy secrets into image")
add(".gitignore exists", bool(gitignore), "Add .gitignore")
add(".gitignore excludes .env and secrets/", ".env" in gitignore and "secrets/" in gitignore, "Never commit local secrets")
add("docker-compose.yml exists", bool(compose), "Add compose for local parity")
add("docker-compose reads APP_API_KEY from environment", "${APP_API_KEY" in compose, "Use variable interpolation, not a literal key")
add("docker-compose does not hardcode demo API key", "APP_API_KEY: demo-key" not in compose, "Remove APP_API_KEY: demo-key")
add("Settings fail fast if APP_API_KEY is missing", "is required" in settings_py and '_secret_env("APP_API_KEY")' in settings_py, "Avoid silent default secrets")
add("Settings support secret file mount", "APP_API_KEY_FILE" in settings_py or "{name}_FILE" in settings_py, "Support Secret Manager / Docker secret file pattern")
add("/health endpoint exists", '@app.get("/health")' in main_py, "Add GET /health")
add("/ready endpoint exists", '@app.get("/ready")' in main_py, "Add GET /ready")
add("/ask endpoint exists", '@app.post("/ask"' in main_py, "Add POST /ask")
add("API key auth uses X-API-Key", "X-API-Key" in security_py, "Require X-API-Key header")
add("Invalid auth returns 401", "401" in security_py or "HTTP_401" in security_py, "Return 401 when missing key")
add("Rate limiting present", "Rate limit" in security_py or "rate_limit" in security_py, "Add rate limit / cost guard")
add("Cost guard present", "MAX_QUESTION_CHARS" in settings_py and "413" in main_py, "Reject overly long requests")
add("Structured JSON logging present", "JsonFormatter" in read("app/logging_config.py"), "Use JSON logs")
add("Railway config exists", bool(railway), "Add railway.toml")
add("Render config exists", bool(render), "Add render.yaml")
add("Render does not hardcode APP_API_KEY", "sync: false" in render, "Use Render dashboard secret/env var for APP_API_KEY")
add("No obvious real OpenAI-style secret", not re.search(r"sk-[A-Za-z0-9]{20,}", all_repo_text), "Remove real API keys")

passed = sum(1 for _, ok, _ in checks if ok)
print(f"Production readiness: {passed}/{len(checks)} checks passed")
for name, ok, hint in checks:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" - {hint}" if not ok and hint else ""))

if passed != len(checks):
    raise SystemExit(1)
