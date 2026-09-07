import hashlib
import zlib
from PySide6.QtCore import QThread, Signal

class HashWorker(QThread):
    """Computes cryptographic hashes in a background thread without freezing the UI."""
    hashes_ready = Signal(dict)
    progress = Signal(int)

    def __init__(self, data_source):
        super().__init__()
        self.data_source = data_source
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if not self.data_source or self.data_source.size <= 0:
            self.hashes_ready.emit({
                'md5': 'N/A',
                'sha1': 'N/A',
                'sha256': 'N/A',
                'crc32': 'N/A',
                'size_bytes': 0
            })
            return

        total_size = self.data_source.size
        # For very large files or memory, cap hashing to avoid extreme delays if > 500MB
        hash_limit = min(total_size, 500 * 1024 * 1024)

        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        crc = 0

        chunk_size = 512 * 1024
        offset = 0

        while offset < hash_limit and not self._is_cancelled:
            read_len = min(chunk_size, hash_limit - offset)
            chunk = self.data_source.read(offset, read_len)
            if not chunk:
                break
                
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
            crc = zlib.crc32(chunk, crc)
            
            offset += read_len
            prog = int((offset / hash_limit) * 100)
            self.progress.emit(prog)

        if not self._is_cancelled:
            self.hashes_ready.emit({
                'md5': md5.hexdigest().upper(),
                'sha1': sha1.hexdigest().upper(),
                'sha256': sha256.hexdigest().upper(),
                'crc32': f"{crc & 0xFFFFFFFF:08X}",
                'size_bytes': total_size,
                'partial': (hash_limit < total_size)
            })
