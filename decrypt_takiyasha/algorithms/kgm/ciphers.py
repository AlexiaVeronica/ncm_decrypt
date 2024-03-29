import lzma
import os
from typing import Generator

from ..common import StreamCipher
from ...utils import xor_bytestrings

_MASK_DIFF_VPR: bytes = bytes(
    [
        0x25, 0xdf, 0xe8, 0xa6, 0x75, 0x1e, 0x75, 0x0e,
        0x2f, 0x80, 0xf3, 0x2d, 0xb8, 0xb6, 0xe3, 0x11,
        0x00
    ]
)
_MASK_V2_PRE_DEF: bytes = bytes(
    [
        0xb8, 0xd5, 0x3d, 0xb2, 0xe9, 0xaf, 0x78, 0x8c, 0x83, 0x33, 0x71, 0x51, 0x76, 0xa0, 0xcd, 0x37,
        0x2f, 0x3e, 0x35, 0x8d, 0xa9, 0xbe, 0x98, 0xb7, 0xe7, 0x8c, 0x22, 0xce, 0x5a, 0x61, 0xdf, 0x68,
        0x69, 0x89, 0xfe, 0xa5, 0xb6, 0xde, 0xa9, 0x77, 0xfc, 0xc8, 0xbd, 0xbd, 0xe5, 0x6d, 0x3e, 0x5a,
        0x36, 0xef, 0x69, 0x4e, 0xbe, 0xe1, 0xe9, 0x66, 0x1c, 0xf3, 0xd9, 0x02, 0xb6, 0xf2, 0x12, 0x9b,
        0x44, 0xd0, 0x6f, 0xb9, 0x35, 0x89, 0xb6, 0x46, 0x6d, 0x73, 0x82, 0x06, 0x69, 0xc1, 0xed, 0xd7,
        0x85, 0xc2, 0x30, 0xdf, 0xa2, 0x62, 0xbe, 0x79, 0x2d, 0x62, 0x62, 0x3d, 0x0d, 0x7e, 0xbe, 0x48,
        0x89, 0x23, 0x02, 0xa0, 0xe4, 0xd5, 0x75, 0x51, 0x32, 0x02, 0x53, 0xfd, 0x16, 0x3a, 0x21, 0x3b,
        0x16, 0x0f, 0xc3, 0xb2, 0xbb, 0xb3, 0xe2, 0xba, 0x3a, 0x3d, 0x13, 0xec, 0xf6, 0x01, 0x45, 0x84,
        0xa5, 0x70, 0x0f, 0x93, 0x49, 0x0c, 0x64, 0xcd, 0x31, 0xd5, 0xcc, 0x4c, 0x07, 0x01, 0x9e, 0x00,
        0x1a, 0x23, 0x90, 0xbf, 0x88, 0x1e, 0x3b, 0xab, 0xa6, 0x3e, 0xc4, 0x73, 0x47, 0x10, 0x7e, 0x3b,
        0x5e, 0xbc, 0xe3, 0x00, 0x84, 0xff, 0x09, 0xd4, 0xe0, 0x89, 0x0f, 0x5b, 0x58, 0x70, 0x4f, 0xfb,
        0x65, 0xd8, 0x5c, 0x53, 0x1b, 0xd3, 0xc8, 0xc6, 0xbf, 0xef, 0x98, 0xb0, 0x50, 0x4f, 0x0f, 0xea,
        0xe5, 0x83, 0x58, 0x8c, 0x28, 0x2c, 0x84, 0x67, 0xcd, 0xd0, 0x9e, 0x47, 0xdb, 0x27, 0x50, 0xca,
        0xf4, 0x63, 0x63, 0xe8, 0x97, 0x7f, 0x1b, 0x4b, 0x0c, 0xc2, 0xc1, 0x21, 0x4c, 0xcc, 0x58, 0xf5,
        0x94, 0x52, 0xa3, 0xf3, 0xd3, 0xe0, 0x68, 0xf4, 0x00, 0x23, 0xf3, 0x5e, 0x0a, 0x7b, 0x93, 0xdd,
        0xab, 0x12, 0xb2, 0x13, 0xe8, 0x84, 0xd7, 0xa7, 0x9f, 0x0f, 0x32, 0x4c, 0x55, 0x1d, 0x04, 0x36,
        0x52, 0xdc, 0x03, 0xf3, 0xf9, 0x4e, 0x42, 0xe9, 0x3d, 0x61, 0xef, 0x7c, 0xb6, 0xb3, 0x93, 0x50,
    ]
)

_MASK_V2: bytes = b''


class KGM_MaskCipher(StreamCipher):
    def __init__(self, key: bytes, is_vpr_format: bool = False):
        if not isinstance(key, bytes):
            raise TypeError(f"'key' must be bytes or bytearray, not {type(key).__name__}")
        super().__init__(key)
        self._is_vpr_format: bool = bool(is_vpr_format)

        # 加载 mask_v2（已加载则跳过）
        global _MASK_V2
        if not _MASK_V2:
            with open(os.path.join(os.path.dirname(__file__), 'binaries/kgm.v2.mask'), 'rb') as lzf:
                _MASK_V2 = lzma.decompress(lzf.read())
        self._mask_v2: bytes = _MASK_V2
        self._full_mask_len: int = len(_MASK_V2) * 16

    @property
    def is_vpr_format(self):
        return self._is_vpr_format

    @property
    def mask_v2(self):
        return self._mask_v2

    @property
    def full_mask_length(self) -> int:
        return self._full_mask_len

    def _yield_vpr_stream(self, src_len: int, offset: int) -> Generator[int, None, None]:
        mask_diff_vpr: bytes = _MASK_DIFF_VPR

        for i in range(offset, offset + src_len):
            yield mask_diff_vpr[(i % 17)]

    def _yield_med8(self, src: bytes, offset: int) -> Generator[int, None, None]:
        src_len: int = len(src)
        key: bytes = self.key
        mask_v2: bytes = self.mask_v2
        mask_v2_pre_def: bytes = _MASK_V2_PRE_DEF

        for idx, i in enumerate(range(offset, offset + src_len)):
            yield src[idx] ^ key[i % 17] ^ mask_v2_pre_def[i % (16 * 17)] ^ mask_v2[i >> 4]

    def decrypt(self, src: bytes, offset: int = 0) -> bytes:
        med8_stream1: bytes = bytes(self._yield_med8(src, offset))
        med8_stream2: bytes = bytes((med8 & 0xf) << 4 for med8 in med8_stream1)

        ret: bytes = xor_bytestrings(med8_stream1, med8_stream2)

        if self._is_vpr_format:
            return xor_bytestrings(ret, bytes(self._yield_vpr_stream(len(src), offset)))
        else:
            return ret
