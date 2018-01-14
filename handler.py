import database
import json
import traceback
import webapp_socket
import wearable_socket
from utils import log

class Handler:
    def __init__(self, webapp_server, wearable_server, database_connection):
        self.webapp_server = webapp_server
        self.wearable_server = wearable_server
        self.database_connection = database_connection
    
    
    
    def webapp(self):
        raw_data = self.webapp_server.queue.get()
        
        try:
            data = json.loads(raw_data)
            
            if 'is_coming' in data:
                self.database_connection.update_fall(data['id'], data['is_coming'])
                self.wearable_server.send_one(self.database_connection.get_mac_address(data['id']), json.dumps({ 'is_coming': data['is_coming'] }))
                
                if data['is_coming']:
                    self.webapp_server.send_all(json.dumps({ 'status': 1000, 'id': data['id'] }))
                else:
                    self.webapp_server.send_all(json.dumps({ 'status': 1002, 'id': data['id'], 'is_coming': data['is_coming'] }))
        except ValueError:
            log('[MAIN] JSON failed: ' + raw_data)
            pass
        except:
            log(traceback.format_exc())
    
    
    
    def wearable(self):
        raw_data = self.wearable_server.queue.get()
        
        self.wearable_server.send_all("hallo")
        
        try:
            data = json.loads(raw_data)
            
            if not 'mac_address' in data:
                return
            
            resident_id = self.database_connection.get_id(data['mac_address'])
            
            if 'is_fallen' in data and data['is_fallen']:
                self.database_connection.add_fall(resident_id)
                self.webapp_server.send_all(json.dumps({ 'status': 1001, 'id': resident_id, 'is_fallen': True }))
            
            if 'low_battery' in data:
                self.database_connection.update_battery(data['mac_address'], data['low_battery'])
                self.webapp_server.send_all(json.dumps({ 'status': 1003, 'id': resident_id, 'low_battery': data['low_battery'] }))
        except ValueError:
            log('[MAIN] JSON failed: ' + raw_data)
            pass
        except:
            log(traceback.format_exc())
