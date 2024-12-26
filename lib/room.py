from lib.user import User
from uno.uno import UnoGame

class Room:
  __owner: User
  __users: list[User]
  __id: int
  __id_counter: int = 0
  __game: UnoGame
  __max_player_count: int
    
  def __init__(self, creator: User, player_count: int) -> None:
    self.__users = [creator]
    self.__owner = creator
    self.__id = Room.__id_counter
    self.__max_player_count = player_count
    Room.__id_counter += 1
    self.__game = UnoGame(player_count)

  def has_user(self, user: User) -> bool:
    return len(list(filter(lambda u : u.name == user.name, self.users))) != 0
    

  def add_user(self, user: User) -> None:
    if self.is_full:
      raise Exception("room is full")
    for user_in_room in self.users:
      if user_in_room.name == user.name:
        raise Exception("user already in room") 
    self.__users.append(user)
    
  def remove_user(self, user: User) -> None:
    if user not in self.__users:
      raise Exception("User not in room")
    self.__users.remove(user)
    if user == self.owner:
      self.__owner = self.__users[0]
      
  @property
  def users(self) -> list[User]:
    return self.__users
  
  @property
  def owner(self) -> User:
    return self.__owner
  
  @property
  def is_full(self) -> bool:
    return self.max_player_count == len(self.users)
  
  @property
  def max_player_count(self) -> int:
    return self.__max_player_count
  
  @property
  def player_count(self) -> int:
    return len(self.__users)  
  
  @property
  def id(self) -> int:
    return self.__id
  
  @property
  def game(self) -> UnoGame:
    return self.__game