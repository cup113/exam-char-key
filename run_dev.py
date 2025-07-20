from dotenv import load_dotenv
from time import sleep
from sys import exit
import subprocess
import os


def start_frontend():
    print("启动前端开发服务器...")
    frontend_path = os.path.join(os.getcwd(), "client")
    return subprocess.Popen(
        ["pnpm", "run", "dev"],
        cwd=frontend_path,
        shell=True,
        stdin=None,
        stdout=None,
        stderr=None,
        close_fds=True,
    )


def start_backend():
    print("启动后端服务器...")
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    return subprocess.Popen(
        ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "4122"],
        shell=True,
    )


def start_db():
    print("启动数据库...")
    db_path = os.path.join(os.getcwd(), "db")
    pocketbase = os.path.join(db_path, "pocketbase.exe")
    if not os.path.exists(pocketbase):
        pocketbase = os.path.join(db_path, "pocketbase")
    if not os.path.exists(pocketbase):
        raise FileNotFoundError("未找到 PocketBase 可执行文件路径。")
    return subprocess.Popen(
        [pocketbase, "serve", "--http=0.0.0.0:4123"],
        cwd=db_path,
    )


def terminate_process(process: subprocess.Popen[bytes]):
    pid_str = f"进程 PID={process.pid}"
    if process.poll() is None:
        print(f"关闭{pid_str}")
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            print(f"{pid_str} 超时未关闭，强制杀死")
            process.kill()
    else:
        print(f"{pid_str} 已关闭")


if __name__ == "__main__":
    print("启动项目...")
    frontend = start_frontend()
    backend = start_backend()
    db = start_db()
    print("前端、后端、数据库服务均已启动。按 Ctrl+C 停止服务。")
    services = [frontend, backend, db]
    try:
        while True:
            for service in services:
                if service.poll() is not None:
                    for service_tt in services:
                        terminate_process(service_tt)
                        exit(0)
            sleep(0.5)
    except KeyboardInterrupt:
        for service_tt in services:
            terminate_process(service_tt)
