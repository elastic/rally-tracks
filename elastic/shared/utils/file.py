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
import json
import logging
import os
import time

from esrally import exceptions
from esrally.track.params import Slice


class FileReader:
    def __init__(self, data_file, file_source, processor, corpus_name):
        self.logger = logging.getLogger(__name__)
        self.data_file = data_file
        self.file_source = file_source
        self.processor = processor
        self.corpus_name = corpus_name

    def __iter__(self):
        return self

    def open(self, bulk_size):
        self.file_source.open(self.data_file, "rt", bulk_size)

    def close(self):
        self.file_source.close()

    def reset(self):
        self.logger.debug("Resetting reader.... [%s]", self.file_source)
        self.file_source.set_position()

    def set_bulk_size(self, bulk_size):
        self.file_source.set_bulk_size(bulk_size)


class JsonFileReader(FileReader):
    def __init__(
        self, data_file, file_source, processor, target_data_stream, corpus_name
    ):
        super().__init__(data_file, file_source, processor, corpus_name)
        self.target_data_stream = target_data_stream

    def __next__(self):
        try:
            b_docs = next(self.file_source)
            docs = []
            total_size = 0
            for i, doc_bytes in enumerate(b_docs):
                # add metadata
                docs.append({"create": {"_index": self.target_data_stream}})
                # size reported here is upto the processor passed
                doc, size = self.processor(doc_bytes, i, self.corpus_name)
                docs.append(doc)
                total_size += size
            return docs, total_size
        except IOError:
            self.logger.exception("Could not read [%s]", self.data_file)
            raise
        except StopIteration:
            return None, 0


class BulkFileReader(FileReader):
    def __init__(self, data_file, file_source, processor, corpus_name):
        super().__init__(data_file, file_source, processor, corpus_name)

    def open(self, bulk_size):
        # bulks size must be even or we wont get meta
        self.file_source.open(
            self.data_file, "rt", bulk_size + 1 if bulk_size % 2 == 1 else bulk_size
        )

    def __next__(self):
        try:
            b_docs = next(self.file_source)
            docs = []
            total_size = 0
            for i, doc_bytes in enumerate(b_docs):
                doc, size = self.processor(doc_bytes, i, self.corpus_name)
                docs.append(doc)
                total_size += size
            return docs, total_size
        except IOError:
            self.logger.exception("Could not read [%s]", self.data_file)
            raise
        except StopIteration:
            return None, 0

    def set_bulk_size(self, bulk_size):
        # bulks size must be even or we wont get meta
        super().set_bulk_size(bulk_size + 1 if bulk_size % 2 == 1 else bulk_size)


class CorpusReader:
    def __init__(self, readers, bulk_size):
        self.bulk_size = bulk_size
        self.readers = readers
        self._num_readers = len(readers)
        self._current_reader = 0

    def __get_next_doc_bulk__(self):
        i = 0
        while True:
            reader = self.readers[self._current_reader]
            # ensure the latest value is applied
            reader.set_bulk_size(self.bulk_size)
            lines, size = next(reader)
            if lines:
                return int(len(lines) / 2), lines, size
            else:
                reader.reset()
                i += 1
                self._current_reader = (self._current_reader + 1) % self._num_readers
                if i > 1:
                    raise exceptions.DataError(
                        f"Excessive file reset detected for file [{reader.data_file}] - reset "
                        f"more than once. Should only need a single reset. Possible empty data "
                        f"file."
                    )

    def __next__(self):
        return self.__get_next_doc_bulk__()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
        return False

    def open(self):
        for reader in self.readers:
            reader.open(self.bulk_size)

    def close(self):
        for reader in self.readers:
            reader.close()

    def reset(self):
        for reader in self.readers:
            reader.reset()

    def set_bulk_size(self, bulk_size):
        self.bulk_size = bulk_size
        # this might be called quite frequently during throttling.
        # We don't loop over the readers to save time and lazily apply


class CorporaReader:
    def __init__(self, corpus_readers):
        self.corpus_readers = corpus_readers

    def __enter__(self):
        for corpus_reader in self.corpus_readers:
            corpus_reader.open()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for corpus_reader in self.corpus_readers:
            corpus_reader.close()
        return False


class WrappingSlice(Slice):
    def __init__(self, source_class, offset, number_of_lines):
        super().__init__(source_class, offset, number_of_lines)
        self.logger = logging.getLogger(__name__)
        self._start_bytes = 0
        self._remaining_lines = 0

    def open(self, file_name, mode, bulk_size):
        self.bulk_size = bulk_size
        self.source = self.source_class(file_name, mode).open()
        self.logger.info(
            "Will read [%d] lines from [%s] starting from line [%d] with bulk size [%d].",
            self.number_of_lines,
            file_name,
            self.offset,
            self.bulk_size,
        )
        start = time.perf_counter()
        self._open_skip(file_name)
        end = time.perf_counter()
        self.logger.debug(
            "Opening file and skipping [%d] lines took [%f] s.",
            self.offset,
            end - start,
        )
        return self

    # see io.skip_lines in rally - difference is we persist the seek so we can return
    def _open_skip(self, data_file_path):
        if self.offset == 0:
            return
        offset_file_path = f"{data_file_path}.offset"
        bytes_offset = 0
        self._remaining_lines = self.offset
        # can we fast forward?
        if os.path.exists(offset_file_path):
            with open(offset_file_path, mode="rt", encoding="utf-8") as offsets:
                for line in offsets:
                    line_number, offset_in_bytes = [
                        int(i) for i in line.strip().split(";")
                    ]
                    if line_number <= self.offset:
                        bytes_offset = offset_in_bytes
                        self._remaining_lines = self.offset - line_number
                    else:
                        break
        # fast forward to the last known file offset
        self._start_bytes = bytes_offset
        self.set_position()

    def set_bulk_size(self, bulk_size):
        self.bulk_size = bulk_size

    def set_position(self):
        self.source.seek(self._start_bytes)
        self.current_line = 0
        if self._remaining_lines > 0:
            for line in range(self._remaining_lines):
                self.source.readline()


class FileMetadata:
    @classmethod
    def write(cls, output_folder, client_index, number_docs, message_size):
        if number_docs is None:
            raise exceptions.DataError("number_docs must not be None")
        if message_size is None:
            raise exceptions.DataError("message_size must not be None")

        with open(
            FileMetadata._meta_data_file_name(output_folder, client_index), "w"
        ) as f:
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
