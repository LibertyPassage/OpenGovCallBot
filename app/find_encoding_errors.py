import os

def find_invalid_utf8_files(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError as e:
                    print(f"UnicodeDecodeError in file: {file_path}")
                    print(f"Error details: {e}")

# Replace 'your_project_directory' with the path to your project directory
# Specify your project directory
project_directory = r'C:\Users\Priya Jaiswal\source\repos\OpenGovCallBot'

find_invalid_utf8_files(project_directory)
