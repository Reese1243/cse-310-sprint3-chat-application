import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()


def broadcast_message(message):
    for key in sel.get_map().values():
        if key.data is None:
            continue
        key.data.outb += message


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            text = recv_data.decode("utf-8", errors="replace").rstrip("\n")
            message = f"[{data.addr[0]}:{data.addr[1]}] {text}\n".encode("utf-8")
            print(f"Broadcasting from {data.addr}: {text!r}")
            broadcast_message(message)
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            try:
                sent = sock.send(data.outb)  # Should be ready to write
            except (BrokenPipeError, ConnectionResetError):
                sent = 0
            if sent:
                data.outb = data.outb[sent:]
            elif data.outb:
                print(f"Closing connection to {data.addr} due to send failure")
                sel.unregister(sock)
                sock.close()


def main():
    if len(sys.argv) != 3:
        print("Usage: python multiconn-server.py <host> <port>")
        return

    host, port = sys.argv[1], int(sys.argv[2])
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind((host, port))
    lsock.listen()
    print(f"Listening on {(host, port)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == "__main__":
    main()

