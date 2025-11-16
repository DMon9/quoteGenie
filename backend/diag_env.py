import sys, importlib.util, os
print('Python', sys.version)
print('Executable:', sys.executable)
print('CWD:', os.getcwd())
spec = importlib.util.find_spec('pytest')
print('Has pytest?', spec is not None)
print('sys.path:')
for p in sys.path:
    print('  ', p)
