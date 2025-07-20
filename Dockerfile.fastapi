FROM node:18 AS frontend-builder
WORKDIR /app
COPY client/package.json client/pnpm-lock.yaml* ./client/
RUN npm install -g pnpm && \
    cd client && \
    pnpm install --frozen-lockfile
COPY client ./client
RUN cd client && \
    pnpm run build

FROM python:3.11-slim AS backend
WORKDIR /app

COPY --from=frontend-builder /app/client/dist ./client/dist

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server ./server

EXPOSE 4122
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "4122"]
