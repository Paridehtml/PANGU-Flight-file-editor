# Pangu Flight File Editor

This project provides a standalone Python application with a graphical user interface (GUI) for interacting with a Pangu 3D simulation server. The application allows users to load, visualize, edit, and play back camera position sequences from flight files, offering an intuitive and efficient interface for space simulation workflows.

## Features

- **Three-Column Layout**: A modern and organized interface for efficient workflow management.
- **Server Connection**: Connect to Pangu 3D space simulation servers.
- **Flight File Management**: Load, save, and "save as" for flight sequence files (`.fli`, `.txt`).
- **Visual Flight Editor**: A large, scrollable list displays all camera positions with detailed coordinates.
- **Frame Editing**: Interactively update, add, and delete frames in the flight sequence.
- **Playback Controls**: Play, pause, stop, and navigate through flight sequences frame-by-frame.
- **Real-time Preview**: View images from the Pangu server as you navigate or edit frames.
- **Manual Camera Controls**: Fine-tune camera positioning using Euler angles or quaternions.
- **Image Export**: Save the currently rendered view as a PNG or JPEG file.
- **Adjustable Playback Speed**: Control the playback FPS for smooth or detailed review.
- **Unsaved Changes Tracking**: The application tracks modifications and prompts the user before closing or loading a new file.

## Prerequisites

You need to have Python installed, along with the following libraries:

- `cffi`
- `Pillow`

You can install them using pip:
\`\`\`bash
pip install cffi Pillow
\`\`\`

You also need a C/C++ compiler accessible from your command line (like GCC from MinGW on Windows) to build the shared library.

## Setup and Usage

### 1. Compile the C Library

The core communication logic is contained within a C++ library. You must compile it into a shared library (`.dll` on Windows, `.so` on Linux) before running the Python application.

**Note:** The `.cpp` files in the `c_library` directory are placeholders. You must replace them with your actual implementation of the Pangu protocol functions.

#### On Windows:

Open a command prompt in the project's root directory and run the build script:

\`\`\`bash
build.bat
\`\`\`

This will create the `build/pan_protocol_lib.dll` file.

#### On Linux/macOS:

Open a terminal in the project's root directory and run the build script:

\`\`\`bash
chmod +x build.sh
./build.sh
\`\`\`

This will create the `build/pan_protocol_lib.so` file.

### 2. Run the Application

Once the library is compiled, you can run the main application:

\`\`\`bash
python main.py
\`\`\`

### 3. Using the Flight File Editor

#### Interface Layout

The application features a three-column layout for a clear and productive user experience:

- **Left Column**: Contains the main flight data tools:
  - **Camera Positions**: A large, scrollable list of all frames in the loaded flight file.
  - **Camera Parameters**: Tabs for manual camera control using Euler or Quaternion coordinates.
  - **Frame Editor**: Buttons to update, add, or delete frames.

- **Center Column**: The primary visual workspace:
  - **Image Display**: A large area showing the live preview from the Pangu server.
  - **Playback Controls**: Controls for playing, pausing, stopping, and navigating the flight sequence.

- **Right Column**: Manages connections and files:
  - **Server Connection**: Controls for connecting to and disconnecting from the Pangu server.
  - **Flight File**: Buttons for loading and saving flight files.

#### Workflow

1.  **Connect to Server**: Use the controls in the right column to connect to your Pangu server.
2.  **Load Flight File**: Click "Load Flight File..." to open a sequence file. The frames will appear in the "Camera Positions" list in the left column.
3.  **Navigate & Preview**: Click on any frame in the list or use the playback slider to navigate. The image display will update with a preview from the server.
4.  **Edit Frames**:
    -   Select a frame from the list. Its parameters will load into the "Camera Parameters" section.
    -   Modify the Euler angles.
    -   Click "Update" in the "Frame Editor" to apply the changes.
    -   Use "Add" to insert a new frame with the current parameters or "Delete" to remove the selected frame.
5.  **Playback**: Use the playback controls in the center column to watch the sequence in real-time. Adjust the FPS for desired speed.
6.  **Save Changes**: Use "Save Flight File" or "Save As..." to persist your edits. The window title will show an asterisk (`*`) if there are unsaved changes.

## Troubleshooting

-   **Connection Issues**: Ensure the Pangu server is running and accessible. Check your firewall settings and verify the server IP address and port.
-   **Flight File Errors**: Make sure the flight file lines start with `start` followed by 6 numeric values (X, Y, Z, Yaw, Pitch, Roll).
-   **Build Failures**: Confirm that a C++ compiler is installed and accessible in your system's PATH.
-   **Performance Problems**: If playback is choppy, try reducing the FPS value or ensure you have a stable network connection to the server.
