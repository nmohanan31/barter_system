from image_aiagent import describe_image, load_api_key
import tkinter as tk
from tkinter import filedialog


if __name__ == "__main__":
    try:
        
               # Create and hide the main tkinter window
        root = tk.Tk()
        root.withdraw()
        
        # Open file chooser dialog
        image_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if image_path:  # Only proceed if a file was selected
            description = describe_image(image_path)
        else:
            print("No file selected")
            
    except Exception as e:
        print(f"Error: {str(e)}")