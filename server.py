import argparse
import threading
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket

from constCS import BACKLOG, BUFFER_SIZE, HOST, PORT


cars = []
cars_lock = threading.Lock()


def add_car(brand, name):
    with cars_lock:
        for car in cars:
            if car["brand"] == brand and car["name"] == name:
                return f"{brand} {name} already registered"

        cars.append({"brand": brand, "name": name})
        return f"{brand} {name} registered."


def list_cars():
    with cars_lock:
        if not cars:
            return "No models registered."

        result = "Models:\n"
        for i, car in enumerate(cars):
            result += f"{i + 1} - {car['brand']} {car['name']}\n"
        return result.strip()


def delete_car(index):
    try:
        position = int(index) - 1
    except ValueError:
        return "Invalid index."

    with cars_lock:
        if 0 <= position < len(cars):
            removed = cars.pop(position)
            return f"{removed['brand']} {removed['name']} deleted."
        return "Invalid model number."


def process_request(message):
    parts = message.strip().split(" ", 2)
    command = parts[0].upper() if parts else ""

    if command == "LIST":
        return list_cars()
    if command == "ADD" and len(parts) == 3:
        return add_car(parts[1], parts[2])
    if command == "DELETE" and len(parts) == 2:
        return delete_car(parts[1])
    return "Invalid command. Use: LIST, ADD <brand> <name>, DELETE <number>, QUIT"


def receive_request(conn):
    data = conn.recv(BUFFER_SIZE)
    if not data:
        return ""
    return data.decode().strip()


def send_response(conn, message):
    response = process_request(message)
    conn.sendall(response.encode())


def handle_threaded_request(conn, addr, message):
    try:
        send_response(conn, message)
    finally:
        conn.close()


def serve_threaded(server_socket):
    while True:
        conn, addr = server_socket.accept()
        message = receive_request(conn)
        if not message:
            conn.close()
            continue

        worker = threading.Thread(
            target=handle_threaded_request,
            args=(conn, addr, message),
        )
        worker.daemon = True
        worker.start()


def parse_args():
    parser = argparse.ArgumentParser(description="Car Service API server")
    parser.add_argument("--host", default=HOST, help="host/interface to bind")
    parser.add_argument("--port", type=int, default=PORT, help="TCP port to bind")
    return parser.parse_args()


def main():
    args = parse_args()

    with socket(AF_INET, SOCK_STREAM) as server_socket:
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen(BACKLOG)

        print(f"Server listening on {args.host}:{args.port} in multithread mode")

        try:
            serve_threaded(server_socket)
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == "__main__":
    main()
