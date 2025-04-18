import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pyautogui
import pygetwindow
from PIL import ImageTk, Image
import threading
import time

from predictions import predict

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Options: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue" (default), "green", "dark-blue"

# Global variables
project_folder = os.path.dirname(os.path.abspath(__file__))
folder_path = project_folder + '/images/'
filename = ""

class LoadingAnimation:
    def __init__(self, master, width=30, height=30):
        self.master = master
        self.width = width
        self.height = height
        # Fix the background color issue by using a string color
        if ctk.get_appearance_mode() == "Dark":
            bg_color = "#2b2b2b"  # Dark mode background
        else:
            bg_color = "#ebebeb"  # Light mode background
            
        self.canvas = ctk.CTkCanvas(master, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.angle = 0
        self.is_running = False
        self.counter = 0
        
    def start(self):
        self.is_running = True
        # Use grid instead of pack to be consistent with the parent's geometry manager
        self.canvas.grid(row=4, column=0, pady=10)
        self.update()
        
    def update(self):
        if not self.is_running:
            return
        
        self.canvas.delete("all")
        
        # Create loading spinner effect
        self.angle = (self.angle + 10) % 360
        arc_length = 100  # Length of the arc in degrees
        start_angle = self.angle
        
        # Draw arc
        self.canvas.create_arc(5, 5, self.width-5, self.height-5, 
                              start=start_angle, extent=arc_length, 
                              outline="#1f538d", width=3, style="arc")
        
        self.counter += 1
        self.master.after(50, self.update)
        
    def stop(self):
        self.is_running = False
        # Use grid_remove instead of pack_forget
        self.canvas.grid_remove()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Bone Fracture Detection")
        self.geometry("800x700")
        self.minsize(700, 650)
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        # Create header frame
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#3a7ebf", "#1f538d"), height=70)
        self.header_frame.grid(row=0, column=0, sticky="nsew")
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        
        # Create logo and title in header
        self.logo_label = ctk.CTkLabel(
            self.header_frame, 
            text="Bone Fracture Detection", 
            font=ctk.CTkFont(family="Roboto", size=28, weight="bold"),
            text_color="white"
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        # Info button
        info_image = ctk.CTkImage(Image.open(folder_path + "info.png"), size=(25, 25))
        self.info_button = ctk.CTkButton(
            self.header_frame, 
            text="", 
            image=info_image,
            fg_color="transparent", 
            width=40, 
            height=40,
            hover_color=("#4a8ece", "#2f639d"),
            command=self.open_image_window
        )
        self.info_button.grid(row=0, column=1, padx=20, pady=15, sticky="e")
        
        # Create main content area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=0)
        
        # Welcome message
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text="Upload an X-ray image for fracture detection",
            font=ctk.CTkFont(family="Roboto", size=16)
        )
        self.info_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Upload button with icon
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        self.upload_btn = ctk.CTkButton(
            self.button_frame, 
            text="Upload X-ray Image", 
            command=self.upload_image,
            font=ctk.CTkFont(family="Roboto", size=14),
            height=40,
            corner_radius=8
        )
        self.upload_btn.pack(side="left", padx=5)
        
        self.predict_btn = ctk.CTkButton(
            self.button_frame, 
            text="Analyze", 
            command=self.predict_gui,
            font=ctk.CTkFont(family="Roboto", size=14),
            fg_color="#28a745",
            hover_color="#218838",
            height=40,
            corner_radius=8
        )
        self.predict_btn.pack(side="left", padx=5)
        
        # Image display area
        self.image_frame = ctk.CTkFrame(self.main_frame, fg_color=("#e0e0e0", "#333333"))
        self.image_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)
        
        # Initialize with placeholder image
        img = Image.open(folder_path + "Question_Mark.jpg")
        self.display_img(img)
        
        # Results area
        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(1, weight=1)
        
        # Bone type result
        self.type_label = ctk.CTkLabel(
            self.results_frame,
            text="Type: ",
            font=ctk.CTkFont(family="Roboto", size=18),
            anchor="center"
        )
        self.type_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Fracture result
        self.result_label = ctk.CTkLabel(
            self.results_frame,
            text="Result: ",
            font=ctk.CTkFont(family="Roboto", size=18),
            anchor="center"
        )
        self.result_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Save button
        self.save_btn = ctk.CTkButton(
            self.results_frame, 
            text="Save Results", 
            command=self.save_result,
            font=ctk.CTkFont(family="Roboto", size=14),
            fg_color="#6c757d",
            hover_color="#5a6268",
            height=35,
            corner_radius=8
        )
        self.save_btn.grid(row=1, column=0, columnspan=2, padx=20, pady=10)
        self.save_btn.grid_remove()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.results_frame,
            text="",
            font=ctk.CTkFont(family="Roboto", size=14)
        )
        self.status_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        
        # Create loading animation
        self.loading_animation = LoadingAnimation(self.main_frame)

    def display_img(self, img, max_height=300, max_width=500):
        # Calculate new size while maintaining aspect ratio
        img_width, img_height = img.size
        ratio = min(max_width/img_width, max_height/img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        # Resize the image
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to CTkImage to avoid HighDPI warning
        ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(new_width, new_height))
        
        # Clear existing image if any
        for widget in self.image_frame.winfo_children():
            widget.destroy()
        
        # Create and place the new image label
        self.img_label = ctk.CTkLabel(self.image_frame, text="", image=ctk_img)
        self.img_label.image = ctk_img  # Keep a reference
        self.img_label.grid(row=0, column=0, padx=10, pady=10)

    def upload_image(self):
        global filename
        
        f_types = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp"),
            ("All Files", "*.*")
        ]
        
        new_filename = filedialog.askopenfilename(
            filetypes=f_types, 
            initialdir=project_folder+'/test/Wrist/',
            title="Select X-ray Image"
        )
        
        if not new_filename:  # User canceled the dialog
            return
            
        filename = new_filename
        
        # Reset results
        self.type_label.configure(text="Type: ")
        self.result_label.configure(text="Result: ")
        self.status_label.configure(text="")
        self.save_btn.grid_remove()
        
        try:
            img = Image.open(filename)
            self.display_img(img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def predict_gui(self):
        if not filename:
            messagebox.showwarning("Warning", "Please upload an X-ray image first")
            return
            
        # Show loading animation
        self.loading_animation.start()
        self.status_label.configure(text="Analyzing image, please wait...")
        
        # Run prediction in a separate thread to keep UI responsive
        threading.Thread(target=self._run_prediction, daemon=True).start()
    
    def _run_prediction(self):
        try:
            # First predict bone type
            bone_type_result = predict(filename, "Parts")
            
            # Then predict fracture status
            result = predict(filename, bone_type_result)
            
            # Update UI in the main thread
            self.after(0, lambda: self._update_ui_with_results(bone_type_result, result))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
    
    def _update_ui_with_results(self, bone_type, result):
        # Stop loading animation
        self.loading_animation.stop()
        
        # Update bone type
        self.type_label.configure(
            text=f"Type: {bone_type}",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold")
        )
        
        # Update result with color coding
        if result == 'fractured':
            self.result_label.configure(
                text="Result: Fractured",
                text_color="#dc3545",
                font=ctk.CTkFont(family="Roboto", size=18, weight="bold")
            )
        else:
            self.result_label.configure(
                text="Result: Normal",
                text_color="#28a745",
                font=ctk.CTkFont(family="Roboto", size=18, weight="bold")
            )
        
        # Show save button
        self.save_btn.grid()
        self.status_label.configure(text="Analysis complete")
    
    def _show_error(self, error_message):
        self.loading_animation.stop()
        self.status_label.configure(text=f"Error: {error_message}")
        messagebox.showerror("Error", f"An error occurred during analysis: {error_message}")

    def save_result(self):
        default_filename = f"bone_{time.strftime('%Y%m%d_%H%M%S')}.png"
        
        save_path = filedialog.asksaveasfilename(
            parent=self,
            initialdir=project_folder + '/PredictResults/',
            initialfile=default_filename,
            title='Save Screenshot',
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if not save_path:  # User canceled
            return
            
        try:
            # Take screenshot of the window
            window = pygetwindow.getWindowsWithTitle('Bone Fracture Detection')[0]
            left, top = window.topleft
            right, bottom = window.bottomright
            
            # Take screenshot with slight delay to ensure UI is updated
            self.status_label.configure(text="Saving results...")
            self.update_idletasks()
            time.sleep(0.2)  # Small delay
            
            pyautogui.screenshot(save_path)
            im = Image.open(save_path)
            im = im.crop((left + 10, top + 35, right - 10, bottom - 10))
            im.save(save_path)
            
            self.status_label.configure(text=f"Results saved to: {os.path.basename(save_path)}")
        except Exception as e:
            self.status_label.configure(text="Error saving results")
            messagebox.showerror("Error", f"Failed to save results: {str(e)}")

    def open_image_window(self):
        try:
            im = Image.open(folder_path + "rules.jpeg")
            im = im.resize((700, 700))
            im.show()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open information image: {str(e)}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
