# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rossen Georgiev <rossen@rgp.io>

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

This is an updated copy of
https://github.com/ValvePython/steam/blob/master/steam/core/msg/headers.py
"""

import struct

from . import steammessages_base, foobar
from .emsg import EMsg
from ..utils import set_proto_bit, clear_proto_bit

__all__ = (
    'MsgHdr',
    'GCMsgHdr',
    'GCMsgHdrProto',
    'ExtendedMsgHdr',
    'MsgHdrProtoBuf',
)


class MsgHdr:
    __slots__ = ('msg', 'target_job_id', 'source_job_id')
    SIZE = 20

    def __init__(self, data: bytes = None):
        self.msg = EMsg.Invalid
        self.target_job_id = -1
        self.source_job_id = -1
        if data:
            self.load(data)

    def __repr__(self):
        resolved = [f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__]
        return f'<MsgHdr {" ".join(resolved)}>'

    def serialize(self):
        return struct.pack("<Iqq", self.msg, self.target_job_id, self.source_job_id)

    def load(self, data):
        (msg, self.target_job_id, self.source_job_id) = struct.unpack_from("<Iqq", data)
        self.msg = EMsg(msg)


class ExtendedMsgHdr:
    __slots__ = ('msg', 'steam_id', 'session_id',
                 'header_size', 'header_size', 'header_version', 'header_canary',
                 'target_job_id', 'source_job_id')
    SIZE = 36

    def __init__(self, data: bytes = None):
        self.msg = EMsg.Invalid
        self.header_size = 36
        self.header_version = 2
        self.target_job_id = -1
        self.source_job_id = -1
        self.header_canary = 239
        self.steam_id = -1
        self.session_id = -1
        if data:
            self.load(data)

    def __repr__(self):
        attrs = (
            'msg', 'steam_id', 'session_id'
        )
        resolved = [f'{attr}={getattr(self, attr)!r}' for attr in attrs]
        return f'<ExtendedMsgHdr {" ".join(resolved)}>'

    def serialize(self):
        return struct.pack("<IBHqqBqi", self.msg, self.header_size, self.header_version, self.target_job_id,
                           self.source_job_id, self.header_canary, self.steam_id, self.session_id)

    def load(self, data: bytes):
        (msg, self.header_size, self.header_version, self.target_job_id, self.source_job_id,
         self.header_canary, self.steam_id, self.session_id) = struct.unpack_from("<IBHqqBqi", data)

        self.msg = EMsg(msg)

        if self.header_size != 36 or self.header_version != 2:
            raise RuntimeError("Failed to parse header")


class MsgHdrProtoBuf:
    SIZE = 8
    __slots__ = ('proto', 'msg', '_full_size')

    def __init__(self, data: bytes = None):
        self.msg = EMsg.Invalid
        self.proto = steammessages_base.CMsgProtoBufHeader()
        self._full_size = self.SIZE

        if data:
            self.load(data)

    def __repr__(self):
        attrs = (
            'msg',
        )
        resolved = [f'{attr}={getattr(self, attr)!r}' for attr in attrs]
        resolved.extend([f'{k}={v!r}' for k, v in self.proto.to_dict().items()])
        return f'<MsgHdrProtoBuf {" ".join(resolved)}>'

    def serialize(self) -> bytes:
        proto_data = self.proto.SerializeToString()
        return struct.pack("<II", set_proto_bit(self.msg.value), len(proto_data)) + proto_data

    def load(self, data: bytes) -> None:
        msg, proto_length = struct.unpack_from("<II", data)

        self.msg = EMsg(clear_proto_bit(msg))
        self._full_size = self.SIZE + proto_length
        self.proto.FromString(data[self.SIZE:self._full_size])


class GCMsgHdr:
    __slots__ = ('msg', 'proto', 'header_version', 'target_job_id', 'source_job_id')
    SIZE = 18

    def __init__(self, msg, data=None):
        self.msg = clear_proto_bit(msg)
        self.proto = None
        self.header_version = 1
        self.target_job_id = -1
        self.source_job_id = -1

        if data:
            self.load(data)

    def __repr__(self):
        attrs = (
            'msg', 'target_job_id', 'source_job_id'
        )
        resolved = [f'{attr}={getattr(self, attr)!r}' for attr in attrs]
        resolved.extend([f'{k}={v!r}' for k, v in self.proto.to_dict().items()])
        return f'<GCMsgHdr {" ".join(resolved)}>'

    def serialize(self):
        return struct.pack("<Hqq", self.header_version, self.target_job_id, self.source_job_id)

    def load(self, data):
        (self.header_version, self.target_job_id, self.source_job_id) = struct.unpack_from("<Hqq", data)


class GCMsgHdrProto:
    __slots__ = ('msg', 'proto', 'header_length')
    SIZE = 8

    def __init__(self, msg, data=None):
        self.msg = EMsg.try_value(clear_proto_bit(msg))
        self.proto = foobar.CMsgProtoBufHeader()
        self.header_length = 0

        if data:
            self.load(data)

    def __repr__(self):
        attrs = (
            'msg',
        )
        resolved = [f'{attr}={getattr(self, attr)!r}' for attr in attrs]
        resolved.extend([f'{k}={v!r}' for k, v in self.proto.to_dict().items()])
        return f'<GCMsgHdrProto {" ".join(resolved)}>'

    def serialize(self):
        proto_data = self.proto.SerializeToString()
        self.header_length = len(proto_data)

        return struct.pack("<Ii", set_proto_bit(self.msg), self.header_length) + proto_data

    def load(self, data):
        (msg, self.header_length) = struct.unpack_from("<Ii", data)

        self.msg = EMsg(clear_proto_bit(msg))

        if self.header_length:
            x = GCMsgHdrProto.SIZE
            self.proto.FromString(data[x:x + self.header_length])
