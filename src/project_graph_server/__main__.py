import argparse
import socket
import threading


def main():
    parser = argparse.ArgumentParser(description="Project Graph Server")
    parser.add_argument("--port", type=int, default=0, help="Port to listen on")
    parser.add_argument(
        "--max-connections",
        type=int,
        default=10,
        help="Maximum number of connections to allow",
    )
    args = parser.parse_args()

    s = socket.socket()
    s.bind(("0.0.0.0", args.port))

    s.listen(args.max_connections)
    print(f"Server listening on port {s.getsockname()[1]}")

    conns: list[socket.socket] = []

    while True:
        conn, addr = s.accept()

        # 开一个线程处理客户端请求
        def handle_client(conn: socket.socket, addr: tuple[str, int]):
            conns.append(conn)
            print("有用户连接上了", addr, "当前连接数", len(conns))
            while True:
                data = conn.recv(1024)
                print("收到来自", addr, "消息", data)
                if not data:
                    break
                for c in conns:
                    if c == conn:
                        continue
                    c.send(data)
            print("用户断开连接", addr, "当前连接数", len(conns) - 1)
            conn.close()
            conns.remove(conn)

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    main()
