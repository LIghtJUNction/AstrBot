import logging
import asyncio
import sys

logger = logging.getLogger("astrbot")


class PipInstaller:
    def __init__(self, pip_install_arg: str, pypi_index_url: str | None = None):
        self.pip_install_arg = pip_install_arg
        self.pypi_index_url = pypi_index_url

    async def install(
        self,
        package_name: str | None = None,
        requirements_path: str | None = None,
        mirror: str | None = None,
    ):
        args = ["install"]
        if package_name:
            args.append(package_name)
        elif requirements_path:
            args.extend(["-r", requirements_path])

        index_url = mirror or self.pypi_index_url or "https://pypi.org/simple"

        args.extend(["--trusted-host", "mirrors.aliyun.com", "-i", index_url])

        if self.pip_install_arg:
            args.extend(self.pip_install_arg.split())

        logger.info(f"Pip 包管理器: pip {' '.join(args)}")
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m",
                "pip", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            assert process.stdout is not None
            async for line in process.stdout:
                logger.info(line.decode().strip())

            await process.wait()

            if process.returncode != 0:
                raise Exception(f"安装失败，错误码：{process.returncode}")
        except FileNotFoundError:
            # 没有 pip
            from pip import main as pip_main

            result_code = await asyncio.to_thread(pip_main, args)

            # 清除 pip.main 导致的多余的 logging handlers
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            if result_code != 0:
                raise Exception(f"安装失败，错误码：{result_code}")
