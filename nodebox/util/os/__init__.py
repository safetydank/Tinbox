import nodebox.util.os.path as path

__all__ = ["path", "getcwd"]

from System.IO.Directory import GetCurrentDirectory

def getcwd():
    return GetCurrentDirectory()

