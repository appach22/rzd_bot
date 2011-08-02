
import db

db = db.db()

db.query("SELECT * FROM bot_dynamic_info")

for row in db.rows:
    if db.query("SELECT * FROM obsolete_static_info WHERE uid = %d" % row[0]):
        if len(db.rows):
            row = db.rows[0]
            car_type = int(row[16])
            places_range_low = row[13]
            if places_range_low == None:
                places_range_low = 1
            places_range_high = row[14]
            if places_range_high == None:
                places_range_high = 120
            places_parity = row[15]
            if places_parity == None:
                places_parity = 3
            date = row[7]
            if row[8] != None and len(row[8]):
                trains = row[8].split(',')
                for train in trains:
                    db.query("""INSERT INTO trains
                        (uid, number, date, car_type, places_parity,
                         places_range_low, places_range_high, prev, total_prev)
                        VALUES(%d, '%s', '%s', %d, %d, %d, %d, %d, %d)""" % \
                        (row[0], train, date.strftime("%Y-%m-%d"),
                        car_type, places_parity, places_range_low,
                        places_range_high, 0, 0))
            date = row[9]
            if row[10] != None and len(row[10]):
                trains = row[10].split(',')
                for train in trains:
                    db.query("""INSERT INTO trains
                        (uid, number, date, car_type, places_parity,
                         places_range_low, places_range_high, prev, total_prev)
                        VALUES(%d, '%s', '%s', %d, %d, %d, %d, %d, %d)""" % \
                        (row[0], train, date.strftime("%Y-%m-%d"),
                        car_type, places_parity, places_range_low,
                        places_range_high, 0, 0))
            date = row[11]
            if row[12] != None and len(row[12]):
                trains = row[12].split(',')
                for train in trains:
                    db.query("""INSERT INTO trains
                        (uid, number, date, car_type, places_parity,
                         places_range_low, places_range_high, prev, total_prev)
                        VALUES(%d, '%s', '%s', %d, %d, %d, %d, %d, %d)""" % \
                        (row[0], train, date.strftime("%Y-%m-%d"),
                        car_type, places_parity, places_range_low,
                        places_range_high, 0, 0))
                    

