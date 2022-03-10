import typing
from dataclasses import dataclass
from typing import Union

if typing.TYPE_CHECKING:
    from .device import DeviceId


RawData = int
FWType = int
Version = int
ChunkId = int


@dataclass(frozen=True, eq=True)
class ChunkDescriptor:
    fw_type: FWType
    version: Version
    chunk_id: ChunkId


@dataclass(frozen=True, eq=True)
class Proto:
    from_device: 'DeviceId'
    chunk_size: int  # size of a typical chunk
    chunks: int  # total number of chunks
    fw_size: int  # firmware size in bytes


@dataclass(frozen=True, eq=True)
class AnnounceMessage:
    proto: Proto
    dsc: ChunkDescriptor


@dataclass(frozen=True, eq=True)
class RequestMessage:
    proto: Proto
    dsc: ChunkDescriptor


@dataclass(frozen=True, eq=True)
class DataMessage:
    proto: Proto
    dsc: ChunkDescriptor
    data: RawData


AnyMessage = Union[AnnounceMessage, RequestMessage, DataMessage]
