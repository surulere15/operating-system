import os

def read_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        return f'Error reading file: {e}'

def main():
    base_path = '/Users/sam/.openclaw/memory/2026_INTEL/'
    files = ['DEAI_2026_STATE.md', 'REGULATORY_WARFARE_2026.md']
    
    combined_data = ''
    for file in files:
        filepath = os.path.join(base_path, file)
        data = read_file(filepath)
        combined_data += f'---Contents of {file}---\n{data}\n\n'
        
    print(combined_data)

if __name__ == "__main__":
    main()