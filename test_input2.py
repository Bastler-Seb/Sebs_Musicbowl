import sys
import tty
import termios
import select

fd = sys.stdin.fileno()
print(f"stdin fileno: {fd}")

try:
    old = termios.tcgetattr(fd)
    print(f"Old termios settings: {old}")
    
    tty.setraw(fd)
    sys.stdin.flush()
    
    print("Terminal set to raw mode. Press a key...")
    r, _, _ = select.select([sys.stdin], [], [], 5.0)
    if r:
        ch = sys.stdin.read(1)
        print(f"Read: {ch!r}")
    else:
        print("Timeout")
    
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
    print("Terminal restored")
