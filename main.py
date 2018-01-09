#!/usr/bin/python3.6

import database
import handler
import sys
import threaded_server
import time
import webapp_socket
import wearable_socket

if __name__ == '__main__':
    ip_addr = '192.168.2.152'
    
    print('[MAIN] Connecting to database')
    database_connection = database.Database()
    
    print('[MAIN] Starting WebApp Server')
    webapp_server = threaded_server.ThreadedServer(ip_addr, 51030, database_connection, webapp_socket.WebAppSocket)
    webapp_server.start()
    
    print('[MAIN] Starting Wearable Server')
    wearable_server = threaded_server.ThreadedServer(ip_addr, 24192, database_connection, wearable_socket.WearableSocket)
    wearable_server.start()
    
    print('[MAIN] Setting up handlers')
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
