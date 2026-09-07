import os
import mmap
import ctypes
from ctypes import wintypes
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import psutil

# Windows API Constants & Types
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", wintypes.LPVOID),
        ("AllocationBase", wintypes.LPVOID),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]

class DataSource(ABC):
    """Abstract Base Class for Hex View data source (File or Process Memory)."""

    def __init__(self, name: str, base_address: int = 0):
        self.name = name
        self.base_address = base_address

    @property
    @abstractmethod
    def size(self) -> int:
        pass

    @abstractmethod
    def read(self, offset: int, length: int) -> bytes:
        pass

    @property
    def is_process(self) -> bool:
        return False

    def close(self):
        pass


class FileSource(DataSource):
    """High-performance file data source supporting files of any size without loading all into RAM."""

    def __init__(self, filepath: str):
        self.filepath = os.path.abspath(filepath)
        filename = os.path.basename(self.filepath)
        super().__init__(name=filename, base_address=0)
        self._file_size = os.path.getsize(self.filepath)
        self._file = open(self.filepath, "rb")
        self._mmap: Optional[mmap.mmap] = None
        
        # Use mmap if file size > 0 and reasonable (under 1GB for 32/64-bit safety, or fallback to seek)
        if 0 < self._file_size < 1024 * 1024 * 1024:
            try:
                self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
            except Exception:
                self._mmap = None

    @property
    def size(self) -> int:
        return self._file_size

    def read(self, offset: int, length: int) -> bytes:
        if offset < 0 or offset >= self._file_size or length <= 0:
            return b""
        
        actual_len = min(length, self._file_size - offset)
        if self._mmap is not None:
            return self._mmap[offset : offset + actual_len]
        
        try:
            self._file.seek(offset)
            return self._file.read(actual_len)
        except Exception:
            return b"\x00" * actual_len

    def close(self):
        if self._mmap is not None:
            try:
                self._mmap.close()
            except Exception:
                pass
            self._mmap = None
        if self._file and not self._file.closed:
            try:
                self._file.close()
            except Exception:
                pass


class ProcessSource(DataSource):
    """Data source for inspecting a live Windows Process memory or specific module/region."""

    def __init__(self, pid: int, base_address: int, region_size: int, module_name: str = ""):
        self.pid = pid
        self._size = region_size
        name = f"PID {pid}"
        if module_name:
            name += f" - {module_name}"
        super().__init__(name=name, base_address=base_address)
        
        self.h_process = None
        self._kernel32 = ctypes.windll.kernel32
        self._open_process()

    def _open_process(self):
        # Request VM Read & Query Information permissions
        access = PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
        self.h_process = self._kernel32.OpenProcess(access, False, self.pid)
        if not self.h_process:
            # Try limited info if elevated process
            access = PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION
            self.h_process = self._kernel32.OpenProcess(access, False, self.pid)

    @property
    def is_process(self) -> bool:
        return True

    @property
    def size(self) -> int:
        return self._size

    def read(self, offset: int, length: int) -> bytes:
        if not self.h_process or offset < 0 or offset >= self._size or length <= 0:
            return b"\x00" * length
        
        actual_len = min(length, self._size - offset)
        target_addr = self.base_address + offset
        buffer = (ctypes.c_char * actual_len)()
        bytes_read = ctypes.c_size_t(0)
        
        success = self._kernel32.ReadProcessMemory(
            self.h_process,
            ctypes.c_void_p(target_addr),
            buffer,
            actual_len,
            ctypes.byref(bytes_read)
        )
        
        if success and bytes_read.value > 0:
            data = buffer.raw[:bytes_read.value]
            if len(data) < actual_len:
                data += b"\x00" * (actual_len - len(data))
            return data
        else:
            # Unmapped, guarded, or protected page in process address space
            return b"\x00" * actual_len

    def close(self):
        if self.h_process:
            self._kernel32.CloseHandle(self.h_process)
            self.h_process = None


def get_running_processes() -> List[Dict[str, Any]]:
    """Enumerate running processes with useful metadata for inspection."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_info']):
        try:
            info = p.info
            name = info.get('name') or 'Unknown'
            pid = info.get('pid') or 0
            exe = info.get('exe') or ''
            mem = info.get('memory_info')
            mem_rss = mem.rss if mem else 0
            procs.append({
                'pid': pid,
                'name': name,
                'exe': exe,
                'memory_rss': mem_rss,
                'memory_str': f"{mem_rss / (1024 * 1024):.1f} MB" if mem_rss else "0 MB"
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(procs, key=lambda x: x['name'].lower())


class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", wintypes.LPVOID),
        ("SizeOfImage", wintypes.DWORD),
        ("EntryPoint", wintypes.LPVOID),
    ]

def get_process_modules(pid: int) -> List[Dict[str, Any]]:
    """Enumerate loaded DLLs and executable modules for a process with base address and size."""
    modules = []
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    
    access = PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
    h_proc = kernel32.OpenProcess(access, False, pid)
    if not h_proc:
        access = PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION
        h_proc = kernel32.OpenProcess(access, False, pid)
    
    if not h_proc:
        return modules
        
    try:
        # Array of HMODULEs
        h_mods = (wintypes.HMODULE * 1024)()
        cb_needed = wintypes.DWORD()
        
        if psapi.EnumProcessModules(h_proc, ctypes.byref(h_mods), ctypes.sizeof(h_mods), ctypes.byref(cb_needed)):
            num_mods = int(cb_needed.value / ctypes.sizeof(wintypes.HMODULE))
            for i in range(num_mods):
                h_mod = h_mods[i]
                if not h_mod:
                    continue
                
                # Module path
                mod_name_buf = (ctypes.c_wchar * 1024)()
                psapi.GetModuleFileNameExW(h_proc, h_mod, mod_name_buf, 1024)
                mod_path = mod_name_buf.value
                mod_name = os.path.basename(mod_path) if mod_path else f"Module_{i}"
                
                # Module info
                mod_info = MODULEINFO()
                if psapi.GetModuleInformation(h_proc, h_mod, ctypes.byref(mod_info), ctypes.sizeof(mod_info)):
                    base_addr = mod_info.lpBaseOfDll if isinstance(mod_info.lpBaseOfDll, int) else (mod_info.lpBaseOfDll or 0)
                    size = mod_info.SizeOfImage
                    entry = mod_info.EntryPoint if isinstance(mod_info.EntryPoint, int) else (mod_info.EntryPoint or 0)
                    
                    modules.append({
                        'name': mod_name,
                        'path': mod_path,
                        'base_address': base_addr,
                        'base_hex': f"0x{base_addr:016X}" if base_addr > 0xFFFFFFFF else f"0x{base_addr:08X}",
                        'size': size,
                        'size_str': f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.2f} MB",
                        'entry_point': entry,
                        'entry_hex': f"0x{entry:016X}" if entry > 0xFFFFFFFF else f"0x{entry:08X}",
                    })
    except Exception:
        pass
    finally:
        kernel32.CloseHandle(h_proc)
        
    return modules

