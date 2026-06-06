import socket
import threading
import sys

def receive_loop(sock):
    while True:
        try:
            data = sock.recv(1024)
        except ConnectionResetError:
            print("\nServer closed the connection.")
            break
        if not data:
            print("\nDisconnected from server.")
            break
        print("\r" + data.decode("utf-8") + "\n> ", end="", flush=True)

def main():
    if len(sys.argv) != 3:
        print("Usage: python multiconn-client.py <host> <port>")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    username = input("Enter your username: ").strip()
    if not username:
        username = "Anonymous"

    receiver = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
    receiver.start()

    print(f"Connected as {username}. Type messages and press Enter.")
    sock.sendall(f"{username} has joined the chat.".encode("utf-8"))

    while True:
        try:
            message = input("> ")
        except EOFError:
            break
        if not message:
            continue
        if message.lower() in {"/quit", "/exit"}:
            break
        full_message = f"{username}: {message}"
        sock.sendall(full_message.encode("utf-8"))

    try:
        sock.sendall(f"{username} has left the chat.".encode("utf-8"))
    except Exception:
        pass
    sock.close()

if __name__ == "__main__":
    main()