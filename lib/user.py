import socket

class User:
  __name: str
  id: int
  __id_counter: int = 0
  __connection: socket.socket
  def __init__(self, name: str, connection: socket.socket) -> None:
    self.__name = name
    self.__connection = connection
    User.__id_counter += 1

  @property
  def connection(self) -> socket.socket:
    return self.__connection

  @property
  def name(self) -> str:
    return self.__name
  
  def __eq__(self, value: object) -> bool:
    return type(value) == User and value.name == self.name

if __name__ == "__main__":
  print(User.__name)