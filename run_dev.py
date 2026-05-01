import sys as _sys
from sys import argv, stdout, stderr
from os import environ
from pathlib import Path
from subprocess import Popen, CREATE_NEW_PROCESS_GROUP
from typing import Union, Optional
from shutil import which

ROOT = Path(argv[0]).absolute().parent


def get_which(name: str) -> Path:
    result = which(name)
    assert result is not None, f"{name} not found"
    return Path(result)


pnpm = get_which("pnpm")


def general_popen(
    *cmd: Union[str, Path],
    cwd: Path = ROOT,
    env_add: Optional[dict[str, str]] = None,
    creationflags: int = 0,
):
    if env_add is None:
        env_add = {}
    new_env = environ.copy()
    new_env.update(env_add)
    return Popen(
        [str(c) for c in cmd],
        cwd=str(cwd),
        stdout=stdout,
        stderr=stderr,
        env=new_env,
        creationflags=creationflags,
    )


def all_wait(*wait_list: Popen[bytes]):
    for p in wait_list:
        code = p.wait()
        if code != 0:
            raise ChildProcessError(f"Process {p.args} exited with code {code}")


if __name__ == "__main__":
    process_pnpm = general_popen(pnpm, "run", "dev", cwd=ROOT / "client")
    process_uvicorn = general_popen(
        "uvicorn",
        "main:app",
        "--reload",
        "--port",
        "8000",
        cwd=ROOT / "server",
        creationflags=CREATE_NEW_PROCESS_GROUP if _sys.platform == "win32" else 0,
    )

    processes = [process_pnpm, process_uvicorn]
    try:
        all_wait(*processes)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            process.terminate()
