import logging
import os

from esrally.utils import net

BASE_URL = "https://rally-tracks.elastic.co/has-privileges"


def download(url, target_path):
    """
    Downloads a single file. This is executed by Rally's task executor actors, so it must be a module-level function
    that can be pickled.
    """
    logger = logging.getLogger(__name__)
    if os.path.exists(target_path):
        logger.info("[%s] already exists, skipping download", target_path)
        return
    logger.info("Downloading [%s] to [%s]", url, target_path)
    net.download(url, target_path)
    logger.info("Downloaded [%s]", target_path)


class HasPrivilegesDataDownloader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def on_after_load_track(self, track):
        pass

    def on_prepare_track(self, track, data_root_dir):
        data_dir = os.path.join(data_root_dir, "has_privileges")
        os.makedirs(data_dir, exist_ok=True)
        version = track.selected_challenge_or_default.parameters.get("version")
        self.logger.info("Kibana privileges version: %s", version)

        filenames = ["has-privileges-request-body.json"]
        if version:
            filenames.append(f"kibana-app-privileges-{version}.json.bz2")
        else:
            self.logger.warning("No version parameter specified, skipping Kibana privileges download")

        # Rally executes the yielded functions in its task executor actors instead of the main actor thread
        for filename in filenames:
            yield download, {"url": f"{BASE_URL}/{filename}", "target_path": os.path.join(data_dir, filename)}
