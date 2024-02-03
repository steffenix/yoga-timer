import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from PIL import Image, ImageTk
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

    def __init__(self, master, plan, name_to_image):
        self.master = master
        master.title("Yoga Pose Timer")
        master.geometry("1600x850") 

        self.plan = plan
        self.name_to_image = name_to_image
        self.current_pose_index = 0
        self.running = False

        # Style configuration
        style = ttk.Style()
        style.configure("TLabel", font=("Bangla MN", 14))
        style.configure("TButton", font=("Bangla MN", 12), padding=[3, 8, 3, 3])
        style.configure("Big.TLabel", font=("Bangla MN", 30))

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
        self.pose_label.pack(pady=0)

        self.canvas = tk.Canvas(master, width=700, height=600)
        self.canvas.pack()
        self.canvas.place(x=0.0, y=150.0)
        self.circle = self.canvas.create_arc(
            55, 10, 645, 600, start=90, extent=360, fill=COLOR_POSE, outline='systemTransparent')
        self.inner_circle = self.canvas.create_oval(205, 160, 495, 450, fill=COLOR_INNER_CIRCLE, outline=COLOR_INNER_CIRCLE)
        self.timer_text = self.canvas.create_text(350, 305, text="", font=("Bangla MN", 30), fill=COLOR_INNER_TEXT)
         # Initial placeholder image
        self.pose_image = PhotoImage()
        self.image_canvas = tk.Canvas(master, width=900, height=600)
        self.image_canvas.place(x=700, y=150.0)
        self.image_item = self.image_canvas.create_image(450, 300, image=self.pose_image) 

    def toggle_pause(self):
        self.running = not self.running
        if self.running:
            self.pause_button.config(text="Pause")
            threading.Thread(target=self.countdown, daemon=True).start()
        else:
            self.pause_button.config(text="Resume")

    def reset_timer(self):
        self.running = False
        self.current_pose_index = 0
        self.pose_label.config(text="")
        self.canvas.itemconfig(self.circle, start=90, extent=360, fill=COLOR_POSE, outline='systemTransparent')
        self.day_selector.current(0)  # Reset to Day 1
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(text="Pause", state=tk.DISABLED)

    def update_pose_image(self, index):
        day = self.day_selector.get()
        pose = self.plan[day]["Poses"][index]
        if pose["Name"] not in self.name_to_image:
            self.pose_image = PhotoImage()
            return
        image = self.name_to_image[pose["Name"]]
        image_path = f"images/{image}"
        if os.path.exists(image_path):
            image = Image.open(image_path)
            max_width, max_height = 900, 600
            original_width, original_height = image.size
            ratio = min(max_width/original_width, max_height/original_height)
            new_size = (int(original_width * ratio), int(original_height * ratio))
            
            # Resize the image with the calculated ratio
            resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
            self.pose_image = ImageTk.PhotoImage(resized_image)

            self.image_canvas.itemconfig(self.image_item, image=self.pose_image)
            self.image_canvas.coords(self.image_item, max_width/2, max_height/2)
        else:
            self.pose_image = PhotoImage()
            # Optional: Update with a default image if pose image does not exist
            print(f"No image found for {pose['Name']}, at path: {image_path}")


    def start_timer(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.countdown).start()

    def countdown(self):
        day = self.day_selector.get()
        poses = self.plan[day]["Poses"]

        # Transition before the first pose
        if self.current_pose_index == 0:
            self.update_pose_image(self.current_pose_index)
            next_pose_name = poses[self.current_pose_index]["Name"]
            self.transition_period(self.current_pose_index)

        while self.current_pose_index < len(poses) and self.running:
            pose = poses[self.current_pose_index]
            # Handle poses with sides
            if "Side" in pose:
                for side in ["Left", "Right"]:
                    if side == "Right":
                        self.transition_period(10, f"Transition to right side")
                    self.pose_label.config(text=f"{pose['Name']} ({side})")
                    # Split duration for each side
                    self.perform_pose(pose["Duration"], pose["Name"] + " " + side)
                    self.speak(pose["Name"] + side)
            else:
                self.pose_label.config(text=pose["Name"])
                self.perform_pose(pose["Duration"], pose["Name"])
                self.speak(pose["Name"])

            # Transition to the next pose if applicable
            next_pose_index = self.current_pose_index + 1
            if next_pose_index < len(poses):
                self.update_pose_image(next_pose_index)
                self.transition_period(next_pose_index)
            self.current_pose_index += 1

        if self.current_pose_index >= len(poses):
            self.pose_label.config(text="Session Complete!")
            self.running = False
            self.current_pose_index = 0  # Reset for next session

    def perform_pose(self, duration, pose_name):
        """Updated to modify the inner circle and timer text."""
        self.update_circle(duration, pose_name, COLOR_POSE)

    def transition_period(self, index):
        """Updated to modify the inner circle and timer text during transitions."""
        day = self.day_selector.get()
        pose = self.plan[day]["Poses"][index]
        next_pose_name = pose["Name"]
        duration = pose["Transition"] if "Transition" in pose.keys() else TRANSITION_TIME
        message = f"Transition to {next_pose_name}"
        self.update_circle(duration, message, COLOR_TRANSITION)

    def update_circle(self, duration, message, color):
        self.pose_label.config(text=message)
        total_time = duration
        while duration > 0 and self.running:
            extent = (duration * 360) / total_time
            self.canvas.itemconfig(self.circle, start=90, extent=extent, fill=color)
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

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    root = tk.Tk()
    # Ensure this load_json is correct
    yoga_plan = load_json("yoga_plan_complete.json")
    name_to_image = load_json("names_to_image.json")
    app = YogaTimerApp(root, yoga_plan, name_to_image)
    with keep.presenting() as k:
        root.mainloop()


if __name__ == "__main__":
    main()