# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import glob
import json
import logging
import os
import random
from datetime import datetime, timezone

from esrally import exceptions
from esrally.track import DocumentCorpus, Documents
from esrally.track.loader import DocumentSetPreparator
from esrally.utils import io


class FileMetadata:
    @classmethod
    def write(cls, output_folder, client_index, number_docs, message_size):
        if number_docs is None:
            raise exceptions.DataError("number_docs must not be None")
        if message_size is None:
            raise exceptions.DataError("message_size must not be None")

        with open(FileMetadata._meta_data_file_name(output_folder, client_index), "w") as f:
            metadata = {
                "number-of-documents": number_docs,
                "message-size": message_size,
            }
            json.dump(metadata, f, indent=2)

    @classmethod
    def read(cls, filename):
        with open(f"{filename}.metadata", "r") as f:
            metadata = json.load(f)
            return metadata["number-of-documents"], metadata["message-size"]

    @classmethod
    def _meta_data_file_name(cls, output_folder, client_index):
        return os.path.join(output_folder, f"{client_index}.metadata")


class LazyMetadataDocuments(Documents):
    def __init__(self, document_file):
        super().__init__(source_format=Documents.SOURCE_FORMAT_BULK,
                         document_file=document_file,
                         includes_action_and_meta_data=True)

    @property
    def uncompressed_size_in_bytes(self):
        try:
            return os.path.getsize(self.document_file)
        # called before data have been generated (e.g. when listing tracks)
        except FileNotFoundError:
            return 0

    @property
    def _metadata(self):
        return FileMetadata.read(self.document_file[:-len(".json")])

    @property
    def number_of_documents(self):
        try:
            return self._metadata[0]
        # called before data have been generated (e.g. when listing tracks)
        except FileNotFoundError:
            return 0

    @number_of_documents.setter
    def number_of_documents(self, value):
        # ignore any attempts to change the number of documents (e.g. via test mode)
        pass

    @property
    def message_size(self):
        try:
            return self._metadata[1]
        except FileNotFoundError:
            return 0


class DataGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def on_after_load_track(self, track):
        self.logger.info("##cavok## on_after_load_track")
        # inject a generated corpus
        track_id = track.selected_challenge_or_default.parameters["track-id"]
        client_count = track.selected_challenge_or_default.parameters.get("data-generation-clients", 2)
        documents = []
        for client_id in range(client_count):
            # only use a relative path; the absolute path will be set by Rally on the target machine
            documents.append(
                LazyMetadataDocuments(document_file=os.path.join("generated", track_id, f"{client_id}.json")))

        # keep this corpus, as well as other corpora below the track directory by name it like the track
        generated_corpus = DocumentCorpus(name=track.name, documents=documents, meta_data={
            "generated": True
        })
        track.corpora.append(generated_corpus)

    def on_prepare_track(self, track, data_root_dir):
        self.logger.info("##cavok## on_prepare_track")
        track_data_root = os.path.join(data_root_dir, track.name)
        for corpus in track.corpora:
            if not corpus.meta_data.get("generated", False):
                data_root = os.path.join(track_data_root, corpus.name)
                self.logger.info("Resolved data root directory for document corpus [%s] in track [%s] to [%s].",
                                 corpus.name, track.name, data_root)

        # data is now available locally, proceed with generating data
        client_count = track.selected_challenge_or_default.parameters.get("data-generation-clients", 2)
        track_id = track.selected_challenge_or_default.parameters["track-id"]
        output_folder = os.path.join(track_data_root, "generated", track_id)
        track.selected_challenge_or_default.parameters["output-folder"] = output_folder
        retval = []
        for client_id in range(client_count):
            generator_params = {
                "track": track,
                "track_data_root": track_data_root,
                "client_index": client_id,
                "client_count": client_count
            }
            retval.append((generate, generator_params))
        return retval


class CorpusGenerator:
    def __init__(self, track, track_data_root, client_index="*", client_count=None):
        self.logger = logging.getLogger(__name__)
        self.output_folder = track.selected_challenge_or_default.parameters["output-folder"]
        self.output_file = os.path.join(self.output_folder, f"{client_index}.json")
        self.client_index = client_index
        self.client_count = client_count
        self.complete = False

        # check if output folder exists and contains files. If it does, we complete early unless force=True
        if not track.selected_challenge_or_default.parameters.get("force-data-generation"):
            file_pattern = f"{client_index}.json"
            if len(glob.glob(os.path.join(self.output_folder, file_pattern))) > 0:
                self.complete = True
                self.logger.info(
                    "Skipping data generation as files are present and force-data-generation is set to false.")

    def init_internal_params(self):
        pass

    def doc_generator(self):
        current_docs = 0
        total_size_in_bytes = 0

        os.makedirs(self.output_folder, exist_ok=True)
        with open(self.output_file, "wt") as data_file:
            for n in range(1000):
                data = {
                    "destination": {
                        "ip": "127.0.0.1",
                        "port": 22,
                    },
                    "source": {
                        "ip": "127.0.0.1",
                        "port": n + 22,
                    },
                    "timestampo": "12234",
                }
                s = json.dumps(data, sort_keys=True) + "\n"
                total_size_in_bytes += len(s)
                current_docs += 1;
                data_file.write(s)

        self.logger.info("Generator [%d] has completed generating [%d] docs with [%d] bytes.",
                         self.client_index, current_docs, total_size_in_bytes)
        FileMetadata.write(self.output_folder, self.client_index, current_docs, total_size_in_bytes)

def generate(track, track_data_root, client_index=None, client_count=None):
    generator = CorpusGenerator(track=track, track_data_root=track_data_root, client_index=client_index,
                                client_count=client_count)
    # This is determined at startup based on the presence of files
    if generator.complete:
        return True
    generator.init_internal_params()
    generator.doc_generator()
    return False
