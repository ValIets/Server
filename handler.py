import database
import json
import webapp_socket
import wearable_socket

class Handler:
    def __init__(self, webapp_server, wearable_server, database_connection):
        self.webapp_server = webapp_server
        self.wearable_server = wearable_server
        self.database_connection = database_connection
    
    
    
    def webapp(self):
        raw_data = self.webapp_server.queue.get()
        
        try:
            data = json.loads(raw_data)
            
            if 'coming' in data:
                self.database_connection.update_fall(data['id'], data['coming'])
                self.webapp_server.send_all(json.dumps({ 'id': data['id'], 'coming': data['coming'] }))
                self.wearable_server.send_one(self.database_connection.get_mac_address(data['id']), json.dumps({ 'coming': data['coming'] }))
        except:
            pass
    
    
    
    def wearable(self):
        raw_data = self.wearable_server.queue.get()
        
        try:
            data = json.loads(raw_data)
            
            if not 'mac_address' in data:
                return
            
            resident_id = self.database_connection.get_id(data['mac_address'])
            
            if 'fallen' in data and data['fallen']:
                self.database_connection.add_fall(resident_id)
                self.webapp_server.send_all(json.dumps({ 'id': resident_id, 'fallen': True }))
            
            if 'low_battery' in data:
                self.database_connection.update_battery(data['mac_address'], data['low_battery'])
                self.webapp_server.send_all(json.dumps({ 'id': resident_id, 'low_battery': data['low_battery'] }))
        except:
            pass
