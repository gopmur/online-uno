from curses import OK
from os import name
import socket
import threading

from lib.proto import MessageType, recv_message, send_message
from lib.room import Room
from lib.user import User

import models
from models import db

active_rooms: list[Room] = []
active_rooms_lock = threading.Lock()
active_sessions: list[User] = []
active_sessions_lock = threading.Lock()

def register_user(connection: socket.socket, message: dict[str, str]) -> None:
  username: str = message["username"]
  password: str = message["password"]
  with db.atomic():
    try:
      models.User.create(username=username, password=password)
      send_message(connection, {
        "type": MessageType.OK.name
      })
      print(f"user {username} registered")
    except:
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      print(f"failed to register user {username}")

def login_user(connection: socket.socket, message: dict[str, str], active_session: User | None) -> User | None:
  username: str = message["username"]
  password: str = message["password"]
  try:
    if active_session:
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      print(f"user {active_session.name} already logged in")
      return active_session
    with db.atomic():
      user = models.User.get_or_none(models.User.username == username, models.User.password == password)
    if not user:
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      print(f"failed to login user {username}")
      return None
    with active_sessions_lock:
      active_session = User(username, connection)
      active_sessions.append(active_session)
    send_message(connection, {
      "type": MessageType.OK.name
    })
    print(f"user {username} logged in")
    return active_session
  except:
    send_message(connection, {
      "type": MessageType.ERROR.name
    })
    print(f"failed to login user {username}")
    return None

def whoami(connection: socket.socket, client_address: tuple[str, int], user: User | None) -> None:
  if not user:
    send_message(connection, {
      "type": MessageType.ERROR.name
    })
    print(f"failed to get user information for {client_address}")
  else:
    send_message(connection, {
      "type": MessageType.OK.name,
      "username": user.name,
    })
    print(f"sent user information for {client_address}")

def logout_user(connection: socket.socket, client_address: tuple[str, int], user: User | None) -> None:
  with active_sessions_lock:
    if user:
      active_sessions.remove(user)
      send_message(connection, {
        "type": MessageType.OK.name
      })
      print(f"user {user.name} logged out")
    else:
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      print(f"failed to logout user {client_address}")

def create_room(connection: socket.socket, message: dict[str, int], user: User | None) -> None:
  player_count = message["player_count"]
  if not user:
    send_message(connection, {
      "type": MessageType.ERROR.name
    })
    print(f"failed to create room")
    return
  with active_rooms_lock:
    room = next(filter(lambda r: r.owner.name == user.name if user else None, active_rooms), None)
    if room:
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      print(f"user {user.name} already has a room")
      return
  with active_rooms_lock:
    try:
      room = Room(user, player_count)
      active_rooms.append(room)
    except:
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      print(f"failed to create room for {user.name}")
      return
  send_message(connection, {
    "type": MessageType.OK.name,
    "room_id": room.id
  })
  print(f"room {room.id} created by {user.name}")

def join_room(connection: socket.socket, message: dict[str, str], user: User | None) -> None:
  if not user:
    print(f"user cannot join because not logged in")
    send_message(connection, {
      "type": MessageType.ERROR.name
    })
    return
  room_id = message["room_id"]
  with active_rooms_lock:
    active_room = next(filter(lambda room : room.id == room_id, active_rooms), None)
    if not active_room:
      print(f"user {user.name} cannot join because room {room_id} does not exists")
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      return
    if active_room.is_full:
      print(f"user {user.name} cannot join because room {room_id} is full")
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      return
    try:
      active_room.add_user(user)
    except:
      print(f"user {user.name} cannot join because room {room_id} already is joined")
      send_message(connection, {
        "type": MessageType.ERROR.name
      })
      return
    for (i, user_in_room) in enumerate(active_room.users):
      send_message(user_in_room.connection, {
        "type": MessageType.ROOM_JOIN_UPDATE.name,
        "username": user.name,
        "max_player_count": active_room.max_player_count,
        "current_player_count": len(active_room.users)
      })
  print(f"user {user.name} joined room {room_id}")
   
def serve_client(connection: socket.socket, client_address: tuple[str, int]) -> None:
  user: User | None = None
  try:
    while (True):      
      message = recv_message(connection)
      if message["type"] == MessageType.REGISTER_REQUEST.name:
        register_user(connection, message)
      elif message["type"] == MessageType.LOGIN_REQUEST.name:
        user = login_user(connection, message, user)
      elif message["type"] == MessageType.WHOAMI_REQUEST.name:
        whoami(connection, client_address, user)
      elif (message["type"] == MessageType.LOGOUT_REQUEST.name):
        logout_user(connection, client_address, user)
        user = None
      elif (message["type"] == MessageType.ROOM_CREATION_REQUEST.name):
        create_room(connection, message, user)
      elif (message["type"] == MessageType.ROOM_CONNECTION_REQUEST.name):
        join_room(connection, message, user)
      else:
        send_message(connection, {
          "type": MessageType.ERROR.name
        })
        print(f"received invalid message from {client_address}")
  except Exception as e:
    print(e)
    print(f"connection with {client_address} closed")
    if user:
      with active_sessions_lock:
        for active_session in active_sessions:
          if active_session.name == user.name:
            print(f"logging out user {active_session.name}")
            active_sessions.remove(active_session)
      with active_rooms_lock:
        for active_room in active_rooms:
          if active_room.owner.name == user.name:
            for active_user in active_room.users:
              print(f"closing room connection with {active_user.name}")
              try:
                send_message(active_user.connection, {
                  "type": MessageType.ROOM_CLOSE_UPDATE.name
                })
              except:
                active_user.connection.close()
            print(f"closing room {active_room.id}")
            active_rooms.remove(active_room)
          elif active_room.has_user(user):
            active_room.remove_user(user)
    connection.close()
      
    

if __name__ == "__main__":
  SERVER_IP = "127.0.0.1"
  server_port = 12345
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:    
    while (True):
      server_address = (SERVER_IP, server_port)
      try:    
        server_socket.bind(server_address)
        break
      except:
        server_port += 1
    server_socket.listen(1)
    print(f"listening on {SERVER_IP}:{server_port}")
    while (True):
      print("waiting for connection")
      connection, client_address = server_socket.accept()
      client_ip, client_port = client_address
      print(f"connection established with {client_ip}:{client_port}")
      thread = threading.Thread(target=serve_client, daemon=True, args=[connection, client_address])
      thread.start()
  except Exception as e:
    print(e)
    server_socket.close()
