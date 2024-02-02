import tkinter as tk
from tkinter import ttk
import time
import threading
import json
from playsound import playsound

TRANSITION_TIME = 15
class YogaTimerApp:
    def __init__(self, master, plan):
        self.master = master
        master.title("Yoga Pose Timer")

        self.plan = plan
        self.current_pose_index = 0
        self.running = False

        self.day_selector = ttk.Combobox(master, values=[f"Day {i}" for i in range(1, len(plan) + 1)])
        self.day_selector.current(0)  # Default to Day 1
        self.day_selector.pack()

        self.pose_label = ttk.Label(master, text="", font=("Helvetica", 30))
        self.pose_label.pack()

        self.canvas = tk.Canvas(master, width=700, height=600, bg='white')
        self.canvas.pack()
        self.circle = self.canvas.create_arc(10, 10, 690, 590, start=90, extent=360, fill="red")

        self.start_button = ttk.Button(master, text="Start", command=self.start_timer)
        self.start_button.pack()

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
            self.transition_period(TRANSITION_TIME, f"Next pose: {next_pose_name}")

        while self.current_pose_index < len(poses) and self.running:
            pose = poses[self.current_pose_index]
            # Handle poses with sides
            if "Side" in pose:
                for side in ["Left", "Right"]:
                    if side == "Right":
                        self.transition_period(10, f"Transition to right side")
                    self.pose_label.config(text=f"{pose['Name']} ({side})")
                    self.perform_pose(pose["Duration"] // 2, pose["Name"] + " " + side)  # Split duration for each side
                    self.speak(pose["Name"] + side)
            else:
                self.pose_label.config(text=pose["Name"])
                self.perform_pose(pose["Duration"], pose["Name"])
                self.speak(pose["Name"])

            # Transition to the next pose if applicable
            next_pose_index = self.current_pose_index + 1
            if next_pose_index < len(poses):
                next_pose_name = poses[next_pose_index]["Name"]
                self.transition_period(TRANSITION_TIME, f"Next pose: {next_pose_name}")
            self.current_pose_index += 1

        if self.current_pose_index >= len(poses):
            self.pose_label.config(text="Session Complete!")
            self.running = False
            self.current_pose_index = 0  # Reset for next session

    def perform_pose(self, duration, pose_name):
        """Performs the countdown for a pose's duration with a red circle."""
        self.pose_label.config(text=pose_name)
        pose_duration = duration
        while duration > 0 and self.running:
            extent = (duration * 360) / pose_duration
            self.canvas.itemconfig(self.circle, start=90, extent=extent, fill="red")
            time.sleep(1)
            duration -= 1
            self.master.update()

    def transition_period(self, duration, message):
        """Handles the transition period between poses with a blue circle."""
        self.pose_label.config(text=message)
        total_transition_time = duration  # Total time allocated for transitions
        while duration > 0 and self.running:
            extent = (duration * 360) / total_transition_time
            self.canvas.itemconfig(self.circle, start=90, extent=extent, fill="blue")
            time.sleep(1)
            duration -= 1
            self.master.update()

    def speak(self, text):
        playsound('ding.mp3')

def load_plan(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    root = tk.Tk()
    yoga_plan = load_plan("yoga_plan_complete.json")  # Ensure this path is correct
    app = YogaTimerApp(root, yoga_plan)
    root.mainloop()

if __name__ == "__main__":
    main()
