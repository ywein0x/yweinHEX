import math
from typing import List

def calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy for a block of bytes (returns 0.0 to 8.0)."""
    if not data:
        return 0.0
    
    length = len(data)
    frequencies = [0] * 256
    for b in data:
        frequencies[b] += 1
        
    entropy = 0.0
    for count in frequencies:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
            
    return entropy

def calculate_entropy_blocks(data_source, total_size: int, block_count: int = 128) -> List[float]:
    """Sample data source across uniform blocks to plot an entropy curve/histogram."""
    if total_size <= 0:
        return []
    
    block_size = max(1024, total_size // block_count)
    actual_blocks = min(block_count, max(1, total_size // block_size))
    
    entropies = []
    step = total_size / actual_blocks
    
    for i in range(actual_blocks):
        offset = int(i * step)
        read_len = min(block_size, total_size - offset)
        chunk = data_source.read(offset, read_len)
        entropies.append(calculate_entropy(chunk))
        
    return entropies
