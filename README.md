# Python Socket Chat Application (Group G6)

## Group Members
| Name                             | Student IDs |
|----------------------------------|-------------|
| Ang Ke Ying                      |             |
| Rojas Alessandro Rafael Doronila |             |
| Tay Yu Xuan Jolene               |             |
| Choh Kaifeng                     |             |
| Raffael Davin Harjanto           |             |

---

## Features Implemented

### Core Functionality
- **Client-server chat system** using TCP sockets and threading.
- **Username registration** with uniqueness check.
- **Broadcast messaging** to all connected users.
- **Private messaging** using `@username <message>`.
- **User list retrieval** via `@names`.
- **Disconnection support** via `@quit`.

### Group Chat Commands
- `@group set <groupname> <user1> <user2> ...`: Create a group.
- `@group send <groupname> <message>`: Send message to group members.
- `@group leave <groupname>`: Leave a group.
- `@group delete <groupname>`: Delete group if member.

### Enhancement: Customizable User Status
- `@status <new_status>`: Set your current status (e.g., Busy, Away).
- `@whois <username>`: View another user’s status.

### Chat History Logging
Retrieve past messages by replacing `N` with the number of messages you want to view:
- `@history N` — View the last **N public messages**.  
  _Example: `@history 5` shows the 5 most recent public messages._
- `@history user <username> N` — View the last **N direct messages** with the specified user.  
  _Example: `@history user Alice 3` shows the last 3 private messages with Alice._
- `@history group <groupname> N` — View the last **N messages** in the specified group chat.  
  _Example: `@history group devs 10` shows the last 10 messages in the "devs" group._
  
### User Blocking Feature
  - `@block <username>` — Block messages from a user.  
  - `@unblock <username>` — Unblock a user.  
  - `@blocklist` — View a list of currently blocked users.

---

## How to Run the Application
1. Open 4x Command Prompt
2. CD to the location where the files are saved
3. Run the command `Python server.py` for one of the command prompts
4. Run the command `Python client.py` for the remaining command prompts
5. Enter the usernames when prompted by the client, Commands can be refered in the above section

### Requirements
- Python 3.6+
- Command-line interface (Command Prompt)

### Folder Structure
codes/
├── server.py
├── client.py
└── README.md
video/
│ └── video_url.txt
├── report/
    └── report.pdf
