from dataclasses import dataclass
from io import BytesIO

# Mode bitfield
from enum import IntFlag
class _FileMode(IntFlag):
    S_IFMT   = 0o0170000
    S_IFIFO  = 0o0010000
    S_IFCHR  = 0o0020000
    S_IFDIR  = 0o0040000
    S_IFBLK  = 0o0060000
    S_IFREG  = 0o0100000
    S_IFLNK  = 0o0120000
    S_IFSOCK = 0o0140000

    #S_IRWXU  = 0o0000700
    S_IRUSR  = 0o0000400
    S_IWUSR  = 0o0000200
    S_IXUSR  = 0o0000100

    #S_IRWXG  = 0o0000070
    S_IRGRP  = 0o0000040
    S_IWGRP  = 0o0000020
    S_IXGRP  = 0o0000010

    #S_IRWXO  = 0o0000007
    S_IROTH  = 0o0000004
    S_IWOTH  = 0o0000002
    S_IXOTH  = 0o0000001

    S_ISUID  = 0o0004000
    S_ISGID  = 0o0002000
    S_ISVTX  = 0o0001000

@dataclass
class MbdbRecord:
    domain: str
    filename: str
    link: str
    hash: bytes
    key: bytes
    mode: _FileMode
    inode: int
    user_id: int
    group_id: int
    mtime: int
    atime: int
    ctime: int
    size: int
    flags: int
    properties: list

    def to_bytes(self) -> bytes:
        d = BytesIO()

        d.write(len(self.domain).to_bytes(2, "big"))
        d.write(self.domain.encode("utf-8"))

        d.write(len(self.filename).to_bytes(2, "big"))
        d.write(self.filename.encode("utf-8"))

        d.write(len(self.link).to_bytes(2, "big"))
        d.write(self.link.encode("utf-8"))

        d.write(len(self.hash).to_bytes(2, "big"))
        d.write(self.hash)

        d.write(len(self.key).to_bytes(2, "big"))
        d.write(self.key)

        d.write(self.mode.to_bytes(2, "big"))
        #d.write(self.unknown2.to_bytes(4, "big"))
        #d.write(self.unknown3.to_bytes(4, "big"))
        d.write(self.inode.to_bytes(8, "big"))
        d.write(self.user_id.to_bytes(4, "big"))
        d.write(self.group_id.to_bytes(4, "big"))
        d.write(self.mtime.to_bytes(4, "big"))
        d.write(self.atime.to_bytes(4, "big"))
        d.write(self.ctime.to_bytes(4, "big"))
        d.write(self.size.to_bytes(8, "big"))
        d.write(self.flags.to_bytes(1, "big"))

        d.write(len(self.properties).to_bytes(1, "big"))

        for name, value in self.properties:
            d.write(len(name).to_bytes(2, "big"))
            d.write(name.encode("utf-8"))

            d.write(len(value).to_bytes(2, "big"))
            d.write(value.encode("utf-8"))

        return d.getvalue()
    
@dataclass
class Mbdb:
    records: list[MbdbRecord]

    def to_bytes(self) -> bytes:
        d = BytesIO()

        d.write(b"mbdb")
        d.write(b"\x05\x00")

        for record in self.records:
            d.write(record.to_bytes())

        return d.getvalue()