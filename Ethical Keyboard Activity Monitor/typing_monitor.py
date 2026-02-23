"""
Ethical Keyboard Activity Monitor
Tracks typing activity with user consent.
"""

import tkinter as tk
from collections import Counter
import time

class TypingMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ethical Keyboard Activity Monitor")
        self.key_count = 0
        self.start_time = None
        self.key_freq = Counter()
        self.last_minute_keys = []
        self.active = False
        self.sensitive_mode = False

        self.info_label = tk.Label(root, text="Press 'Start Monitoring' to begin.")
        self.info_label.pack(pady=10)

        self.stats_label = tk.Label(root, text="")
        self.stats_label.pack(pady=10)

        self.start_btn = tk.Button(root, text="Start Monitoring", command=self.start_monitoring)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        self.root.bind('<FocusIn>', self.on_focus_in)
        self.root.bind('<FocusOut>', self.on_focus_out)

    def start_monitoring(self):
        self.active = True
        self.key_count = 0
        self.key_freq.clear()
        self.last_minute_keys.clear()
        self.start_time = time.time()
        self.info_label.config(text="Monitoring... (App must be focused)")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.root.bind('<Key>', self.on_key_press)
        self.update_stats()

    def stop_monitoring(self):
        self.active = False
        self.info_label.config(text="Monitoring stopped.")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.root.unbind('<Key>')
        self.stats_label.config(text="")

    def on_focus_in(self, event):
        if self.active:
            self.info_label.config(text="Monitoring... (App is focused)")

    def on_focus_out(self, event):
        if self.active:
            self.info_label.config(text="Monitoring paused (App not focused)")

    def on_key_press(self, event):
        if not self.active or not self.root.focus_displayof():
            return
        # Exclude sensitive input (rudimentary: skip if Entry widget is password)
        widget = self.root.focus_get()
        if isinstance(widget, tk.Entry) and widget.cget('show'):
            return
        self.key_count += 1
        self.key_freq[event.keysym] += 1
        now = time.time()
        self.last_minute_keys.append(now)
        # Remove keys older than 60 seconds
        self.last_minute_keys = [t for t in self.last_minute_keys if now - t <= 60]

    def update_stats(self):
        if self.active:
            wpm = len(self.last_minute_keys) / 5  # 5 chars per word
            most_common = self.key_freq.most_common(5)
            stats = f"Keys pressed: {self.key_count}\nWPM: {wpm:.1f}\nMost frequent: {most_common}"
            self.stats_label.config(text=stats)
            self.root.after(1000, self.update_stats)

def show_consent_dialog():
    consent_root = tk.Tk()
    consent_root.title("Consent Required")
    consent_text = (
        "This app tracks your typing activity (number of keys, WPM, most used keys) "
        "ONLY while this window is active.\n\n"
        "Sensitive input (like passwords) is NOT recorded.\n\n"
        "By clicking 'I Consent', you agree to this monitoring."
    )
    label = tk.Label(consent_root, text=consent_text, wraplength=350, justify="left")
    label.pack(padx=20, pady=15)
    consent_given = {'value': False}

    def accept():
        consent_given['value'] = True
        consent_root.destroy()

    def decline():
        consent_root.destroy()

    btn_frame = tk.Frame(consent_root)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="I Consent", command=accept).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Decline", command=decline).pack(side="left", padx=10)
    consent_root.mainloop()
    return consent_given['value']

if __name__ == "__main__":
    if show_consent_dialog():
        root = tk.Tk()
        app = TypingMonitorApp(root)
        root.mainloop()
    else:
        print("Consent not given. Exiting.")
