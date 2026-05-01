FROM node:22-alpine AS frontend
WORKDIR /app
COPY client/package.json client/pnpm-lock.yaml ./client/
RUN corepack enable && pnpm install --frozen-lockfile --prefix client
COPY client/ client/
RUN pnpm run build --prefix client

FROM python:3.12-slim
WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ .
COPY --from=frontend /app/client/dist ./static
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
