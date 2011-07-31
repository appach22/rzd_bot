#coding=utf-8

import MySQLdb
from copy import deepcopy

host = "localhost"
database = "rzdtickets.ru"
user = "rzdbot"
passw = "rzdtickets22"

class db:

    def __init__(self):
        self.rows = []
        self.lastrowid = 0

    def query(self, query):
        self.rows = []
        try:
            conn = MySQLdb.connect(host = host,
                                   user = user,
                                   passwd = passw,
                                   db = database,
                                   charset = "utf8", 
                                   use_unicode = True)
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return False
        else:
            try:
                cursor = conn.cursor()
            except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return False
            else:
                try:
                    cursor.execute(query)
                    self.lastrowid = cursor.lastrowid
                    row = cursor.fetchone()
                    while not row == None:
                        self.rows.append(deepcopy(row))
                        row = cursor.fetchone()
                except MySQLdb.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    return False
                finally:
                    cursor.close()
            finally:
                conn.close()

        return True

    def queries(self, queries):
        for query in queries:
            if not self.query(query):
                return False
        return True
