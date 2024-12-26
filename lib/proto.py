from enum import Enum, auto
import json
import socket
from typing import Any

class MessageType(Enum):
  ROOM_CONNECTION_REQUEST = auto()
  ROOM_CREATION_REQUEST = auto()
  REGISTER_REQUEST = auto()
  LOGIN_REQUEST = auto()
  WHOAMI_REQUEST = auto()
  LOGOUT_REQUEST = auto()
  ROOM_CLOSE_UPDATE = auto()
  ROOM_JOIN_UPDATE = auto()
  GAME_START_UPDATE = auto()
  OK = auto()
  ERROR = auto()
  
def recv_message(connection: socket.socket) -> dict[str, Any]:
  CHUNK_SIZE = 1024
  message_length_bytes = connection.recv(4)
  message_length = int.from_bytes(message_length_bytes)
  message = b""
  while (message_length > CHUNK_SIZE):
    message += connection.recv(CHUNK_SIZE)
    message_length -= 1024
  if (message_length > 0):
    message += connection.recv(message_length)
  json_message: dict[str, Any]
  json_message = json.loads(message.decode('utf-8'))
  return json_message
    
def send_message(connection: socket.socket, message: dict[str, Any]):
  message_bytes = json.dumps(message).encode('utf-8')
  message_length = len(message_bytes).to_bytes(4)
  connection.sendall(message_length)
  connection.sendall(message_bytes)
    
def send_and_recv_message(connection: socket.socket, message: dict[str, Any]):
  send_message(connection, message)
  return recv_message(connection)