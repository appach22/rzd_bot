import sys
import MySQLdb
#import trackingData

def prepareDatabase():
    try:
        conn = MySQLdb.connect(host = "localhost",
                               user = "root",
                               passwd = "123456",
                               charset = "utf8", 
                               use_unicode = True)#,
                               #db = "test")
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        return False
    else:
        try:
            cursor = conn.cursor ()
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return False
        else:
            try:
                cursor.execute("CREATE DATABASE IF NOT EXISTS rzdbot CHARACTER SET utf8")
            except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return False
            finally:
                cursor.close()
        finally:
            conn.close()
    
    return True


def prepareTables():
    try:
        conn = MySQLdb.connect(#host = "%",
                               user = "root",
                               passwd = "rzdtickets22",
                               db = "rzdtickets.ru",
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
                cursor.execute("DROP TABLE IF EXISTS bot_static_info")
                cursor.execute("""
                    CREATE TABLE bot_static_info
                    (
                        uid                 INT,
                        username            VARCHAR(40),
                        emails              VARCHAR(128) NOT NULL,
                        sms                 VARCHAR(24),    
                        creation_date       DATETIME NOT NULL,
                        station_from        VARCHAR(50) NOT NULL,
                        station_to          VARCHAR(50) NOT NULL,
                        date1               DATE NOT NULL,
                        trains1             VARCHAR(32) NOT NULL,
                        date2               DATE,
                        trains2             VARCHAR(32),
                        date3               DATE,
                        trains3             VARCHAR(32),
                        places_range_low    TINYINT,    
                        places_range_high   TINYINT,
                        places_parity       TINYINT,
                        car_type            TINYINT NOT NULL,
                        ip_addr             VARCHAR(24),
                        sms_count           SMALLINT,
                        PRIMARY KEY (uid)
                    )
                            """)
                
                cursor.execute("DROP TABLE IF EXISTS bot_dynamic_info")
                cursor.execute("""
                    CREATE TABLE bot_dynamic_info
                    (
                        uid                 INTEGER,
                        pid                 SMALLINT,
                        expiration_date     DATE,
                        PRIMARY KEY (uid)
                    )
                            """)
            except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return False
            finally:
                cursor.close()
        finally:
            conn.close()

    return True

def CreateTask(data):
    pass


#print prepareDatabase()
print prepareTables()
