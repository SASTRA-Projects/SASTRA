import pymysql

timeout = 10

db_connector = None
cursor = None

def connect(user, __pwd, host="mysql-93e938b-harikrishnasri3.f.aivencloud.com"):
  global db_connector, cursor
  db_connector = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    host=host,
    password=__pwd,
    read_timeout=timeout,
    port=17216,
    user=user,
    write_timeout=timeout,
  )

  cursor = db_connector.cursor()
  db_connector.autocommit = False

  cursor.execute("""CREATE DATABASE IF NOT EXISTS `SASTRA`""")
  cursor.execute("""USE `SASTRA`""")

def close():
	db_connector.commit()
	cursor.close()
	db_connector.close()
	exit()

if __name__ == "__main__":
	close()
