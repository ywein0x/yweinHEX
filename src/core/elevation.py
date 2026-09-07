import sys
import os
import ctypes
from ctypes import wintypes

advapi32 = ctypes.windll.advapi32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_PRIVILEGE_ENABLED = 0x00000002

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Privileges", LUID_AND_ATTRIBUTES * 1)]

def is_admin() -> bool:
    """Check if current process has Windows Administrator privileges."""
    try:
        return bool(shell32.IsUserAnAdmin())
    except Exception:
        return False

def enable_debug_privilege() -> bool:
    """
    Enable SeDebugPrivilege in the access token.
    Allows opening and inspecting memory of protected games and elevated processes.
    """
    try:
        h_token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(h_token)):
            return False
        
        luid = LUID()
        if not advapi32.LookupPrivilegeValueW(None, "SeDebugPrivilege", ctypes.byref(luid)):
            kernel32.CloseHandle(h_token)
            return False
            
        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
        
        res = advapi32.AdjustTokenPrivileges(h_token, False, ctypes.byref(tp), 0, None, None)
        kernel32.CloseHandle(h_token)
        return bool(res)
    except Exception:
        return False

def restart_as_admin() -> bool:
    """
    Relaunches the current script with Windows UAC elevation prompt (runas).
    If accepted by user, terminates the non-elevated instance.
    """
    if is_admin():
        return True

    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    cmd_args = f'"{script}" {params}'.strip()

    try:
        ret = shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            cmd_args,
            None,
            1  # SW_SHOWNORMAL
        )
        # ShellExecute returns an HINSTANCE > 32 on success
        if int(ret) > 32:
            sys.exit(0)
            return True
    except Exception:
        pass

    return False
