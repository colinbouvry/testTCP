import select
import socket
import threading
from datetime import datetime
from pythonosc.osc_message import OscMessage

CONNECTION_LIST_TCP = []
CONNECTION_LIST_UDP = []
RECV_BUFFER = 4096
TCP_IP = "0.0.0.0"  # Define the TCP IP address
TCP_PORT = 5000
UDP_IP = "0.0.0.0"  # Define the UDP IP address
UDP_PORT = 5001  # Define the UDP port

def broadcast_data(server_socket, socket, message):
    for client_socket in CONNECTION_LIST_TCP:
        if client_socket != server_socket and client_socket != socket:
            try:
                client_socket.send(message)
            except:
                client_socket.close()
                CONNECTION_LIST_TCP.remove(client_socket)

def find_all(data, value=192):
    indices = []
    start = 0
    while True:
        try:
            index = data.index(value, start)
            indices.append(index)
            start = index + 1
        except ValueError:
            break
    return indices

def tcp_server(server_socket):
    CONNECTION_LIST_TCP.append(server_socket)
    while True:
        ready_to_read, _, _ = select.select(CONNECTION_LIST_TCP, [], [])
        for current_socket in ready_to_read:
            if current_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                CONNECTION_LIST_TCP.append(client_socket)
                print(f"Client {client_address} connected")
            else:
                try:
                    data = current_socket.recv(RECV_BUFFER)
                    system_time = datetime.now().timestamp() # get the current system time
                    if data:
                        # Broadcast the received data to all other clients
                        broadcast_data(server_socket, current_socket, data)
                        # Parse the received data as an OSC message
                        print(f"TCP message: {data}")
                        # find all occurrences of 192 in the data
                        indices = find_all(data)
                        data_between = []
                        if indices:
                            if len(indices) == 1:
                                data_between.append(data)
                            else:
                                for i in range(len(indices) - 1):
                                    data_between.append(data[indices[i]+1:indices[i+1]])
                        else:
                            data_between.append(data)
                        # print(f"The data between all occurrences of 192 is {data_between}")

                        for i in range(len(data_between)):
                            try:
                                osc_msg = OscMessage(data_between[i])
                            except:
                                print(f"Cannot decode OSC message: {data_between[i]}")
                                continue

                            # Now you can access the OSC message's address and arguments
                            label = osc_msg.address
                            args = osc_msg.params
                            print(f"TCP OSC message: {label} {args}")

                            if label == "/time" and len(args) == 2:
                                received_time1 = args[0]/1000.0
                                received_time2 = args[1]/1000.0
                                received_time1_utc = received_time1 - 7200

                                # Now you can compare received_time1, received_time2 and system_time, or synchronize them as needed
                                print(f"Received time 1: {received_time1_utc}, Received time 2: {received_time2}, System time: {system_time}, latency: {system_time - received_time1_utc} ")
                            else:
                                if label == "/button1" and len(args) == 1:
                                    buttonarg0 = args[0]
                                    # print(f"Button 1: {buttonarg0}")
                            
                    else:
                        print("ConnectionResetError")
                        raise ConnectionResetError

                except ConnectionResetError:
                    broadcast_data(server_socket, current_socket, f"Client {client_address} is offline")
                    print(f"Client {client_address} is offline")
                    current_socket.close()
                    CONNECTION_LIST_TCP.remove(current_socket)

def udp_server(server_socket):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((UDP_IP, UDP_PORT))
    CONNECTION_LIST_UDP.append(udp_socket)

    while True:
        data, addr = udp_socket.recvfrom(RECV_BUFFER)
        system_time = datetime.now().timestamp() # get the current system time
        if data:
            print("UDP message:", data)
            # Broadcast the received data to all other clients
            broadcast_data(server_socket, server_socket, data)
            # Handle UDP data
            try:
                osc_msg = OscMessage(data)
                # Now you can access the OSC message's address and arguments
                label = osc_msg.address
                args = osc_msg.params
                print(f"UDP OSC message: {label} {args}")
            except:
                print(f"Cannot decode OSC message: {data}")


def main():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((TCP_IP, TCP_PORT))
    server_socket.listen(10)

    tcp_thread = threading.Thread(target=tcp_server, args=(server_socket,))
    udp_thread = threading.Thread(target=udp_server, args=(server_socket,))

    tcp_thread.start()
    udp_thread.start()

    tcp_thread.join()
    udp_thread.join()

if __name__ == "__main__":
    main()