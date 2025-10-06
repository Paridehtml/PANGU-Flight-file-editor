import cffi
import os
import platform

# Path to your library
MODULE_DIR = os.path.dirname(__file__)
HEADER_PATH = os.path.join(MODULE_DIR, 'pan_protocol_lib_bindings.h')

if platform.system() == 'Linux':
    LIBRARY_PATH = os.path.join(MODULE_DIR, 'build/pan_protocol_lib.so')
elif platform.system() == 'Windows':
    LIBRARY_PATH = os.path.join(MODULE_DIR, 'build/pan_protocol_lib.dll')

def get_pan_library():
    ffi = cffi.FFI()

    with open(HEADER_PATH) as header_file:
        ffi.cdef(header_file.read())
        
    try:
        lib = ffi.dlopen(LIBRARY_PATH)
    except OSError as e:
        raise RuntimeError(f'Failed to load the shared library: {e}')
    
    return lib, ffi

def test():
    try:
        
        lib, cffi = get_pan_library()
        lib.pan_protocol_safety_checks()
        
        print('Testing complete')
    
    except OSError as e:
        # Handle errors related to loading the shared library
        print(f'Failed to load shared library or function: {e}')
    
    except AttributeError as e:
        # Handle errors related to missing functions in the shared library
        print(f'Function not found in shared library: {e}')

    except Exception as e:
        # Handle any other unexpected errors
        print(f'An unexpected error occurred: {e}')

if __name__ == '__main__':
    test()