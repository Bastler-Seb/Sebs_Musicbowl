from utils.input_utils import read_key
print("Testing read_key()...")
print("Press some keys (q to quit):")
while True:
    key = read_key()
    if key:
        print(f"Key: {key}")
        if key == 'q':
            break
