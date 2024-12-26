from peewee import SqliteDatabase, Model, CharField, IntegerField

db = SqliteDatabase("uno.db")

class User(Model):
    id = IntegerField(primary_key=True)
    username = CharField(unique=True, null=False)
    password = CharField(null=False)
    wins = IntegerField(default=0)
    losses = IntegerField(default=0)

    class Meta:
        database = db

db.connect()
if __name__ == "__main__":
  db.create_tables([User])

  # User.create(username="gopmur", password="1234")
  # for user in User.select():
  #     print(user.username, user.password)


