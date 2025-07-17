import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if msg:
                print(msg)
            else:
                break
        except:
            break

def send_messages(sock):
    while True:
        try:
            msg = input()
            sock.send(msg.encode())
            if msg.startswith('@quit'):
                break
        except:
            break

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # Prompt for and send username immediately
    prompt = client.recv(1024).decode()
    print(prompt, end='')  # Display "Enter your username: "
    username = input()
    client.send(username.encode())  # Send username before launching threads

    # Now start listening and sending messages
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()
    send_messages(client)
    client.close()

if __name__ == "__main__":
    main()
