import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, messagebox
import yt_dlp
import threading
import os
import sys

# Logging setup if needed
import logging
logging.basicConfig(filename='yt_dlp.log', level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define constants for easy adjustments
NUM_THREADS = 4

class StdoutRedirector:
    """Class for redirecting stdout/stderr to a tkinter widget."""
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        self.widget.configure(state='normal')
        self.widget.insert('end', string)
        self.widget.configure(state='disabled')
        self.widget.yview('end')

    def flush(self):
        pass

def download_video(url, file_format):
    ydl_opts = {
        'format': 'bestaudio/best',
        'embed-metadata' : True,
        'addmetadata': True,
        'writethumbnail': True,  # Write the thumbnail to disk
        'postprocessors': [
            # Extract audio
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': file_format,
                'preferredquality': '192',
            },
            # Embed thumbnail in audio as cover art
            {
                'key': 'EmbedThumbnail',
            },
            # Embed metadata (this will also ensure the thumbnail gets embedded)
            {
                'key': 'FFmpegMetadata',
            },
        ],
        'outtmpl': f'%(title)s.%(ext)s',
        'cleanup': True  # Clean up after post-processing
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def worker(urls, file_format, output_widget, status_labels, thread_id):
    """Function for threads to download videos."""
    for index, url in enumerate(urls):
        try:
            download_video(url, file_format)
            # Update status label from the thread using after method of the main thread
            app.after(0, lambda i=index: status_labels[i].configure(text=f"{i+1}: ✓", fg_color="green"))
        except Exception as exc:
            output_widget.write(f'Error downloading {url}: {exc}\n')
            app.after(0, lambda i=index: status_labels[i].configure(text=f"{i+1}: ✗", fg_color="red"))

    output_widget.write(f"Thread {thread_id} completed.\n")

def check_threads(threads, output_widget):
    """Check the status of threads and update the GUI accordingly."""
    if all(not thread.is_alive() for thread in threads):
        output_widget.write("All downloads are complete.\n")
        download_directory = os.getcwd()
        os.startfile(download_directory)
    else:
        app.after(1000, lambda: check_threads(threads, output_widget))

def start_download(urls, file_format, output_widget, status_labels):
    """Function to handle the download process in threads."""
    threads = []
    for i in range(NUM_THREADS):
        thread_urls = urls[i::NUM_THREADS]  # Distribute URLs among threads
        thread = threading.Thread(target=worker, args=(thread_urls, file_format, output_widget, status_labels, i))
        threads.append(thread)
        thread.start()

    check_threads(threads, output_widget)  # Check if all threads have finished

def on_convert_click():
    """Function called when the Convert button is clicked."""
    content = url_textbox.get("1.0", "end-1c").strip()
    urls = [line for line in content.split('\n') if line]
    
    if not urls:
        messagebox.showerror("Error", "No URLs provided.")
        return
    
    file_format = format_optionmenu.get()
    
    # Clear and create new status labels for each URL
    for label in status_labels:
        label.destroy()
    status_labels.clear()
    
    for i, _ in enumerate(urls):
        label = ctk.CTkLabel(center_frame, text=f"{i+1}:")
        label.pack()
        status_labels.append(label)
    
    stdout_redirector = StdoutRedirector(console_output)
    sys.stdout = stdout_redirector
    sys.stderr = stdout_redirector
    
    start_download(urls, file_format, stdout_redirector, status_labels)

# GUI setup
app = ctk.CTk()
app.title('YouTube Downloader')
app.geometry('1000x600')

# The left frame for URLs
left_frame = ctk.CTkFrame(app)
left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

url_label = ctk.CTkLabel(left_frame, text="Enter URLs (one per line):")
url_label.pack()

# Enlarge the URL textbox vertically
url_textbox = scrolledtext.ScrolledText(left_frame, wrap='none', height=30)  # Increase height as needed
url_textbox.pack(pady=(0, 10), fill='both', expand=True)

# The center frame for file format selection and status labels
center_frame = ctk.CTkFrame(app)
center_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

format_label = ctk.CTkLabel(center_frame, text="Select file format:")
format_label.pack()

format_optionmenu = ctk.CTkOptionMenu(center_frame, values=["mp3", "wav", "aac", "flac", "m4a", "opus", "vorbis", "wav"])
format_optionmenu.pack()


# This container will hold the status labels
status_container = ctk.CTkFrame(center_frame)
status_container.pack(fill='both', expand=True)

# The right frame for console output
right_frame = ctk.CTkFrame(app)
right_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

console_label = ctk.CTkLabel(right_frame, text="Console Output:")
console_label.pack()

# Enlarge the console output vertically
console_output = scrolledtext.ScrolledText(right_frame, height=50, width=250, state='disabled')
console_output.pack(padx=10, pady=10)

# The Download button should be at the bottom of the center frame
download_button = ctk.CTkButton(right_frame, text="Download", command=on_convert_click)
download_button.pack(pady=10)

# Initialize the list for status labels to be filled during download
status_labels = []

app.mainloop()

