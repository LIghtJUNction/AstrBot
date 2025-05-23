import os
from pathlib import Path
import zipfile
import shutil

from ..updator import RepoZipUpdator
from astrbot.core.utils.io import  on_error
from ..star.star import StarMetadata
from astrbot.core import logger
from astrbot.core.utils.astrbot_path import get_astrbot_plugin_path


class PluginUpdator(RepoZipUpdator):
    def __init__(self, repo_mirror: str = "") -> None:
        super().__init__(repo_mirror)
        self.plugin_store_path: Path = get_astrbot_plugin_path()

    def plugin_path(self, repo_name: str) -> Path:
        return self.plugin_store_path / repo_name

    def get_plugin_store_path(self) -> Path:
        return self.plugin_store_path

    async def install(self, repo_url: str, proxy="") -> Path:
        repo_name = self.format_repo_name(repo_url)
        plugin_path = self.plugin_path(repo_name)
        await self.download_from_repo_url(plugin_path, repo_url, proxy)
        self.unzip_file(plugin_path + ".zip", plugin_path)

        return plugin_path

    async def update(self, plugin: StarMetadata, proxy="") -> Path:
        repo_url = plugin.repo

        if not repo_url:
            raise Exception(f"插件 {plugin.name} 没有指定仓库地址。")

        if proxy:
            proxy = proxy.removesuffix("/")
            repo_url = f"{proxy}/{repo_url}"

        plugin_path: Path = self.plugin_path(plugin.repo_name)

        logger.info(f"正在更新插件，路径: {plugin_path}，仓库地址: {repo_url}")
        await self.download_from_repo_url(plugin_path, repo_url, proxy=proxy)

        try:
            plugin_path.rmdir()
        except BaseException as e:
            logger.error(
                f"删除旧版本插件 {plugin_path} 文件夹失败: {str(e)}，使用覆盖安装。"
            )

        self.unzip_file(plugin_path + ".zip", plugin_path)

        return plugin_path

    def unzip_file(self, zip_path: str, target_dir: str):
        os.makedirs(target_dir, exist_ok=True)
        update_dir = ""
        logger.info(f"解压文件: {zip_path}")
        with zipfile.ZipFile(zip_path, "r") as z:
            update_dir = z.namelist()[0]
            z.extractall(target_dir)

        files = os.listdir(os.path.join(target_dir, update_dir))
        for f in files:
            if os.path.isdir(os.path.join(target_dir, update_dir, f)):
                if os.path.exists(os.path.join(target_dir, f)):
                    shutil.rmtree(os.path.join(target_dir, f), onerror=on_error)
            else:
                if os.path.exists(os.path.join(target_dir, f)):
                    os.remove(os.path.join(target_dir, f))
            shutil.move(os.path.join(target_dir, update_dir, f), target_dir)

        try:
            logger.info(
                f"删除临时文件: {zip_path} 和 {os.path.join(target_dir, update_dir)}"
            )
            shutil.rmtree(os.path.join(target_dir, update_dir), onerror=on_error)
            os.remove(zip_path)
        except BaseException:
            logger.warning(
                f"删除更新文件失败，可以手动删除 {zip_path} 和 {os.path.join(target_dir, update_dir)}"
            )
