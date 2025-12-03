import asyncio
import logging
import os

import aiohttp


class HasPrivilegesDataDownloader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://rally-tracks.elastic.co/has-privileges"

    def on_after_load_track(self, track):
        pass

    def on_prepare_track(self, track, data_root_dir):
        """Synchronous method that Rally calls during track preparation"""
        self.logger.info("Preparing has_privileges track data...")

        data_dir = os.path.join(data_root_dir, "has_privileges")
        os.makedirs(data_dir, exist_ok=True)
        params = track.selected_challenge_or_default.parameters
        version = params.get("version")
        self.logger.info(f"Kibana privileges version: {version}")

        if not version:
            self.logger.warning("No kibana_privileges_as_of or version parameter specified, skipping Kibana privileges download")

        # Run async downloads synchronously
        asyncio.run(self._download_files(data_dir, version))

        self.logger.info("Has_privileges track data preparation complete")

        # Return empty list - setup operations are now runners in the schedule
        return []

    async def _download_files(self, data_dir, version):
        """Download all required files"""
        await self._download_has_privileges_template(data_dir)
        if version:
            await self._download_kibana_privileges(data_dir, version)

    async def _download_has_privileges_template(self, data_dir):

        template_path = os.path.join(data_dir, "has-privileges-request-body.json")

        if os.path.exists(template_path):
            self.logger.info("has-privileges-request-body.json already exists, skipping download")
            return

        download_url = f"{self.base_url}/has-privileges-request-body.json"
        self.logger.info(f"Downloading {download_url}...")

        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, ssl=False) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(template_path, "wb") as file:
                        file.write(content)
                    self.logger.info("Downloaded has-privileges-request-body.json")
                else:
                    raise Exception(f"Failed to download has-privileges-request-body.json. HTTP status: {response.status}")

    async def _download_kibana_privileges(self, data_dir, version):
        """Download kibana-app-privileges-{version}.json.bz2"""
        filename = f"kibana-app-privileges-{version}.json.bz2"
        data_path = os.path.join(data_dir, filename)

        if os.path.exists(data_path):
            self.logger.info(f"{filename} already exists, skipping download")
            return

        download_url = f"{self.base_url}/{filename}"
        self.logger.info(f"Downloading {download_url}...")

        async with aiohttp.ClientSession() as session:
            async with session.get(download_url, ssl=False) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(data_path, "wb") as file:
                        file.write(content)
                    self.logger.info(f"Downloaded {filename}")
                else:
                    raise Exception(f"Failed to download {filename}. HTTP status: {response.status}")
