import socket
import time

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    s.settimeout(2)

    attempts = 0
    dead = False

    try:

        while attempts < 5:
            try:
                join_request = 'M-SEARCH * HTTP/1.1\r\nHOST:224.0.1.20:1900\r\nMAN:"ssdp:discover"\r\nST:urn:brocker:service\r\n\r\n'
                s.sendto(join_request.encode(), ('224.0.0.251', 1900))
                data, addr = s.recvfrom(1024)
                attempts = 0
                break
            except socket.timeout:
                attempts += 1
                print(f'Could not find server, attempt {attempts}/5\n')

        for line in data.decode().split('\n'):
            if 'LOCATION' in line:
                ip_addr, port = line.split(' ')[1].split('/')[2].split(':')
                print(f'Server IP address: {ip_addr}')
                print(f'Server port: {port}\n')

        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while attempts < 5:

            keep_alive = 'NOTIFY * HTTP/1.1\r\nHOST:224.0.1.20:1900\r\nNTS:ssdp:alive\r\nUSN:mydevice:service\r\nCACHE-CONTROL:max-age=1800\r\nLOCATION:http://192.168.1.101:8080/sensor.xml\r\nNT:mydevice:service\r\n\r\n'

            conn.sendto(keep_alive.encode(), addr)
            print(f'Sent keep alive message to server ip address {addr[0]} and server port {addr[1]}\n')

            try:
                _, addr = s.recvfrom(1024)
                attempts = 0
                time.sleep(2)
                
            except socket.timeout:
                attempts += 1
                print(f'Could not reach server, attempt {attempts}/5\n')

    except KeyboardInterrupt:
        disconnect = 'NOTIFY * HTTP/1.1\r\nHOST:224.0.1.20:1900\r\nNTS:ssdp:byebye\r\nUSN:mydevice:service\r\nNT:mydevice:service\r\n\r\n'
        dead = True
        conn.sendto(disconnect.encode(), addr)
        print(f'\nSent disconnect request message to server ip address {addr[0]} and server port {addr[1]}\n')
        conn.close()
        
    finally:
        try:
            conn.close()
            print(f'\nServer disconnected\n')
        except NameError:
            print(f'\nCould not find server\n')
        finally:
            s.close()
            if dead is True:
                exit()
            else:
                print('Restarting...\n')
                time.sleep(5)
                try:
                    main()
                except KeyboardInterrupt:
                    exit()

main()