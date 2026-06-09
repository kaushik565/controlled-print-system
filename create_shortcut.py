import os
import sys

def create_shortcut():
    try:
        import win32com.client
    except ImportError:
        print("Installing pywin32...")
        os.system("pip install pywin32")
        import win32com.client

    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    path = os.path.join(desktop, "CDPS.lnk")
    
    # We want it to run pythonw.exe so it doesn't open a terminal window
    target = sys.executable.replace("python.exe", "pythonw.exe")
    cwd = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(cwd, "app.py")
    
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.Arguments = f'"{app_path}"'
    shortcut.WorkingDirectory = cwd
    
    # Optional: use a standard system icon or leave default python icon
    shortcut.IconLocation = os.path.join(cwd, "app_icon.ico")
    
    shortcut.save()
    print("Shortcut successfully created at:", path)

if __name__ == "__main__":
    create_shortcut()
