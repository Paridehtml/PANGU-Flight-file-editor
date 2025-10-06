import socket
import logging
import io
from PIL import Image
from pan_protocol_wrapper import get_pan_library

logger = logging.getLogger(__name__)

class PanguClient:

    def __init__(self, ip, port):
        self.server_ip = ip
        self.server_port = int(port)
        self.sock = None
        self.lib = None
        self.ffi = None
        self.sock_fd = -1
        self.is_connected = False

    def connect(self):
        """Establishes a persistent connection to the Pangu server."""
        if self.is_connected:
            return True, "Already connected."
            
        try:
            self.lib, self.ffi = get_pan_library()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.server_ip, self.server_port)
            logger.info(f'Connecting to {self.server_ip}:{self.server_port}')
            self.sock.connect(server_address)
            self.sock_fd = self.sock.fileno()
            self.lib.pan_protocol_start(self.sock_fd)
            self.is_connected = True
            logger.info(f'Connected successfully.')
            return True, "Connected successfully."
        except Exception as e:
            error_message = f'Error connecting to Pangu Server: {e}'
            logger.error(error_message)
            self.sock = None
            self.sock_fd = -1
            self.lib = None # Ensure lib is None on failure
            self.is_connected = False
            return False, error_message

    def disconnect(self):
        """Disconnects from the Pangu server."""
        if not self.is_connected:
            return
            
        if self.sock and self.lib:
            try:
                self.lib.pan_protocol_finish(self.sock_fd)
                self.sock.close()
                logger.info("Disconnected successfully.")
            except Exception as e:
                logger.error(f"Error during disconnection: {e}")
        
        self.sock = None
        self.sock_fd = -1
        self.is_connected = False

    def _get_image_from_server(self, get_image_func, *args):
       
        if not self.is_connected or not self.lib:
            return None, "Not connected to the server."

        try:
            size_ptr = self.ffi.new("unsigned long *")
            logger.info(f'Requesting image with function {get_image_func.__name__}...')
            image_ptr = get_image_func(self.sock_fd, *args, size_ptr)
            
            if image_ptr == self.ffi.NULL:
                logger.error("Received NULL pointer for image.")
                return None, "Failed to get image from server (received NULL)."

            image_size = size_ptr[0]
            if image_size == 0:
                logger.warning("Received image with size 0.")
                return None, "Received an empty image from server."

            image_data = self.ffi.buffer(image_ptr, image_size)[:]
            logger.info(f'Got image of size {image_size} bytes.')
            
            image_stream = io.BytesIO(image_data)
            image = Image.open(image_stream)
            return image, "Image received successfully."
        except Exception as e:
            error_message = f'Error during image retrieval: {e}'
            logger.error(error_message)
            return None, error_message

    def get_image(self):
        """Gets an image using the current server camera settings."""
        return self._get_image_from_server(self.lib.pan_protocol_get_image)

    def update_camera_euler(self, params):
        """Sets camera viewpoint using Euler angles and gets an image."""
        return self._get_image_from_server(self.lib.pan_protocol_get_viewpoint_by_degrees_d, *params)

    def update_camera_quaternion(self, params):
        """Sets camera viewpoint using a quaternion and gets an image."""
        return self._get_image_from_server(self.lib.pan_protocol_get_viewpoint_by_quaternion_s, *params)
