import argparse
import socket
import threading
from typing import TypedDict


class Connection(TypedDict):
    sock: socket.socket
    addr: tuple[str, int]
    username: str | None


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

    conns: list[Connection] = []

    while True:
        conn, addr = s.accept()

        # 开一个线程处理客户端请求
        def handle_client(conn: socket.socket, addr: tuple[str, int]):
            conns.append(
                {
                    "sock": conn,
                    "addr": addr,
                    "username": None,
                }
            )
            print("有用户连接上了", addr, "当前连接数", len(conns))
            while True:
                """
                客户端发过来的消息格式：
                0x xx    ...
                   ──    ───
                   event data
                要给客户端的消息格式：
                0x ...      005000 xx    ...
                   ───      ────── ──    ───
                   username NUL    event data
                """
                try:
                    data: bytes = conn.recv(1024)
                except ConnectionResetError:
                    break
                print("收到来自", addr, "消息", data)
                if not data:
                    break
                # 检测消息格式
                if len(data.hex()) < 2:
                    continue
                # 如果event是00, 则表示客户端请求用户名
                if data.hex()[0:2] == "00":
                    # data是要设置的用户名
                    username = data[2:].decode()
                    # 设置用户名
                    for c in conns:
                        if c["addr"] == addr:
                            c["username"] = username
                    print("用户", addr, "设置用户名为", username)
                # 检测是否已经设置了用户名
                for c in conns:
                    if c["addr"] == addr and c["username"] is not None:
                        # 把消息广播给所有连接的客户端
                        for c2 in conns:
                            c2["sock"].send(
                                bytes(
                                    f"{c['username']}\0{data}",
                                    encoding="utf-8",
                                )
                            )
            print("用户断开连接", addr, "当前连接数", len(conns) - 1)
            conn.close()
            for c in conns:
                if c["addr"] == addr:
                    conns.remove(c)
                    break

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    main()
