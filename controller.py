import socket
import threading
stop_flag = threading.Event()

def handle_client(ip_addr, port):

    dead_flag = False

    addr = (ip_addr, port)

    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn.settimeout(10)

    local_address, local_port = conn.getsockname()

    conn.bind((local_address, local_port))

    print(f'Connected to client {addr[0]}:{addr[1]}\n')

    response = f'HTTP/1.1 200 OK\nLOCATION: http://{local_address}:{local_port}\n\n'
    conn.sendto(response.encode(), addr)

    print(f'Sent response to {addr[0]}:{addr[1]}\n')

    try:
        while True:
            if stop_flag.is_set():
                raise socket.timeout

            data, _ = conn.recvfrom(1024)

            keep_alive = f'HTTP/1.1 200 OK\nNTS:ssdp:alive\nLOCATION: http://{local_address}:{local_port}\n\n'
            conn.sendto(keep_alive.encode(), addr)

            if not data:
                break

            print('\n' + data.decode())

            for line in data.decode().split('\n'):
                if 'NTS' in line:
                    if line.split(':')[2] == 'byebye\r':
                        dead_flag = True
                        raise socket.error

    except socket.timeout:
        if stop_flag.is_set() or dead_flag is True:
            pass
        else:
            print(f'Connection to client {addr[0]}:{addr[1]} timed out\n')

    except socket.error:
        print(f'Disconnect request from client {addr[0]}:{addr[1]}\n')

    finally:
        conn.close()
        print(f'Disconnected from client {addr[0]}:{addr[1]}\n')

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    addr = '224.0.0.251'

    s.bind((addr, 1900))

    mreq = socket.inet_aton(addr) + socket.inet_aton('0.0.0.0')
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Server listening on {addr}:1900...\n")

    while True:
        try:
            data, addr = s.recvfrom(1024)
            
            for line in data.decode().split('\n'):
                if 'ST' in line:
                    if line.split(':')[2] == 'brocker':
                        print(f'Received join request from {addr[0]}:{addr[1]}\n')
                        t = threading.Thread(target=handle_client, args=(addr[0], addr[1]))
                        t.start()
                        
        except KeyboardInterrupt:
            stop_flag.set()
            s.close()
            exit()

start_server()