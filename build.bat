@echo off
setlocal

set "BUILD_DIR=build"

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

gcc -shared -o build/pan_protocol_lib.dll c_library/pan_protocol_lib.cpp c_library/pan_socket_io.cpp -lws2_32

endlocal