import socket

class User:
  __name: str
  __id: int
  __id_counter: int = 0
  __connection: socket.socket
  def __init__(self, name: str, connection: socket.socket) -> None:
    self.__name = name
    self.__id = User.__id_counter
    self.__connection = connection
    User.__id_counter += 1

  @property
  def connection(self) -> socket.socket:
    return self.__connection

  @property
  def name(self) -> str:
    return self.__name
  
  @property
  def id(self) -> int:
    return self.__id
  
  def __eq__(self, value: object) -> bool:
    return type(value) == User and value.name == self.name

if __name__ == "__main__":
  print(User.__name)