import pymysql.cursors


def connect_db():
    try:
        # Establish a connection to the MySQL database
        conn = pymysql.connect(
            host="192.168.5.229",
            user="root",
            password="YeGhbdtnHf,jnybxrb69",
            charset='utf8',
            database="antivor",
            cursorclass=pymysql.cursors.DictCursor  # Use a dictionary cursor for easier access to results
        )
        return conn
    except pymysql.Error as e:
        print(f"Error: Unable to connect to MySQL database. {e}")
        return None



def copy():
    conn = connect_db()
    cursor = conn.cursor()
    select_all_data = "SELECT * FROM pc_reloader LIMIT 250"
    cursor.execute(select_all_data)
    all_data = cursor.fetchall()

    for data in all_data:
        print(data['Ip'])
        insert = ("INSERT INTO tester (Ip, HostName, UserName, Domain, UpTime, LastUpdate, Logged, Surname) VALUES(%s, %s, "
                  "%s, %s, %s, %s, %s, %s)")
        cursor.execute(insert,(data['Ip'],data['HostName'],data['UserName'],data['Domain'],data['UpTime'],data['LastUpdate'],data['Logged'],data['Surname']))
    conn.commit()
    conn.close()


