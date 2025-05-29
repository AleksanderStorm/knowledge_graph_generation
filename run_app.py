# run_app.py (or your_package_name/cli.py)
import subprocess
import sys

def main():
    """
    Entry point for running the Streamlit app.
    """
    # Adjust 'App.py' to the actual path of your Streamlit app file
    # If App.py is in a subdirectory (e.g., 'src/App.py'), use that path.
    streamlit_app_path = "App.py" 
    
    # You might want to handle arguments passed to your script if needed
    # For now, we'll just pass 'run' and the app path to streamlit
    
    try:
        subprocess.run(["streamlit", "run", streamlit_app_path], check=True, text=True)
    except FileNotFoundError:
        print("Error: 'streamlit' command not found. Is Streamlit installed in your environment?", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}", file=sys.stderr)
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()