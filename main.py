#!/usr/bin/python3.4

import database
import handler
import sys
import threaded_server
import time
import traceback
import webapp_socket
import wearable_socket
from utils import log

if __name__ == '__main__':
    ip_addr = '192.168.2.24'
    
    log('[MAIN] Connecting to database')
    database_connection = database.Database()
    
    log('[MAIN] Starting WebApp Server')
    webapp_server = threaded_server.ThreadedServer(ip_addr, 51030, database_connection, webapp_socket.WebAppSocket)
    webapp_server.start()
    
    log('[MAIN] Starting Wearable Server')
    wearable_server = threaded_server.ThreadedServer(ip_addr, 24192, database_connection, wearable_socket.WearableSocket)
    wearable_server.start()
    
    log('[MAIN] Setting up handlers')
    server_handler = handler.Handler(webapp_server, wearable_server, database_connection)
    
    while True:
        try:
            if not webapp_server.queue.empty():
                server_handler.webapp()
            
            if not wearable_server.queue.empty():
                server_handler.wearable()
            
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            log(traceback.format_exc())
