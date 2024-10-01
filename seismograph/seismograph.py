import tkinter as tk
import random
import cv2
from PIL import Image, ImageTk
import threading

class SeismographApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Seismograph")
        self.root.geometry("850x600")

        self.background_image = Image.open("bg.jpg").resize((850, 600), Image.LANCZOS)
        self.background_photo = ImageTk.PhotoImage(self.background_image)

        self.background_label = tk.Label(root, image=self.background_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.frame = tk.Frame(root, bg="#2C2C2C")
        self.frame.place(x=20, y=20, width=400, height=300)

        self.title_label = tk.Label(self.frame, text="Calculate Magnitude", font=("Arial", 16), fg="white", bg="#2C2C2C")
        self.title_label.pack(pady=10)

        self.hard_rock_var = tk.IntVar()
        self.firm_soil_var = tk.IntVar()
        self.soft_soil_var = tk.IntVar()

        tk.Checkbutton(self.frame, text="Hard Rock", variable=self.hard_rock_var, fg="white", bg="#2C2C2C", selectcolor="#2C2C2C").pack(anchor='w', padx=20)
        tk.Checkbutton(self.frame, text="Firm Soil", variable=self.firm_soil_var, fg="white", bg="#2C2C2C", selectcolor="#2C2C2C").pack(anchor='w', padx=20)
        tk.Checkbutton(self.frame, text="Soft Soil", variable=self.soft_soil_var, fg="white", bg="#2C2C2C", selectcolor="#2C2C2C").pack(anchor='w', padx=20)

        button_frame = tk.Frame(self.frame, bg="#2C2C2C")
        button_frame.pack(pady=10)

        self.generate_button = tk.Button(button_frame, text="Generate earthquake", command=self.generate_random_amplitude)
        self.generate_button.grid(row=0, column=0, padx=5)

        self.calculate_button = tk.Button(button_frame, text="Calculate Magnitude", command=self.calculate_with_random_amplitude)
        self.calculate_button.grid(row=0, column=1, padx=5)

        self.clear_button = tk.Button(button_frame, text="Clear", command=self.clear_values)
        self.clear_button.grid(row=0, column=2, padx=5)

        self.amplitude_label = tk.Label(self.frame, text="Highest Amplitude: N/A", fg="white", bg="#2C2C2C")
        self.amplitude_label.pack(pady=5)

        self.result_label = tk.Label(self.frame, text="", fg="white", bg="#2C2C2C")
        self.result_label.pack(pady=10)

        self.instruction_label = tk.Label(root, text="Instructions:\n1. Select soil type.\n2. Click 'Generate'.\n3. Click 'Calculate Magnitude'.\n4. Click 'Clear' to reset.", 
                                           fg="white", bg="#2C2C2C", justify='left')
        self.instruction_label.place(x=450, y=40)

        self.outcome_label = tk.Label(root, text="Possible Outcomes Based on Magnitude:\n"
                                                 "1.0 - 3.0: Minor tremor, no damage.\n"
                                                 "3.0 - 4.0: Light earthquake, slight damage.\n"
                                                 "4.0 - 5.0: Moderate earthquake, some damage.\n"
                                                 "5.0 - 6.0: Strong earthquake, moderate damage.\n"
                                                 "6.0 - 7.0: Major earthquake, serious damage.\n"
                                                 "7.0+: Great earthquake, severe damage.", 
                                      fg="white", bg="#2C2C2C", justify='left')
        self.outcome_label.place(x=450, y=180)

        self.video_frame = tk.Frame(root)
        self.video_frame.place(x=20, y=330, width=800, height=300)

        self.video_canvas = tk.Canvas(self.video_frame, width=800, height=300)
        self.video_canvas.pack()

        self.video_thread = None
        self.stop_video = False
        self.highest_amplitude = None

    def log10(self, x):
        if x <= 0:
            raise ValueError("log10 is undefined for non-positive values")

        n = 0
        while x < 1:
            x *= 10
            n -= 1
        while x >= 10:
            x /= 10
            n += 1

        log_approx = 0
        factor = 1
        for _ in range(10):  
            x = x ** 2
            factor /= 2
            if x >= 10:
                x /= 10
                log_approx += factor

        return log_approx + n

    def fuzzy_k(self, hard_rock_weight, firm_soil_weight, soft_soil_weight):
        k_hard_rock = 2.5
        k_firm_soil = 5.0
        k_soft_soil = 6.0
        return (hard_rock_weight * k_hard_rock +
                firm_soil_weight * k_firm_soil +
                soft_soil_weight * k_soft_soil)

    def calculate_epicenter_magnitude(self, amplitude, k):
        if amplitude <= 0:
            return "Invalid input (amplitude must be greater than 0)"

        magnitude = self.log10(amplitude) + k
        return magnitude

    def generate_random_amplitude(self):
        self.highest_amplitude = random.randint(1, 1000)
        self.amplitude_label.configure(text=f"Highest Amplitude: {self.highest_amplitude}")

        self.stop_video = True
        if self.video_thread is not None:
            self.video_thread.join()

        self.stop_video = False
        self.video_thread = threading.Thread(target=self.play_video, args=(self.highest_amplitude,))
        self.video_thread.start()

    def calculate_with_random_amplitude(self):
        if self.highest_amplitude is None:
            self.result_label.configure(text="Please generate first.")
            return

        hard_rock_weight = self.hard_rock_var.get()
        firm_soil_weight = self.firm_soil_var.get()
        soft_soil_weight = self.soft_soil_var.get()

        total_weight = hard_rock_weight + firm_soil_weight + soft_soil_weight

        if total_weight == 0:
            self.result_label.configure(text="Please select at least one ground type.")
            return

        hard_rock_weight /= total_weight
        firm_soil_weight /= total_weight
        soft_soil_weight /= total_weight

        k = self.fuzzy_k(hard_rock_weight, firm_soil_weight, soft_soil_weight)
        magnitude = self.calculate_epicenter_magnitude(self.highest_amplitude, k)
        self.result_label.configure(text=f"Magnitude: {magnitude:.2f}")

    def clear_values(self):
        self.highest_amplitude = None
        self.amplitude_label.configure(text="Highest Amplitude: N/A")
        self.result_label.configure(text="")
        
        self.stop_video = True
        if self.video_thread is not None:
            self.video_thread.join()
        
    def play_video(self, amplitude):
        if amplitude < 300:
            video_path = "low.mp4"
        elif amplitude < 700:
            video_path = "mid.mp4"
        else:
            video_path = "high.mp4"

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return

        while cap.isOpened() and not self.stop_video:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)

            frame = frame.resize((800, 300), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(frame)

            self.video_canvas.create_image(0, 0, image=self.photo, anchor="nw")
            self.video_canvas.update_idletasks()
            self.video_canvas.update()

            cv2.waitKey(25)

        cap.release()

if __name__ == "__main__":
    root = tk.Tk()
    app = SeismographApp(root)

    root.resizable(False, False)
    root.mainloop()
