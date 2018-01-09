import queue
import socket
import threading
import traceback

class ThreadedSocket(threading.Thread):
    def __init__(self, queue, parent_queue, connection, database_connection):
        threading.Thread.__init__(self)
        
        self.queue = queue
        self.parent_queue = parent_queue
        self.connection = connection
        self.database_connection = database_connection
        self.identifier = None
        
        self.address = self.connection.getpeername()
    
    def run(self):
        pass

class ThreadedServer(threading.Thread):
    def __init__(self, host, port, database_connection, socket_type):
        threading.Thread.__init__(self)
        
        self.host = host
        self.port = port
        self.database_connection = database_connection
        self.socket_type = socket_type
        
        self.threads = []
        self.queue = queue.Queue()
    
    def run(self):
        sock = socket.socket()
        sock.bind((self.host, self.port))
        sock.listen()
        
        print(vars(self.socket_type)['log_prefix'] + ' Server ready and listening')
        
        while True:
            try:
                connection, address = sock.accept()
                print(vars(self.socket_type)['log_prefix'] + ' New connection from ' + str(address[0]) + ':' + str(address[1]))
                
                thread = self.socket_type(queue.Queue(), self.queue, connection, self.database_connection)
                self.threads.append(thread)
                thread.start()
            except:
                traceback.print_exc()
    
    def send_all(self, msg):
        thread_count = len(self.threads)
        
        for i in range(thread_count):
            thread = self.threads[thread_count-1 - i]
            
            if thread.isAlive():
                thread.queue.put(msg)
            else:
                print(vars(self.socket_type)['log_prefix'] + ' Dropped connection from ' + str(thread.address[0]) + ':' + str(thread.address[1]))
                del self.threads[thread_count-1 - i]
    
    def send_one(self, identifier, msg):
        for i in range(len(self.threads)):
            thread = self.threads[len(self.threads)-1 - i]
            
            if vars(thread)['identifier'] == identifier:
                thread.queue.put(msg)
                return
