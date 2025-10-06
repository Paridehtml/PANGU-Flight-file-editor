import logging

logger = logging.getLogger(__name__)

class FlightSequence:
    """
    Parses and stores a flight sequence from a Pangu flight file.
    The expected format for each line is:
    start X Y Z Yaw Pitch Roll
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.frames = []
        self._parse()

    def _parse(self):
        """Reads the file and parses the frames."""
        logger.info(f"Parsing flight file: {self.filepath}")
        try:
            with open(self.filepath, 'r') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    # Skip empty lines or lines not starting with 'start'
                    if not line or not line.lower().startswith('start'):
                        continue
                    
                    parts = line.split()
                    # A valid line should have 'start' + 6 numeric values
                    if len(parts) != 7:
                        logger.warning(f"Skipping malformed line {i+1} in {self.filepath}: Expected 7 parts, found {len(parts)}.")
                        continue
                    
                    try:
                        # parts[0] is 'start', parts[1] to parts[6] are the Euler angle values
                        params = [float(p) for p in parts[1:]]
                        self.frames.append(params)
                    except ValueError:
                        logger.warning(f"Skipping malformed line {i+1} in {self.filepath}: Could not convert parts to float.")
                        continue
        except Exception as e:
            logger.error(f"Failed to read or parse flight file {self.filepath}: {e}")
            self.frames = []  # Ensure frames list is empty on error
        
        if self.frames:
            logger.info(f"Successfully parsed {len(self.frames)} frames from {self.filepath}.")
        else:
            logger.error(f"No valid frames were parsed from {self.filepath}.")

    def get_frame_count(self):
        """Returns the total number of frames in the sequence."""
        return len(self.frames)

    def get_frame(self, index):
        """Returns the parameters for a specific frame index."""
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None
