import System.IO.Path as Path

def splitext(fname):
    dirname = Path.GetDirectoryName(fname)
    basename = Path.GetFileNameWithoutExtension(fname)
    ext = Path.GetExtension(fname)
    return (Path.Combine(dirname, basename), ext)

def join(*args):
    return reduce(Path.Combine, args)

