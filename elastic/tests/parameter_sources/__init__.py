import json
import os

from esrally.track import (
    DocumentCorpus,
    Documents,
    track,
    IndexTemplate,
    Index,
    Challenge,
    ComponentTemplate,
)
from shared.track_processors.data_generator import LazyMetadataDocuments

cwd = os.path.dirname(__file__)


class EmptyTrack:
    def __init__(
        self,
        name="test_track",
        parameters=None,
        challenge_parameters=None,
    ):
        self.name = name
        if challenge_parameters is None:
            challenge_parameters = {}
        if parameters is None:
            parameters = {}
        self.selected_challenge = Challenge(
            "test-challenge", parameters={**parameters, **challenge_parameters}
        )
        self.selected_challenge_or_default = self.selected_challenge
        self.data_streams = []
        self.component_templates = []
        self.composable_templates = []
        # test file references are relative from root elastic/ folder
        self.root = os.path.join(cwd, "..", "..")


class StaticTrack:
    def __init__(
        self,
        name="test_track",
        parameters=None,
        challenge_parameters=None,
        generated_document_paths=None,
    ):
        super(StaticTrack, self).__init__(name, parameters, challenge_parameters)

        system_corpora = DocumentCorpus(name="system-logs")
        system_corpora.documents.append(
            Documents(
                target_data_stream="logs-system.test",
                source_format=track.Documents.SOURCE_FORMAT_BULK,
                document_file=os.path.join(
                    cwd, "resources", "documents", "test-system.json"
                ),
                number_of_documents=2,
            )
        )
        agent_corpora = DocumentCorpus(name="agent-logs")
        agent_corpora.documents.append(
            Documents(
                target_data_stream="logs-system.test",
                source_format=track.Documents.SOURCE_FORMAT_BULK,
                document_file=os.path.join(
                    cwd, "resources", "documents", "test-agent.json"
                ),
                number_of_documents=2,
            )
        )
        kakfa_corpora = DocumentCorpus(name="kafka-logs")
        kakfa_corpora.documents.append(
            Documents(
                target_data_stream="logs-kafka.test",
                source_format=track.Documents.SOURCE_FORMAT_BULK,
                document_file=os.path.join(
                    cwd, "resources", "documents", "test-kafka.json"
                ),
                number_of_documents=1,
            )
        )

        with open(
            os.path.join(
                cwd, "resources", "templates", "logs-endpoint.events.process.json"
            ),
            "r",
        ) as composable_file:
            self.composable_templates.append(
                IndexTemplate(
                    "logs-endpoint.events.process",
                    "logs-endpoint.events.process-*",
                    json.load(composable_file),
                )
            )
        with open(
            os.path.join(
                cwd,
                "resources",
                "templates",
                "logs-endpoint.events.process-mappings.json",
            ),
            "r",
        ) as component_file:
            self.component_templates.append(
                ComponentTemplate(
                    "logs-endpoint.events.process-mappings", json.load(component_file)
                )
            )

        self.corpora = [system_corpora, agent_corpora, kakfa_corpora]
        if generated_document_paths:
            docs = []
            for p in generated_document_paths:
                docs.append(LazyMetadataDocuments(document_file=p))

            generated_corpus = DocumentCorpus(
                name="generated", documents=docs, meta_data={"generated": True}
            )
            self.corpora.append(generated_corpus)

        self.data_streams = [
            Index("logs-system.syslog-default"),
            Index("logs-elastic.agent-default"),
            Index("logs-elastic.kafka-default"),
        ]


class InvalidTrack:
    def __init__(self):
        system_corpora = DocumentCorpus(name="missing_uncompressed_size_in_bytes")
        cwd = os.path.dirname(__file__)
        system_corpora.documents.append(
            Documents(
                target_index="logs-system.test",
                source_format=track.Documents.SOURCE_FORMAT_BULK,
                document_file=os.path.join(cwd, "resources", "test-system.json"),
                number_of_documents=2,
            )
        )
        self.corpora = [system_corpora]
