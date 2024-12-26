import socket
import sys
from typing import Any
from lib.proto import MessageType, recv_message, send_and_recv_message, send_message
import readline
from termcolor import colored

def enter_game(connection: socket.socket, message: dict[str, Any]):
  id = message["id"]
  while (True):
    if message["type"] == MessageType.GAME_END_UPDATE.name:
      print("game ended")
      print(f"winner: {message['winner']}")
      break
    print(f"your hand:")
    for (i, card) in enumerate(message["hand"]):
      print(f"{i}. {colored(card["type"], card["color"])}")
    print("")
    current_card = message["current_card"]
    print(f"current card: {colored(current_card["type"], current_card["color"])}")
    if id == message["turn"]:
      valid_move = False 
      while not valid_move:
        command = input("> ").strip()
        
        if command == "draw":
          response = send_and_recv_message(connection, {
            "type": MessageType.DRAW_CARD_REQUEST.name
          })
          if response["type"] == MessageType.ERROR.name:
            print("cannot draw card")
          else:
            message = response
            valid_move = True
          
        elif command.startswith("play"):
          card_index = None
          try:
            card_index = int(command[5:])
            message["hand"][card_index]
          except:
            print("invalid card index")
            continue
          
          if card_index != None and message["hand"][card_index]["color"] == "black":
            color = input("color: ")
            if color not in ["red", "green", "blue", "yellow"]:
              print("invalid color")
              continue
            
            response = send_and_recv_message(connection, {
              "type": MessageType.CARD_DROP_REQUEST.name,
              "card_index": card_index,
              "color": color
            })
            if response["type"] == MessageType.ERROR.name:
              print("cannot play card")
            else:
              message = response
              valid_move = True
              break
            
          elif card_index != None:
            response = send_and_recv_message(connection, {
              "type": MessageType.CARD_DROP_REQUEST.name,
              "card_index": card_index
            })
            if response["type"] == MessageType.ERROR.name:
              print("cannot play card")
            else:
              message = response
              valid_move = True
        
        else:
          print("invalid command")
        
    else:
      message = recv_message(connection)

def wait_for_game_start(connection: socket.socket):
  while (True):
    message = recv_message(connection)
    if message["type"] == MessageType.ROOM_JOIN_UPDATE.name:
      max_player_count = message["max_player_count"]
      current_player_count = message["current_player_count"]
      joined_username = message["username"]
      print(f"{joined_username} join the room")
      print(f"{current_player_count}/{max_player_count} joined")
    elif message["type"] == MessageType.GAME_START_UPDATE.name: 
      enter_game(connection, message)
    elif message["type"] == MessageType.ROOM_CLOSE_UPDATE.name:
      print("room closed")
      break

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