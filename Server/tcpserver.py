import select
import socket
import struct
from datetime import datetime
from pythonosc.osc_message import OscMessage

CONNECTION_LIST = []
RECV_BUFFER = 4096
TCP_IP = "0.0.0.0"  # Define the TCP IP address
TCP_PORT = 5000
UDP_IP = "0.0.0.0"  # Define the UDP IP address
UDP_PORT = 5001  # Define the UDP port

def broadcast_data(server_socket, socket, message):
    for client_socket in CONNECTION_LIST:
        if client_socket != server_socket and client_socket != socket:
            try:
                client_socket.send(message)
            except:
                client_socket.close()
                CONNECTION_LIST.remove(client_socket)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((TCP_IP, TCP_PORT))
    server_socket.listen(10)

    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((UDP_IP, UDP_PORT))

    # Add the UDP and TCP socket to the connection list
    CONNECTION_LIST.append(udp_socket)
    CONNECTION_LIST.append(server_socket)

    while True:
        ready_to_read, _, _ = select.select(CONNECTION_LIST, [], [])

        for current_socket in ready_to_read:
            if current_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                CONNECTION_LIST.append(client_socket)
                print(f"Client {client_address} connected")
            elif current_socket == udp_socket:
                data, addr = current_socket.recvfrom(RECV_BUFFER)
                if data:
                    # Handle UDP data
                    try:
                        osc_msg = OscMessage(data)
                        # Now you can access the OSC message's address and arguments
                        label = osc_msg.address
                        args = osc_msg.params
                        print(f"Received OSC message: {label} {args}")
                        
                        # Broadcast the received data to all other clients
                        broadcast_data(server_socket, current_socket, data)
                    except:
                        print(f"Cannot decode OSC message: {data}")
            else:
                try:
                    system_time = datetime.now().timestamp() # get the current system time
                    data = current_socket.recv(RECV_BUFFER)
                    if data:
                        # Broadcast the received data to all other clients
                        broadcast_data(server_socket, current_socket, data)
                        # Parse the received data as an OSC message
                        print(f"OSC message: {data}")
                        if(data[0] == 192 and data[len(data)-1] == 192):
                            # subtring the data to remove the first byte
                            data2  = data[1:len(data)-1]
                        else:
                            data2 = data
                            print(f"Cannot decode OSC message without 192: {data}")

                        try:
                            osc_msg = OscMessage(data2)
                        except:
                            print(f"Cannot decode OSC message: {data2}")
                            continue

                        # Now you can access the OSC message's address and arguments
                        label = osc_msg.address
                        args = osc_msg.params
                        if label == "/time" and len(args) == 2:
                            received_time1 = args[0]
                            received_time2 = args[1]
                            received_time1_utc = received_time1 - 7200

                            # Now you can compare received_time1, received_time2 and system_time, or synchronize them as needed
                            print(f"Received time 1: {received_time1_utc}, Received time 2: {received_time2}, System time: {system_time}, latency: {system_time - received_time1_utc} ")
                        else:
                            if label == "/button1" and len(args) == 2:
                                buttonarg0 = args[0]
                                buttonarg1 = args[1]
                                print(f"Button 1: {buttonarg0}, 2: {buttonarg1}")
                            
                    else:
                        raise ConnectionResetError
                except ConnectionResetError:
                    broadcast_data(server_socket, current_socket, f"Client {client_address} is offline")
                    print(f"Client {client_address} is offline")
                    current_socket.close()
                    CONNECTION_LIST.remove(current_socket)

    server_socket.close()
    udp_socket.close()

if __name__ == "__main__":
    main()