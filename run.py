import tkinter as tk
from tkinter import ttk
import time
import threading
import json
from playsound import playsound
import subprocess
from wakepy import keep
import os

def load_config(file_path):
    file_path = 'config.json'
    file_path = file_path if os.path.exists(file_path) else 'config_example.json'
    with open(file_path, 'r') as file:
        return json.load(file)

config = load_config("config.json")

TRANSITION_TIME = config["transition_duration"]
COLOR_POSE = config["color_pose"]
COLOR_TRANSITION = config["color_transition"]
COLOR_INNER_CIRCLE = config["color_inner_circle"]
COLOR_INNER_TEXT = config["color_inner_text"]
SPEED_DECREASE = 0.1

class YogaTimerApp:

    def __init__(self, master, plan):
        self.master = master
        master.title("Yoga Pose Timer")

        self.plan = plan
        self.current_pose_index = 0
        self.running = False

        # Style configuration
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 14))
        style.configure("TButton", font=("Helvetica", 12))
        style.configure("Big.TLabel", font=("Helvetica", 30))

        # Layout configuration
        control_frame = ttk.Frame(master)
        control_frame.pack(pady=10)

        self.day_selector = ttk.Combobox(
            control_frame, values=[f"Day {i}" for i in range(1, len(plan) + 1)], width=15)
        self.day_selector.current(0)  # Default to Day 1
        self.day_selector.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(
            control_frame, text="Start", command=self.start_timer)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(
            control_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(
            control_frame, text="Reset", command=self.reset_timer)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.pose_label = ttk.Label(master, text="", style="Big.TLabel")
        self.pose_label.pack(pady=20)

        self.canvas = tk.Canvas(master, width=700, height=600, bg='white')
        self.canvas.pack()
        self.circle = self.canvas.create_arc(
            55, 10, 645, 600, start=90, extent=360, fill=COLOR_POSE, outline=COLOR_POSE)
        self.inner_circle = self.canvas.create_oval(205, 160, 495, 450, fill=COLOR_INNER_CIRCLE, outline=COLOR_INNER_CIRCLE)
        self.timer_text = self.canvas.create_text(350, 305, text="", font=("Helvetica", 30), fill=COLOR_INNER_TEXT)
        
    def toggle_pause(self):
        self.running = not self.running
        if self.running:
            threading.Thread(target=self.countdown, daemon=True).start()
            self.pause_button.config(text="Pause")
        else:
            self.pause_button.config(text="Resume")

    def reset_timer(self):
        self.running = False
        self.current_pose_index = 0
        self.pose_label.config(text="")
        self.canvas.itemconfig(self.circle, start=90, extent=360, fill=COLOR_POSE, outline=COLOR_POSE)
        self.day_selector.current(0)  # Reset to Day 1
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(text="Pause", state=tk.DISABLED)

    def update_pose_label(self):
        day = self.day_selector.get()
        pose = self.plan[day]["Poses"][self.current_pose_index]
        self.pose_label.config(text=pose["Name"])

    def start_timer(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.countdown).start()

    def countdown(self):
        day = self.day_selector.get()
        poses = self.plan[day]["Poses"]

        # Transition before the first pose
        if self.current_pose_index == 0:
            next_pose_name = poses[self.current_pose_index]["Name"]
            self.transition_period(
                TRANSITION_TIME, f"Next pose: {next_pose_name}")

        while self.current_pose_index < len(poses) and self.running:
            pose = poses[self.current_pose_index]
            # Handle poses with sides
            if "Side" in pose:
                for side in ["Left", "Right"]:
                    if side == "Right":
                        self.transition_period(10, f"Transition to right side")
                    self.pose_label.config(text=f"{pose['Name']} ({side})")
                    # Split duration for each side
                    self.perform_pose(pose["Duration"] //
                                      2, pose["Name"] + " " + side)
                    self.speak(pose["Name"] + side)
            else:
                self.pose_label.config(text=pose["Name"])
                self.perform_pose(pose["Duration"], pose["Name"])
                self.speak(pose["Name"])

            # Transition to the next pose if applicable
            next_pose_index = self.current_pose_index + 1
            if next_pose_index < len(poses):
                next_pose_name = poses[next_pose_index]["Name"]
                self.transition_period(
                    TRANSITION_TIME, f"Next pose: {next_pose_name}")
            self.current_pose_index += 1

        if self.current_pose_index >= len(poses):
            self.pose_label.config(text="Session Complete!")
            self.running = False
            self.current_pose_index = 0  # Reset for next session

    def perform_pose(self, duration, pose_name):
        """Updated to modify the inner circle and timer text."""
        self.pose_label.config(text=pose_name)
        pose_duration = duration
        while duration > 0 and self.running:
            extent = (duration * 360) / pose_duration
            self.canvas.itemconfig(self.circle, start=90, extent=extent, fill=COLOR_POSE, outline=COLOR_POSE)
            # Update the timer text
            self.canvas.itemconfig(self.timer_text, text=self.seconds_to_minutes(duration))
            time.sleep(SPEED_DECREASE)
            duration -= SPEED_DECREASE
            self.master.update()

    def transition_period(self, duration, message):
        """Updated to modify the inner circle and timer text during transitions."""
        self.pose_label.config(text=message)
        total_transition_time = duration
        while duration > 0 and self.running:
            extent = (duration * 360) / total_transition_time
            self.canvas.itemconfig(self.circle, start=90, extent=extent, fill=COLOR_TRANSITION, outline=COLOR_TRANSITION)
            # Update the timer text
            self.canvas.itemconfig(self.timer_text, text=self.seconds_to_minutes(duration))
            time.sleep(SPEED_DECREASE)
            duration -= SPEED_DECREASE
            self.master.update()

    def speak(self, text):
        playsound('ding.mp3')

    def seconds_to_minutes(self, seconds):
        minutes = round(seconds // 60)
        remaining_seconds = round(seconds) % 60
        minutes_text = f"{minutes}" if minutes > 9 else f"0{minutes}"
        seconds_text = f"{remaining_seconds}" if remaining_seconds > 9 else f"0{remaining_seconds}"
        return f"{minutes_text}:{seconds_text}"

def load_plan(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    root = tk.Tk()
    # Ensure this path is correct
    yoga_plan = load_plan("yoga_plan_complete.json")
    app = YogaTimerApp(root, yoga_plan)
    with keep.presenting() as k:
        root.mainloop()


if __name__ == "__main__":
    main()