from asyncio import wait_for
import socket
import sys
from lib.proto import MessageType, recv_message, send_and_recv_message, send_message
import readline

def wait_for_game_start(connection: socket.socket):
  pass

if __name__ == "__main__":
  server_ip = "127.0.0.1"
  server_port = 12345
  if (len(sys.argv) == 2):
    server_port = int(sys.argv[1])
  server_address = (server_ip, server_port)
  connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    connection.connect(server_address)  
    while (True):    
      command = input("> ").strip()
      if (command == "help"):
        print("login - login to the server")
        print("register - register a new account")
        print("whoami - show the current user")
        print("logout - logout from the server")
        print("exit - exit the program")
        print("help - show this message")
      elif (command == "login"):
        username = input("username: ")
        password = input("password: ")
        response = send_and_recv_message(connection, {
          "type": MessageType.LOGIN_REQUEST.name,
          "username": username,
          "password": password,
        })
        if response["type"] == MessageType.ERROR.name:
          print("login failed")
        else:
          print("logged in successfully")
      elif (command == "register"):
        username = input("username: ")
        password = input("password: ")
        send_message(connection, {
          "type": MessageType.REGISTER_REQUEST.name,
          "username": username,
          "password": password
        })
        response = recv_message(connection)
        if response["type"] == MessageType.ERROR.name:
          print("register failed")
        else:
          print("registered successfully")
      elif (command == "whoami"):
        response = send_and_recv_message(connection, {
          "type": MessageType.WHOAMI_REQUEST.name
        })
        if response["type"] == MessageType.ERROR.name:
          print("failed to get user information")
        else:
          print(f"{response['username']}")
      elif (command == "logout"):
        response = send_and_recv_message(connection, {
          "type": MessageType.LOGOUT_REQUEST.name
        })
        if response["type"] == MessageType.ERROR.name:
          print("failed to logout")
        else:
          print("logged out successfully")
      elif (command == "new room"):
        try:
          player_count = int(input("player count: "))
        except:
          print("invalid player count")
          continue
        response = send_and_recv_message(connection, {
          "type": MessageType.ROOM_CREATION_REQUEST.name,
          "player_count": player_count,
        })
        if response["type"] == MessageType.OK.name:
          print(f"room created successfully with id {response['room_id']}")
          print(f"1/{player_count} joined")
          wait_for_game_start(connection)
        else:
          print("failed to create room")
      elif (command == "exit"):
        connection.close()
        break
      elif command == "join room":
        try:
          room_id = int(input("room id: "))
        except:
          print("invalid room id")
          continue
        response = send_and_recv_message(connection, {
          "type": MessageType.ROOM_CONNECTION_REQUEST.name,
          "room_id": room_id 
        })
        if response["type"] == MessageType.ERROR.name:
          print(f"cannot join room with id {room_id}")
          continue
        print(f"joined room with id {room_id}")
        print(f"{response["current_player_count"]}/{response["max_player_count"]} joined")
        wait_for_game_start(connection)
      else:
        print("invalid command")
  except Exception as e:
    connection.close()
    print(e)