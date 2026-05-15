import os
import sys
import time

def check_env_var(var_name):
    val = os.getenv(var_name)
    if val and "placeholder" not in val.lower() and "your_" not in val.lower():
        return "✅ READY"
    return "❌ MISSING"

def main():
    print("=== SOVEREIGN EMPIRE DASHBOARD v1.0 ===")
    print(f"Time: {time.ctime()}")
    print("-" * 40)
    
    # 1. Infrastructure Status
    print("[INFRASTRUCTURE]")
    # limited resource check for dashboard display
    try:
        import psutil
        print(f"CPU Usage: {psutil.cpu_percent()}%")
        print(f"RAM Usage: {psutil.virtual_memory().percent}%")
    except ImportError:
        print("System Stats: (psutil not installed)")

    # 2. Key Inventory
    print("\n[CRYPTOGRAPHIC ASSETS]")
    print(f"Quantum RPC:      {check_env_var('RPC_URL')}")
    print(f"Execution Key:    {check_env_var('PRIVATE_KEY')}")
    print(f"Twitter Voice:    {check_env_var('TWITTER_API_KEY')}")
    print(f"Google Intel:     {check_env_var('GOOGLE_API_KEY')}")

    # 3. Fleet Status
    print("\n[FLEET STATUS]")
    if os.path.exists("docker-compose.yml"):
        print("Docker Config:    ✅ FOUND")
    else:
        print("Docker Config:    ❌ MISSING")
        
    print("-" * 40)
    print("STATUS: WAITING FOR KEYS.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
