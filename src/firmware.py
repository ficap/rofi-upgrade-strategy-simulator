from dataclasses import dataclass
from typing import List, Optional

FW_TYPE_A = 1
FW_TYPE_B = 2


@dataclass
class Firmware:
    fw_type: int
    version: int
    data: List[Optional[int]]

    @property
    def data_size(self):
        return len(self.data)

    def is_complete(self):
        return not any([d is None for d in self.data])

    def is_chunk_present(self, chunk_id: int):
        if not self.is_valid_chunk_id(chunk_id):
            return False

        return self.data[chunk_id] is not None

    def is_valid_chunk_id(self, chunk_id: int):
        return 0 <= chunk_id < self.data_size

    def get_missing_chunks(self):
        return list(
            map(
                lambda x: x[0],
                filter(
                    lambda x: x[1],
                    enumerate([
                        d is None for d in self.data
                    ])
                )
            )
        )
