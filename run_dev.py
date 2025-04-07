from dotenv import load_dotenv
import subprocess
import os

def start_frontend():
    print("启动前端开发服务器...")
    frontend_path = os.path.join(os.getcwd(), "client")
    return subprocess.Popen(["pnpm", "run", "dev"], cwd=frontend_path, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

def start_backend():
    print("启动后端服务器...")
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    return subprocess.Popen(["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "4122"], shell=True)

if __name__ == "__main__":
    print("启动项目...")
    frontend = start_frontend()
    backend = start_backend()
    print("前端和后端服务已启动。按 Ctrl+C 停止服务。")
    try:
        frontend.wait()
        backend.wait()
    except KeyboardInterrupt:
        pass
