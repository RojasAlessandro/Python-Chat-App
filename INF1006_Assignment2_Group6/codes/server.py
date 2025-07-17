import socket
import threading
from datetime import datetime


HOST = '127.0.0.1'
PORT = 12345

clients = {}  # username: socket
groups = {}   # groupname: set of usernames
user_status = {}  # username: status
blocked_users = {}  # username: set[usernames blocked]
history = [] # [(ts, sender, scope, target, text)]
lock = threading.Lock()

def log_message(sender: str, scope: str, target: str, msg: str):
    """Helper to keep a timestamped history line."""
    ts = datetime.now().strftime('%H:%M:%S')
    history.append((ts, sender, scope, target, msg))

def deliver(to_user: str, payload: str, from_user: str | None = None):
    """Send `payload` to `to_user` unless he/she has blocked `from_user`."""
    # system messages (from_user is None) bypass blocking
    if from_user and from_user in blocked_users.get(to_user, set()):
        return
    try:
        clients[to_user].send(payload.encode())
    except:
        pass # ignore broken pipes for this demo

def broadcast(payload: str, sender: str | None = None):
    with lock:
        for user in clients.keys():
            if user != sender: # do not echo to sender
                deliver(user, payload, sender)

def show_history(conn, requester, tokens):
    """
    @history N
    @history user <username> N
    @history group <group> N
    """
    try:
        if len(tokens) == 2:  # public only
            n = int(tokens[1])
            filt = lambda h: h[2] == 'public'
        elif len(tokens) == 4 and tokens[1] in ('user', 'group'):
            mode, target, n = tokens[1], tokens[2], int(tokens[3])
            if mode == 'user':
                filt = lambda h: h[2] == 'dm' and \
                                   {h[1], h[3]} == {requester, target}
            else:  # group
                if requester not in groups.get(target, set()):
                    conn.send("You are not in that group.".encode()); return
                filt = lambda h: h[2] == 'group' and h[3] == target
        else:
            conn.send("Usage: @history [user|group] <name> N".encode()); return

        with lock:
            lines = [f"[{t}] {s}->{g}: {m}"
                     for (t, s, sc, g, m) in history if filt((t, s, sc, g, m))]

        output = "\n".join(f"(history) {line}" for line in lines[-n:] or ["<no records>"])
        conn.send(output.encode())

    except ValueError:
        conn.send("N must be an integer.".encode())

def handle_client(conn, addr):
    username = ""
    try:
        # ------------- handshake -------------
        while True:
            conn.send("Enter your username: ".encode())
            username = conn.recv(1024).decode().strip()

            if not username or " " in username:
                conn.send("Invalid username. No spaces allowed.\n".encode()); continue

            with lock:
                if username in clients:
                    conn.send("Username taken. Try another.\n".encode())
                else:
                    clients[username] = conn
                    user_status[username] = "Available"
                    blocked_users[username] = set()
                    break

        print(f"[{username}] connected from {addr}")
        broadcast(f"[{username}] has joined the chat.", sender=username)
        # ------------- main loop -------------
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            # ---------- simple commands ----------
            if data.startswith('@quit'):
                break

            elif data.startswith('@names'):
                with lock:
                    names = ", ".join(clients.keys())
                conn.send(f"Connected users: {names}".encode())

            elif data.startswith('@status'):
                new = data[len('@status'):].strip()
                if new:
                    with lock: user_status[username] = new
                    conn.send(f"Status updated to '{new}'.".encode())
                else:
                    conn.send("Usage: @status <new_status>".encode())

            elif data.startswith('@whois'):
                parts = data.split()
                if len(parts) == 2:
                    target = parts[1]
                    with lock:
                        st = user_status.get(target)
                    conn.send(f"{target} is '{st}'." .encode() if st
                              else f"No such user '{target}'.".encode())
                else:
                    conn.send("Usage: @whois <username>".encode())

            # ---------- NEW: blocking ----------
            elif data.startswith('@blocklist'):
                bl = ", ".join(sorted(blocked_users[username])) or "<empty>"
                conn.send(f"Currently blocked: {bl}".encode())

            elif data.startswith('@block '):
                target = data.split()[1]
                if target == username:
                    conn.send("You cannot block yourself.".encode())
                else:
                    blocked_users[username].add(target)
                    conn.send(f"Blocked '{target}'.".encode())

            elif data.startswith('@unblock '):
                target = data.split()[1]
                blocked_users[username].discard(target)
                conn.send(f"Unblocked '{target}'.".encode())

            # ---------- group / history ----------
            elif data.startswith('@group'):
                handle_group_commands(conn, username, data)

            elif data.startswith('@history'):
                show_history(conn, username, data.split())

            # ---------- private DM ----------
            elif data.startswith('@'):
                target, _, msg = data.partition(' ')  # "@bob", "hello"
                target = target[1:]
                if not msg:
                    conn.send("Invalid private message format.".encode()); continue
                with lock:
                    if target in clients:
                        deliver(target, f"[DM from {username}]: {msg}", username)
                        log_message(username, 'dm', target, msg)
                    else:
                        conn.send(f"User '{target}' not found.".encode())

            # ---------- public broadcast ----------
            else:
                broadcast(f"[{username}]: {data}", sender=username)
                log_message(username, 'public', 'all', data)

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:   # tear-down
        with lock:
            clients.pop(username, None)
            user_status.pop(username, None)
            blocked_users.pop(username, None)
            broadcast(f"[{username}] has left the chat.")
        conn.close()
        print(f"[{username}] disconnected.")

def handle_group_commands(conn, username, command):
    # same signature as before, with minor additions for history + blocking
    tokens = command.split()
    if len(tokens) < 3:
        conn.send("Invalid group command.".encode()); return
    action, gname = tokens[1], tokens[2]

    if action == 'set':
        members = {m.strip(',') for m in tokens[3:]} | {username}
        with lock:
            if gname in groups:
                conn.send("Group already exists.".encode()); return
            groups[gname] = members
        conn.send(f"Group '{gname}' created.".encode())

    elif action == 'send':
        if len(tokens) < 4:
            conn.send("Usage: @group send <gname> <msg>".encode()); return
        msg = " ".join(tokens[3:])
        with lock:
            if gname not in groups or username not in groups[gname]:
                conn.send("Group not found / not a member.".encode()); return
            recipients = groups[gname] - {username}
        for m in recipients:
            deliver(m, f"[{gname} from {username}]: {msg}", username)
        log_message(username, 'group', gname, msg)

    elif action == 'leave':
        with lock:
            if username in groups.get(gname, set()):
                groups[gname].remove(username)
                conn.send(f"You left '{gname}'.".encode())
            else:
                conn.send("You are not in that group.".encode())

    elif action == 'delete':
        with lock:
            if gname in groups and username in groups[gname]:
                del groups[gname]
                conn.send(f"Group '{gname}' deleted.".encode())
            else:
                conn.send("Cannot delete – either no such group or you’re not a member.".encode())
    else:
        conn.send("Unknown group sub-command.".encode())

def start_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((HOST, PORT)); srv.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()