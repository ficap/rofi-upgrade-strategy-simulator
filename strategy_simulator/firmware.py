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

    def get_first_missing_chunk(self):
        return self.get_missing_chunks()[0]

    def get_next_chunk_present(self, chunk_id: int):
        for i in range(chunk_id + 1, self.data_size):  # pozor tady musi byt +1 jinak se nehybeme dal
            if self.data[i] is not None:
                return i

        return None
