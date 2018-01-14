import mysql.connector as mariadb
import time

class Database:
    def __init__(self):
        self.connection = mariadb.connect(host='145.132.98.80', user='valiets', password='********', database='valiets_db', port=54432)
        self.cursor = self.connection.cursor()
    
    
    
    def get_all_residents(self):
        resident_data = []
        
        self.cursor.execute('SELECT * FROM `residents`;')
        residents = self.cursor.fetchall()
        
        for resident in residents:
            resident_data.append(( resident[0], resident[1], resident[2], resident[3], resident[4], resident[5] ))
        
        return resident_data
    
    
    
    def get_newest_wearable(self, resident_id):
        self.cursor.execute('SELECT * FROM `resident_wearables` WHERE `resident_id`=%s;', ( resident_id, ))
        wearables = self.cursor.fetchall()
        
        if len(wearables) > 0:
            return wearables[-1]
        
        return None
    
    
    
    def get_id(self, mac_address):
        self.cursor.execute('SELECT * FROM `resident_wearables` WHERE `mac_address`=%s;', ( mac_address, ))
        row = self.cursor.fetchone()
        
        return row[1]
    
    def get_mac_address(self, resident_id):
        wearable = self.get_newest_wearable(resident_id)
        
        if wearable:
            return wearable[2]
        else:
            return None
    
    
    
    def update_battery(self, mac_address, status):
        self.cursor.execute('UPDATE `resident_wearables` SET `battery_low`=%s WHERE `mac_address`=%s;', ( int(status), mac_address ))
        self.connection.commit()
    
    
    
    def get_status(self, resident_id):
        self.cursor.execute('SELECT * FROM `resident_falls` WHERE `resident_id`=%s AND `finished_time` IS NULL;', ( resident_id, ))
        falls = self.cursor.fetchall()
        
        status = 0
        
        if len(falls) > 0:
            if falls[-1][3] is None:
                status = 1
            else:
                status = 2
        
        return status
    
    def add_fall(self, resident_id):
        if self.get_status(resident_id) == 0:
            self.cursor.execute('INSERT INTO `resident_falls` ( `resident_id`, `fall_time` ) VALUES ( %s, %s );', ( resident_id, time.strftime('%Y-%m-%d %H:%M:%S') ))
            self.connection.commit()
    
    def update_fall(self, resident_id, coming):
        if coming:
            self.cursor.execute('UPDATE `resident_falls` SET `response_time`=%s WHERE `resident_id`=%s ORDER BY `id` DESC LIMIT 1;', ( time.strftime('%Y-%m-%d %H:%M:%S'), resident_id ))
        else:
            self.cursor.execute('UPDATE `resident_falls` SET `finished_time`=%s WHERE `resident_id`=%s ORDER BY `id` DESC LIMIT 1;', ( time.strftime('%Y-%m-%d %H:%M:%S'), resident_id ))
        
        self.connection.commit()
