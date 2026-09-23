"""Lê arquivos de um .zip remoto usando HTTP Range, sem baixar o zip inteiro.

Uso: uv run python tools/remote_zip.py <url> list [filtro]
     uv run python tools/remote_zip.py <url> get <regex> <destino>
"""
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path


class HttpRangeFile(io.RawIOBase):
    def __init__(self, url):
        # resolve o redirecionamento (Dataverse -> S3 pré-assinado) uma vez
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req) as r:
            self.url = r.geturl()
            self.size = int(r.headers["Content-Range"].split("/")[1])
        self.pos = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req) as r:
            data = r.read()
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)


def main():
    url, cmd = sys.argv[1], sys.argv[2]
    zf = zipfile.ZipFile(io.BufferedReader(HttpRangeFile(url), buffer_size=1 << 20))
    if cmd == "list":
        pat = re.compile(sys.argv[3]) if len(sys.argv) > 3 else None
        for i in zf.infolist():
            if pat is None or pat.search(i.filename):
                print(f"{i.file_size:>12} {i.filename}")
    elif cmd == "get":
        pat, dest = re.compile(sys.argv[3]), Path(sys.argv[4])
        for i in zf.infolist():
            if pat.search(i.filename) and not i.is_dir():
                out = dest / i.filename
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(zf.read(i))
                print("ok", out, i.file_size)


if __name__ == "__main__":
    main()
