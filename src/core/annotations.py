import json
import struct
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class Annotation:
    offset: int
    label: str
    category: str = "General"  # Game/Entity, Pointer, Crypto, Network, Code, Variable
    color: str = "#a855f7"     # Purple default
    length: int = 4
    linked_target: Optional[int] = None  # Offset pointed to by this memory location
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Annotation":
        return cls(**data)


class AnnotationManager:
    """
    Manages user-approved annotations, notes, and pointer context links.
    """

    def __init__(self):
        self.annotations: Dict[int, Annotation] = {}

    def add(self, offset: int, label: str, category: str = "General", 
            color: str = "#a855f7", length: int = 4, 
            linked_target: Optional[int] = None, notes: str = "") -> Annotation:
        ann = Annotation(
            offset=offset,
            label=label,
            category=category,
            color=color,
            length=length,
            linked_target=linked_target,
            notes=notes
        )
        self.annotations[offset] = ann
        return ann

    def remove(self, offset: int) -> bool:
        if offset in self.annotations:
            del self.annotations[offset]
            return True
        return False

    def get(self, offset: int) -> Optional[Annotation]:
        return self.annotations.get(offset)

    def get_covering_annotation(self, offset: int) -> Optional[Annotation]:
        """Check if an offset falls inside an annotated range."""
        for start, ann in self.annotations.items():
            if start <= offset < start + max(1, ann.length):
                return ann
        return None

    def all_sorted(self) -> List[Annotation]:
        return sorted(self.annotations.values(), key=lambda a: a.offset)

    def clear(self):
        self.annotations.clear()

    def resolve_pointer_link(self, ann: Annotation, data_source, is_64bit: bool = True) -> Optional[int]:
        """
        Reads memory at annotation offset to determine if it points to a valid address.
        If pointing to an address within data_source, links it.
        """
        if not data_source or ann.offset >= data_source.size:
            return None

        endian = "<"  # Windows x86/x64 little-endian
        try:
            if is_64bit and ann.offset + 8 <= data_source.size:
                raw = data_source.read(ann.offset, 8)
                val = struct.unpack(f"{endian}Q", raw)[0]
            elif ann.offset + 4 <= data_source.size:
                raw = data_source.read(ann.offset, 4)
                val = struct.unpack(f"{endian}I", raw)[0]
            else:
                return None

            base = data_source.base_address
            # Check if val is absolute address matching base_address + relative offset
            if base <= val < base + data_source.size:
                target_offset = val - base
                ann.linked_target = target_offset
                return target_offset
            # Or if val is a direct relative offset
            elif 0 <= val < data_source.size:
                ann.linked_target = val
                return val
        except Exception:
            pass

        return None

    def export_json(self, filepath: str):
        data = [ann.to_dict() for ann in self.all_sorted()]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def import_json(self, filepath: str) -> int:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        for item in data:
            ann = Annotation.from_dict(item)
            self.annotations[ann.offset] = ann
            count += 1
        return count
