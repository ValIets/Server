f = open('server.log', 'w')
def log(msg):
    print(msg)
    print(msg, file=f)
    f.flush()
