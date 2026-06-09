import os
import sys
import customtkinter
import subprocess

def build():
    print("Starting build process...")
    
    # Get the directory of the customtkinter package
    ctk_path = os.path.dirname(customtkinter.__file__)
    
    # Format the data addition string (PathToSource;PathToDestination)
    # Note: On Windows it's ';', on Linux/Mac it's ':'
    add_data_str = f"{ctk_path};customtkinter/"
    add_data_logo = "molbio_logo.png;."
    add_data_logo_white = "molbio_logo_white.png;."
    add_data_bg = "dna_bg.png;."
    
    app_name = "CDPS"
    script_path = "app.py"
    icon_path = "app_icon.ico"
    
    # Construct PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",          # Create a directory rather than a single massive .exe (faster startup)
        "--windowed",        # Do not open a console window
        "--name", app_name,
        "--icon", icon_path,
        "--add-data", add_data_str,
        "--add-data", add_data_logo,
        "--add-data", add_data_logo_white,
        "--add-data", add_data_bg,
        script_path
    ]
    
    print("Running command:", " ".join(cmd))
    
    # Execute PyInstaller
    subprocess.run(cmd, check=True)
    
    print("\\nBuild Complete! The application is located in the 'dist' folder.")

if __name__ == "__main__":
    build()
