import asyncio
import logging
import os

import aiohttp

QUERIES_FILENAME = "queries_emis.json.zst"

class ArxivQueriesDownloader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def on_after_load_track(self, track):
        pass

    def on_prepare_track(self, track, data_root_dir):
        params = track.selected_challenge_or_default.parameters

        base_url = params.get("base_url", "https://rally-tracks.elastic.co/arxiv_for_fanns")
        queries_file = params.get("queries_file", QUERIES_FILENAME)

        track_dir = os.path.dirname(__file__)
        dest = os.path.join(track_dir, queries_file)

        if os.path.exists(dest):
            self.logger.info("Queries file '%s' already exists, skipping download", dest)
            return []

        download_url = f"{base_url}/{queries_file}"
        self.logger.info("Downloading queries from '%s' to '%s'", download_url, dest)
        asyncio.run(self._download(download_url, dest))
        return []

    async def _download(self, url, dest):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"Failed to download queries file from '{url}': HTTP {response.status}"
                    )
                with open(dest, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        f.write(chunk)
        self.logger.info("Downloaded queries file to '%s'", dest)
