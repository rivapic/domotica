import time
import sys
import tinytuya

# Get IP from command line argument
if len(sys.argv) < 2:
    print("Uso: python3 test.py <IP>")
    sys.exit(1)

device_ip = sys.argv[1]

# Connect to Device
while True:
    try:
        d = tinytuya.Device(
            dev_id='bf8a206c2ef8c4accf2sxf',
            address=device_ip,      # Use IP from command line argument
            local_key="[[lv('SpgJmfW|V|",
            version=3.4)
        
        # Get Status
        while True:
            data = d.status()
            print('Device Status: %r' % data)
            time.sleep(1)  # Poll every 10 seconds, adjust as needed
    except RuntimeError as e:
        print(f"Error connecting to device: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(1)