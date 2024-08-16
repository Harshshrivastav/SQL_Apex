import sqlite3

connection = sqlite3.connect('./student.db')
cursor = connection.cursor()

cursor.execute("SELECT name FROM STUDENT;")
tables = cursor.fetchall()
print(tables)
