import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from PIL import ImageTk, Image
import threading
import time
from pangu_client import PanguClient
from flight_parser import FlightSequence

# Setup logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PanguClientApp(tk.Tk):
    """The main GUI application window."""
    def __init__(self):
        super().__init__()
        self.title("Pangu Flight File Editor")
        self.geometry("1400x900")

        # Client instance - using fixed server settings
        self.client = None
        self.current_image = None
        self.server_ip = '127.0.0.1'
        self.server_port = '10363'

        # Flight Sequence data and state
        self.flight_sequence = None
        self.playback_thread = None
        self.playback_running = threading.Event()
        self.playback_paused = threading.Event()
        self.current_frame_index = tk.IntVar(value=0)
        self.playback_fps = tk.DoubleVar(value=10.0)
        
        # Debounce mechanism for slider
        self.debounce_job = None
        
        # Camera controls visibility
        self.camera_controls_visible = tk.BooleanVar(value=False)

        self._create_widgets()
        self._toggle_controls(False)

    def _create_widgets(self):
        """Create and layout all the GUI widgets."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create two main columns with different proportions
        # Left column for controls
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Right column for image display
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Create a scrollable frame for controls ---
        controls_container = ttk.Frame(left_frame)
        controls_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(controls_container, width=400)
        scrollbar = ttk.Scrollbar(controls_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # --- End of scrollable frame setup ---

        self.image_label = ttk.Label(right_frame, text="Connect to server and load a flight file to begin", anchor=tk.CENTER, background="gray")
        self.image_label.pack(fill=tk.BOTH, expand=True)

        self._create_connection_controls(scrollable_frame)
        self._create_playback_controls(scrollable_frame)
        self._create_frame_list(scrollable_frame)
        self._create_camera_controls(scrollable_frame)
        self._create_status_bar()

    def _create_connection_controls(self, parent):
        """Connection controls for server connection."""
        connection_frame = ttk.LabelFrame(parent, text="Server Connection", padding="10")
        connection_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.connection_status_label = ttk.Label(connection_frame, text="Not connected")
        self.connection_status_label.pack(pady=2)
        
        self.connect_button = ttk.Button(connection_frame, text="Connect to Server", command=lambda: self.run_task(self.do_connect))
        self.connect_button.pack(fill=tk.X, pady=2)
        
        self.disconnect_button = ttk.Button(connection_frame, text="Disconnect", command=self.do_disconnect)
        self.disconnect_button.pack(fill=tk.X, pady=2)
        self.disconnect_button.config(state=tk.DISABLED)

    def _create_playback_controls(self, parent):
        playback_frame = ttk.LabelFrame(parent, text="Flight File Editor", padding="10")
        playback_frame.pack(fill=tk.X, pady=5, padx=5)

        load_button = ttk.Button(playback_frame, text="Load Flight File...", command=self.do_load_flight_file)
        load_button.grid(row=0, column=0, columnspan=5, sticky=tk.EW, pady=5)

        self.playback_status_label = ttk.Label(playback_frame, text="No flight file loaded.")
        self.playback_status_label.grid(row=1, column=0, columnspan=5, sticky=tk.W)

        # Playback control buttons
        self.play_button = ttk.Button(playback_frame, text="▶ Play", command=self.do_play)
        self.play_button.grid(row=2, column=0, sticky=tk.EW, padx=(0,2))
        
        self.pause_button = ttk.Button(playback_frame, text="❚❚ Pause", command=self.do_pause)
        self.pause_button.grid(row=2, column=1, sticky=tk.EW, padx=2)

        self.stop_button = ttk.Button(playback_frame, text="■ Stop", command=self.do_stop)
        self.stop_button.grid(row=2, column=2, sticky=tk.EW, padx=2)

        # Frame navigation buttons
        self.prev_frame_button = ttk.Button(playback_frame, text="◀", command=self.do_previous_frame, width=3)
        self.prev_frame_button.grid(row=2, column=3, sticky=tk.EW, padx=2)
        
        self.next_frame_button = ttk.Button(playback_frame, text="▶", command=self.do_next_frame, width=3)
        self.next_frame_button.grid(row=2, column=4, sticky=tk.EW, padx=(2,0))

        self.frame_slider = ttk.Scale(playback_frame, from_=0, to=0, orient=tk.HORIZONTAL, variable=self.current_frame_index, command=self.on_slider_drag)
        self.frame_slider.grid(row=3, column=0, columnspan=5, sticky=tk.EW, pady=5)
        
        fps_label_frame = ttk.Frame(playback_frame)
        fps_label_frame.grid(row=4, column=0, columnspan=5, sticky=tk.EW)
        # ttk.Label(fps_label_frame, text="FPS:").pack(side=tk.LEFT)
        # fps_entry = ttk.Entry(fps_label_frame, textvariable=self.playback_fps, width=5)
        # fps_entry.pack(side=tk.LEFT, padx=5)

        playback_frame.columnconfigure((0,1,2,3,4), weight=1)

    def _create_frame_list(self, parent):
        """A list widget to show all camera positions."""
        list_frame = ttk.LabelFrame(parent, text="Camera Positions", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Frame for listbox and scrollbars
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        # listbox with both vertical and horizontal scrollbars
        self.frame_listbox = tk.Listbox(
            listbox_frame, 
            height=25,
            font=("Courier", 9),
            width=50
        )
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.frame_listbox.yview)
        self.frame_listbox.configure(yscrollcommand=v_scrollbar.set)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(listbox_frame, orient="horizontal", command=self.frame_listbox.xview)
        self.frame_listbox.configure(xscrollcommand=h_scrollbar.set)
        
        # Grid layout for listbox and scrollbars
        self.frame_listbox.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.frame_listbox.bind('<<ListboxSelect>>', self.on_frame_select)
        
        # info label
        self.frame_info_label = ttk.Label(list_frame, text="Load a flight file to see camera positions")
        self.frame_info_label.pack(pady=5)

    def _create_camera_controls(self, parent):
        """Collapsible camera controls for both Euler and Quaternion."""
        # Header frame with toggle button
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.camera_toggle_button = ttk.Button(
            header_frame, 
            text="▼ Show Camera Controls", 
            command=self._toggle_camera_controls
        )
        self.camera_toggle_button.pack(fill=tk.X)
        
        # Camera controls frame (initially hidden)
        self.camera_frame = ttk.LabelFrame(parent, text="Camera Controls", padding="10")
        
        # notebook for tabs
        notebook = ttk.Notebook(self.camera_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Euler tab
        euler_tab = ttk.Frame(notebook)
        notebook.add(euler_tab, text="Euler Angles")
        
        self.euler_vars = [tk.DoubleVar(value=0.0) for _ in range(6)]
        labels = ["X", "Y", "Z", "Yaw", "Pitch", "Roll"]
        for i, label in enumerate(labels):
            ttk.Label(euler_tab, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=2, padx=5)
            ttk.Entry(euler_tab, textvariable=self.euler_vars[i], width=12).grid(row=i, column=1, sticky=tk.EW, pady=2, padx=5)
            
        self.euler_button = ttk.Button(euler_tab, text="Get Image (Euler)", command=lambda: self.run_task(self.do_update_euler))
        self.euler_button.grid(row=6, columnspan=2, pady=5, sticky=tk.EW, padx=5)
        
        # Save Image button in Euler tab
        self.save_image_button = ttk.Button(euler_tab, text="Save Image...", command=self.do_save_image)
        self.save_image_button.grid(row=7, columnspan=2, pady=5, sticky=tk.EW, padx=5)
        
        euler_tab.columnconfigure(1, weight=1)
        
        # Quaternion tab
        quat_tab = ttk.Frame(notebook)
        notebook.add(quat_tab, text="Quaternion")
        
        self.quat_vars = [tk.DoubleVar(value=0.0) for _ in range(7)]
        self.quat_vars[3].set(1.0)
        quat_labels = ["X", "Y", "Z", "Range", "Azimuth", "Elevation", "Roll"]
        for i, label in enumerate(quat_labels):
            ttk.Label(quat_tab, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=2, padx=5)
            ttk.Entry(quat_tab, textvariable=self.quat_vars[i], width=12).grid(row=i, column=1, sticky=tk.EW, pady=2, padx=5)

        self.quat_button = ttk.Button(quat_tab, text="Get Image (Quaternion)", command=lambda: self.run_task(self.do_update_quaternion))
        self.quat_button.grid(row=7, columnspan=2, pady=5, sticky=tk.EW, padx=5)
        
        # Save Image button in Quaternion tab
        self.save_image_button_quat = ttk.Button(quat_tab, text="Save Image...", command=self.do_save_image)
        self.save_image_button_quat.grid(row=8, columnspan=2, pady=5, sticky=tk.EW, padx=5)
        
        quat_tab.columnconfigure(1, weight=1)

    def _toggle_camera_controls(self):
        """Toggle visibility of camera controls."""
        if self.camera_controls_visible.get():
            # Hide controls
            self.camera_frame.pack_forget()
            self.camera_toggle_button.config(text="▼ Show Camera Controls")
            self.camera_controls_visible.set(False)
        else:
            # Show controls
            self.camera_frame.pack(fill=tk.X, pady=5, padx=5)
            self.camera_toggle_button.config(text="▲ Hide Camera Controls")
            self.camera_controls_visible.set(True)

    def _create_status_bar(self):
        self.status_var = tk.StringVar(value="Ready. Connect to server to begin.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _populate_frame_list(self):
        """Populate the listbox with camera positions from the flight sequence."""
        self.frame_listbox.delete(0, tk.END)
        
        if not self.flight_sequence or self.flight_sequence.get_frame_count() == 0:
            self.frame_info_label.config(text="No camera positions available")
            return
        
        for i in range(self.flight_sequence.get_frame_count()):
            params = self.flight_sequence.get_frame(i)
            if params:
                frame_text = f"Frame {i+1:03d}: X={params[0]:8.1f} Y={params[1]:8.1f} Z={params[2]:8.1f} Yaw={params[3]:6.1f} Pitch={params[4]:6.1f} Roll={params[5]:6.1f}"
                self.frame_listbox.insert(tk.END, frame_text)
    
        self.frame_info_label.config(text=f"{self.flight_sequence.get_frame_count()} camera positions loaded")

    def on_frame_select(self, event):
        """Handle selection of a frame from the listbox."""
        selection = self.frame_listbox.curselection()
        if selection:
            frame_index = selection[0]
            self.current_frame_index.set(frame_index)
            
            # Update the slider position
            self.frame_slider.set(frame_index)
            
            # Trigger the image update
            self.on_slider_drag()

    def _toggle_controls(self, connected):
        """Enable or disable controls based on connection status."""
        state = tk.NORMAL if connected else tk.DISABLED
        self.euler_button.config(state=state)
        self.quat_button.config(state=state)
        
        # Connection buttons
        self.connect_button.config(state=tk.DISABLED if connected else tk.NORMAL)
        self.disconnect_button.config(state=tk.NORMAL if connected else tk.DISABLED)
        
        if not connected:
            self.save_image_button.config(state=tk.DISABLED)
            self.save_image_button_quat.config(state=tk.DISABLED)
        
        self._update_playback_controls_state()

    def _update_playback_controls_state(self):
        """Update the state of playback controls."""
        is_connected = self.client and self.client.is_connected
        sequence_loaded = self.flight_sequence and self.flight_sequence.get_frame_count() > 0
        
        can_play = is_connected and sequence_loaded
        can_navigate = is_connected and sequence_loaded and (not self.playback_running.is_set() or self.playback_paused.is_set())
        
        self.play_button.config(state=tk.NORMAL if can_play else tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL if can_play else tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL if can_play else tk.DISABLED)
        self.frame_slider.config(state=tk.NORMAL if can_play else tk.DISABLED)
        
        # Frame navigation buttons are enabled only when not playing or when paused
        self.prev_frame_button.config(state=tk.NORMAL if can_navigate else tk.DISABLED)
        self.next_frame_button.config(state=tk.NORMAL if can_navigate else tk.DISABLED)

    def update_status(self, message):
        self.status_var.set(message)
        self.update_idletasks()

    def display_image(self, img):
        if img:
            self.current_image = img.copy()
            label_w, label_h = self.image_label.winfo_width(), self.image_label.winfo_height()
            if label_w > 1 and label_h > 1:
                img.thumbnail((label_w, label_h), Image.Resampling.LANCZOS)

            self.tk_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.tk_image, text="")
            self.save_image_button.config(state=tk.NORMAL)
            self.save_image_button_quat.config(state=tk.NORMAL)
        else:
            self.current_image = None
            self.image_label.config(image=None, text="Failed to load image.")
            self.save_image_button.config(state=tk.DISABLED)
            self.save_image_button_quat.config(state=tk.DISABLED)

    def run_task(self, task_func, *args, **kwargs):
        thread = threading.Thread(target=task_func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()

    def do_connect(self):
        self.update_status("Connecting to Pangu server...")
        self.connection_status_label.config(text="Connecting...")
        
        self.client = PanguClient(self.server_ip, self.server_port)
        status, msg = self.client.connect()
        
        if status:
            self.connection_status_label.config(text="✓ Connected to Pangu server")
            self.update_status("Connected successfully. Load a flight file to begin.")
        else:
            self.connection_status_label.config(text="✗ Connection failed")
            self.update_status(f"Connection failed: {msg}")
        
        self._toggle_controls(status)

    def do_disconnect(self):
        self.update_status("Disconnecting from server...")
        self.do_stop()
        if self.client:
            self.client.disconnect()
        self.connection_status_label.config(text="Disconnected")
        self.update_status("Disconnected from server.")
        self._toggle_controls(False)
        self.display_image(None)

    def do_update_euler(self, params=None, update_gui_entries=True):
        self.update_status("Requesting image with Euler angles...")
        try:
            if params is None:
                params = [var.get() for var in self.euler_vars]
            image, msg = self.client.update_camera_euler(params)
            self.after(0, self.update_status, msg)
            self.after(0, self.display_image, image)
            if update_gui_entries:
                self.after(0, self._update_euler_entries, params)
        except Exception as e:
            self.after(0, self.update_status, f"Error: {e}")

    def _update_euler_entries(self, params):
        for i, var in enumerate(self.euler_vars):
            var.set(params[i])

    def do_update_quaternion(self):
        self.update_status("Requesting image with Quaternion...")
        try:
            params = [var.get() for var in self.quat_vars]
            image, msg = self.client.update_camera_quaternion(params)
            self.update_status(msg)
            self.display_image(image)
        except Exception as e:
            self.update_status(f"Error: {e}")

    def do_save_image(self):
        if not self.current_image:
            messagebox.showwarning("Save Error", "No image to save.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if not filepath: return
        try:
            self.update_status(f"Saving image to {filepath}...")
            self.current_image.save(filepath)
            self.update_status(f"Image saved successfully to {filepath}")
        except Exception as e:
            self.update_status(f"Failed to save image: {e}")

    def do_load_flight_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a Flight Sequence File",
            filetypes=[("Flight files", "*.fli"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath: return
        self.do_stop()
        self.flight_sequence = FlightSequence(filepath)
        frame_count = self.flight_sequence.get_frame_count()
        if frame_count > 0:
            self.playback_status_label.config(text=f"{frame_count} frames loaded.")
            self.frame_slider.config(to=frame_count - 1)
            self.current_frame_index.set(0)
            self._populate_frame_list()  # Populate the new list
            self.on_slider_drag()
        else:
            self.playback_status_label.config(text="Failed to load flight file.")
            self._populate_frame_list()  # Clear the list
            messagebox.showerror("Load Error", "Could not parse any valid frames from the selected file.")
        self._update_playback_controls_state()

    def do_play(self):
        if not self.playback_running.is_set():
            self.playback_running.set()
            self.playback_paused.clear()
            self.playback_thread = threading.Thread(target=self._playback_loop)
            self.playback_thread.daemon = True
            self.playback_thread.start()
        elif self.playback_paused.is_set():
            self.playback_paused.clear()
        self.play_button.config(text="▶ Play")
        self.pause_button.config(text="❚❚ Pause")
        self._update_playback_controls_state()

    def do_pause(self):
        if self.playback_running.is_set():
            if self.playback_paused.is_set():
                self.playback_paused.clear()
                self.pause_button.config(text="❚❚ Pause")
            else:
                self.playback_paused.set()
                self.pause_button.config(text="► Resume")
        self._update_playback_controls_state()

    def do_stop(self):
        self.playback_running.clear()
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=0.5)
        self.current_frame_index.set(0)
        self.pause_button.config(text="❚❚ Pause")
        self.play_button.config(text="▶ Play")
        self._update_playback_controls_state()

    def on_slider_drag(self, *args):
        if self.debounce_job:
            self.after_cancel(self.debounce_job)
        
        frame_index = self.current_frame_index.get()
        params = self.flight_sequence.get_frame(frame_index)
        if params:
            self._update_euler_entries(params)
            # Update listbox selection to match slider
            self.frame_listbox.selection_clear(0, tk.END)
            self.frame_listbox.selection_set(frame_index)
            self.frame_listbox.see(frame_index)  # Scroll to make it visible
            
        self.debounce_job = self.after(250, self._perform_slider_image_request)

    def _perform_slider_image_request(self):
        self.debounce_job = None
        if not self.playback_running.is_set() or self.playback_paused.is_set():
            frame_index = self.current_frame_index.get()
            params = self.flight_sequence.get_frame(frame_index)
            if params:
                self.run_task(self.do_update_euler, params, update_gui_entries=False)

    def _playback_loop(self):
        while self.playback_running.is_set():
            if self.playback_paused.is_set():
                time.sleep(0.1)
                continue
            frame_idx = self.current_frame_index.get()
            if frame_idx >= self.flight_sequence.get_frame_count(): break
            params = self.flight_sequence.get_frame(frame_idx)
            if self.client and self.client.is_connected:
                self.do_update_euler(params, update_gui_entries=False)
                self.after(0, self._update_gui_for_playback, params, frame_idx + 1)
            try:
                delay = 1.0 / self.playback_fps.get()
                time.sleep(delay)
            except (ZeroDivisionError, tk.TclError):
                time.sleep(0.1)
        self.after(0, self.do_stop)

    def _update_gui_for_playback(self, params, next_frame_idx):
        if not self.playback_running.is_set(): return
        self._update_euler_entries(params)
        self.current_frame_index.set(next_frame_idx)
        # Update listbox selection during playback
        self.frame_listbox.selection_clear(0, tk.END)
        if next_frame_idx < self.flight_sequence.get_frame_count():
            self.frame_listbox.selection_set(next_frame_idx)
            self.frame_listbox.see(next_frame_idx)

    def on_closing(self):
        self.update_status("Closing application...")
        if self.debounce_job:
            self.after_cancel(self.debounce_job)
        self.do_stop()
        if self.client and self.client.is_connected:
            self.client.disconnect()
        self.destroy()

    def do_previous_frame(self):
        if not self.flight_sequence or self.flight_sequence.get_frame_count() == 0:
            return
        
        current_frame = self.current_frame_index.get()
        if current_frame > 0:
            self.current_frame_index.set(current_frame - 1)
            self.on_slider_drag()

    def do_next_frame(self):
        if not self.flight_sequence or self.flight_sequence.get_frame_count() == 0:
            return
        
        current_frame = self.current_frame_index.get()
        max_frame = self.flight_sequence.get_frame_count() - 1
        if current_frame < max_frame:
            self.current_frame_index.set(current_frame + 1)
            self.on_slider_drag()

if __name__ == "__main__":
    app = PanguClientApp()
    app.mainloop()
