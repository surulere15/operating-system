#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description="Autonomous Big File Chunk Reader using Qmd")
    parser.add_argument("file_path", help="Absolute path to the large file")
    parser.add_argument("query", help="Search query to find relevant section")
    parser.add_argument("--buffer", type=int, default=20, help="Lines of context around match")
    parser.add_argument("--profile", default="openclaw", help="OpenClaw browser profile")
    
    args = parser.parse_args()
    
    if not os.path.isabs(args.file_path):
        print("Error: File path must be absolute.")
        sys.exit(1)
        
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} not found.")
        sys.exit(1)

    # 1. Use qmd hybrid query to find relevant lines
    # Note: Assuming qmd is in the PATH or we use the known node path
    env = os.environ.copy()
    env["PATH"] = "/usr/local/Cellar/node@22/22.22.0/bin:" + env.get("PATH", "")
    
    try:
        # Search within the specific file context
        search_cmd = ["qmd", "query", args.query, "--limit", "3"]
        result = subprocess.run(search_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Qmd search failed: {result.stderr}")
            # Fallback to grep -n
            print("Attempting fallback grep...")
            search_cmd = ["grep", "-ni", args.query, args.file_path]
            result = subprocess.run(search_cmd, capture_output=True, text=True)
            
        # 2. Extract line numbers from search results
        # Example qmd output: "filename.md:123: content..."
        lines_to_read = []
        for line in result.stdout.splitlines():
            if ":" in line:
                parts = line.split(":")
                try:
                    line_num = int(parts[1])
                    lines_to_read.append(line_num)
                except ValueError:
                    continue
                    
        if not lines_to_read:
            print("No matches found for query.")
            sys.exit(0)
            
        # 3. Read specific chunks
        with open(args.file_path, "r") as f:
            file_lines = f.readlines()
            
        print(f"--- Chunk Result for '{args.query}' in {os.path.basename(args.file_path)} ---")
        seen_ranges = set()
        
        for line_num in sorted(list(set(lines_to_read))):
            start = max(0, line_num - args.buffer - 1)
            end = min(len(file_lines), line_num + args.buffer)
            
            # Avoid overlapping prints
            if any(start < r[1] and end > r[0] for r in seen_ranges):
                continue
                
            seen_ranges.add((start, end))
            print(f"\n[Lines {start+1} - {end}]")
            for i in range(start, end):
                print(f"{i+1}: {file_lines[i].rstrip()}")
        
        print("\n--- End of Chunks ---")

    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
