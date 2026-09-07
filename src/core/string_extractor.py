import re
from typing import List, Dict, Any

ASCII_REGEX = re.compile(rb"[A-Za-z0-9_\-\.\:\/\\ \t\r\n\(\)\{\}\[\]\<\>\@\#\$\%\^\&\*\+\=\;\,\'\"\?\!\|]{4,}")
UNICODE_REGEX = re.compile(rb"(?:[\x20-\x7E]\x00){4,}")

def extract_strings(data_source, max_scan: int = 5 * 1024 * 1024, min_len: int = 4, max_results: int = 2000) -> List[Dict[str, Any]]:
    """Scan data source up to max_scan bytes for ASCII and Unicode strings."""
    results = []
    chunk_size = 512 * 1024
    total_to_scan = min(data_source.size, max_scan)
    
    current_offset = 0
    while current_offset < total_to_scan and len(results) < max_results:
        read_len = min(chunk_size, total_to_scan - current_offset)
        chunk = data_source.read(current_offset, read_len)
        if not chunk:
            break
            
        # ASCII Matches
        for match in ASCII_REGEX.finditer(chunk):
            s = match.group()
            if len(s) >= min_len:
                try:
                    text = s.decode('ascii', errors='ignore')
                    results.append({
                        'offset': current_offset + match.start(),
                        'offset_hex': f"0x{(current_offset + match.start()):08X}",
                        'type': 'ASCII',
                        'length': len(text),
                        'value': text
                    })
                    if len(results) >= max_results:
                        break
                except Exception:
                    pass

        # Unicode Matches (UTF-16LE)
        if len(results) < max_results:
            for match in UNICODE_REGEX.finditer(chunk):
                s = match.group()
                if len(s) >= (min_len * 2):
                    try:
                        text = s.decode('utf-16le', errors='ignore')
                        results.append({
                            'offset': current_offset + match.start(),
                            'offset_hex': f"0x{(current_offset + match.start()):08X}",
                            'type': 'UTF-16',
                            'length': len(text),
                            'value': text
                        })
                        if len(results) >= max_results:
                            break
                    except Exception:
                        pass

        current_offset += read_len
        
    return results[:max_results]
