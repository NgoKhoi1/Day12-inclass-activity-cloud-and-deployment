# Cloud AI Agent Starter Kit

Starter kit cho bài tập lý thuyết 2 giờ: từ `localhost` đến một AI service có dấu hiệu production-ready. Mục tiêu là hiểu kiến trúc, điểm cần lưu ý và quy trình deploy, không phải xây dựng agent phức tạp.

## Bạn sẽ có gì?

- FastAPI service với `/health`, `/ready`, `/ask`
- API key auth qua header `X-API-Key`
- Rate limit đơn giản và cost guard theo độ dài input
- Structured JSON log có `request_id`
- Mock LLM/agent nên không cần OpenAI key thật
- Dockerfile multi-stage, non-root user, HEALTHCHECK
- docker-compose.yml, railway.toml, render.yaml
- check_production_ready.py để tự kiểm tra checklist

## Quy tắc bảo mật secrets trong starter kit

Không đặt secret thật trực tiếp trong `docker-compose.yml`, Dockerfile, source code hoặc tài liệu nộp bài.

Starter kit dùng 3 mức theo đúng mục tiêu bài học:

1. **Local class/dev**: copy `.env.example` thành `.env`, tự đặt `APP_API_KEY` demo riêng, và không commit `.env`.
2. **Free PaaS**: đặt `APP_API_KEY` trong dashboard của Render/Railway dưới dạng secret/env var, không đưa vào Git.
3. **Production/open-source simulation**: dùng Secret Manager, Vault, Kubernetes Secret, hoặc Docker/Compose secrets dạng file mount.

`.env.example` chỉ chứa placeholder để học viên biết cần cấu hình gì. `.env` thật đã được ignore bằng `.gitignore` và `.dockerignore`.

## Chạy local bằng Python

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Mở .env và đổi APP_API_KEY thành một chuỗi demo riêng của bạn
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --reload --port 8000
```

Windows PowerShell:

```powershell
$env:APP_API_KEY="change-me-dev-only-random-32-chars"
uvicorn app.main:app --reload --port 8000
```

> **Quan trọng:** dùng `.venv` riêng cho lab này. **Không** `pip install` vào conda env dùng chung (`ai-lab`, `base`, ...).

## Chạy bằng Docker Compose

```bash
cp .env.example .env
# Mở .env và đổi APP_API_KEY nếu muốn
docker compose up --build
```

Docker Compose sẽ đọc `.env` để thay vào `docker-compose.yml`. Nếu thiếu `APP_API_KEY`, service sẽ báo lỗi ngay thay vì chạy với key mặc định nguy hiểm.

Test:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me-dev-only-random-32-chars" \
  -d '{"question":"Tóm tắt production checklist cho AI agent"}'
```

Nếu bạn đổi `APP_API_KEY` trong `.env`, hãy dùng đúng giá trị đó khi test.

## Tùy chọn nâng cao: Docker/Compose secrets local

Nếu muốn giả lập secret manager thay vì truyền API key qua env var, có thể dùng file secret:

```yaml
services:
  agent:
    build: .
    environment:
      APP_API_KEY_FILE: /run/secrets/app_api_key
      APP_VERSION: 0.1.0
      ENVIRONMENT: local-docker
      MAX_QUESTION_CHARS: 2000
      RATE_LIMIT_PER_MINUTE: 20
      PORT: 8000
    secrets:
      - app_api_key

secrets:
  app_api_key:
    file: ./secrets/app_api_key.txt
```

Tạo file secret local:

```bash
mkdir -p secrets
printf "my-local-demo-key" > secrets/app_api_key.txt
```

Thư mục `secrets/` đã được ignore trong `.gitignore`.

## Tự kiểm tra bài nộp

```bash
python check_production_ready.py
```

## Deploy path gợi ý

### Railway

1. Push repo lên GitHub.
2. Tạo Railway project từ GitHub repo.
3. Set biến môi trường: `APP_API_KEY`, `ENVIRONMENT=production`, `APP_VERSION` trong Railway Variables.
4. Railway sẽ dùng Dockerfile nếu tên file là `Dockerfile`.
5. Health check path: `/health`.

### Render

1. Tạo Web Service từ GitHub repo.
2. Chọn Docker environment.
3. Set env vars: `APP_API_KEY`, `ENVIRONMENT=production`, `APP_VERSION` trong dashboard của Render. Với `render.yaml`, `APP_API_KEY` đang để `sync: false` để không hardcode secret vào file.
4. Health check path: `/health`.

## Nếu lỡ commit secret

1. Rotate/revoke key ngay.
2. Xóa secret khỏi file hiện tại.
3. Nếu repo đã push public hoặc đã chia sẻ, dùng `git filter-repo`/BFG để xóa khỏi lịch sử Git.
4. Bật secret scanning hoặc pre-commit hook cho lần sau.

## Câu hỏi suy nghĩ

- Vì sao service phải đọc `PORT` từ biến môi trường thay vì hardcode `8000`?
- Khác nhau giữa `/health` và `/ready` là gì?
- Vì sao API key không nên nằm trực tiếp trong `docker-compose.yml`?
- API key auth có đủ cho production thật không? Khi nào cần JWT/OAuth?
- Nếu muốn phục vụ 100 người dùng, phần nào cần stateless, phần nào cần shared storage/cache?
- Chúng ta đang thiếu observability nào nếu chỉ có log trên console?
