import argparse
import random
import threading
import time
from socket import AF_INET, SOCK_STREAM, socket

from constCS import BUFFER_SIZE, DEFAULT_REQUESTS, HOST, PORT


CARS = {
    "Toyota": ("Corolla", "Hilux", "Yaris"),
    "Honda": ("Civic", "Fit", "HR-V"),
    "Ford": ("Focus", "Fiesta", "Ranger"),
    "Chevrolet": ("Onix", "Cruze", "S10"),
    "Volkswagen": ("Golf", "Gol", "Polo"),
    "Fiat": ("Argo", "Mobi", "Toro"),
    "Hyundai": ("HB20", "Creta", "Tucson"),
    "Renault": ("Sandero", "Logan", "Duster"),
}


def send_request(command, host, port):
    start = time.perf_counter()

    with socket(AF_INET, SOCK_STREAM) as client_socket:
        client_socket.settimeout(10)
        client_socket.connect((host, port))
        client_socket.sendall(command.encode())

        chunks = []
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            chunks.append(data)

    elapsed = time.perf_counter() - start
    return command, b"".join(chunks).decode(), elapsed


def safe_send_request(command, host, port):
    try:
        return send_request(command, host, port)
    except OSError as exc:
        return command, f"ERROR: {exc}", 0.0


def generate_requests(total, seed):
    rng = random.Random(seed)
    requests = []

    for i in range(total):
        operation = rng.random()

        if operation < 0.7:
            brand = rng.choice(list(CARS.keys()))
            model = rng.choice(CARS[brand])
            requests.append(f"ADD {brand} {model}")
        elif operation < 0.9:
            requests.append("LIST")
        else:
            requests.append(f"DELETE {rng.randint(1, max(1, i + 1))}")

    return requests


def run_threaded(requests, host, port):
    results = [None] * len(requests)

    def worker(index, request):
        results[index] = safe_send_request(request, host, port)

    threads = []
    start = time.perf_counter()

    for index, request in enumerate(requests):
        thread = threading.Thread(target=worker, args=(index, request))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results, time.perf_counter() - start


def print_summary(total_time, results):
    errors = sum(1 for result in results if result[1].startswith("ERROR:"))
    total = len(results)
    average = total_time / total if total else 0.0

    print("Mode: multithread")
    print(f"Requests: {total}")
    print(f"Errors: {errors}")
    print(f"Total time: {total_time:.6f} seconds")
    print(f"Average time: {average:.6f} seconds/request")
    print(f"TOTAL_SECONDS={total_time:.6f}")


def run_auto(args):
    requests = generate_requests(args.requests, args.seed)
    results, total_time = run_threaded(requests, args.host, args.port)

    print_summary(total_time, results)
    return 1 if any(result[1].startswith("ERROR:") for result in results) else 0


def run_interactive(args):
    print("Car Service API Client")
    print("Commands: LIST, ADD <brand> <name>, DELETE <number>, QUIT")
    print("Client mode: multithread\n")

    while True:
        command = input("Enter command: ").strip()
        if not command:
            continue
        if command.upper() == "QUIT":
            break

        start = time.perf_counter()

        result_box = {}

        def worker():
            result_box["result"] = safe_send_request(command, args.host, args.port)

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        result = result_box["result"]

        print(result[1])
        print(f"Total time spent: {time.perf_counter() - start:.6f} seconds")

    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Car Service API client")
    parser.add_argument("--host", default=HOST, help="server host")
    parser.add_argument("--port", type=int, default=PORT, help="server TCP port")
    parser.add_argument("--auto", action="store_true", help="generate requests automatically")
    parser.add_argument("--requests", type=int, default=DEFAULT_REQUESTS, help="number of automatic requests")
    parser.add_argument("--seed", type=int, default=42, help="random seed for automatic requests")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.auto:
        return run_auto(args)
    return run_interactive(args)


if __name__ == "__main__":
    raise SystemExit(main())
