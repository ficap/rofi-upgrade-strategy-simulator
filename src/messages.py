from dataclasses import dataclass


@dataclass
class AnnounceMsg:
    from_node: int
    fw_type: int
    version: int
    chunk_id: int
    num_of_chunks: int


@dataclass
class RequestMsg:
    from_node: int
    fw_type: int
    version: int
    chunk_id: int


@dataclass
class DataMsg:
    from_node: int
    fw_type: int
    version: int
    chunk_id: int
    num_of_chunks: int
    chunk_length: int
    data: int
