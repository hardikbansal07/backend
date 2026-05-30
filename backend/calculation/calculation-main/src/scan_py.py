import os

def scan_dir(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.py') or file.endswith('.txt') or file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'PyJHora-main' in content or 'seplm48' in content:
                            print(f"FOUND IN: {file_path}")
                            # Print lines containing it
                            lines = content.splitlines()
                            for i, line in enumerate(lines):
                                if 'PyJHora-main' in line or 'seplm48' in line:
                                    print(f"  Line {i+1}: {line}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    scan_dir("c:\\Users\\acer\\backend folder")
