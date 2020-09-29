from socket import *
import sys 
import os

def isChar(string, index):
    if (string[index].isdigit() or string[index].isalpha()):
        return True
    return False


def isSpecial(string, index):
    if (string[index].isdigit() or string[index].isalpha()):
        return False
    elif (string[index] == '<' or string[index] == '>' or string[index] == '(' or string[index] == ')' or string[index] == '['
            or string[index] == ']' or string[index] == '\\' or string[index] == '.' or string[index] == ',' or string[index] == ';'
            or string[index] == ':' or string[index] == '@' or string[index] == '"' or string[index] == ' ' or string[index] == '\t' or string[index] == '\n'):
        return True
    return False

def element(string, index):
    if (not string[index].isalpha()):
        return -1
    while (index < len(string)):
        if not isChar(string, index):
            return index
        index += 1
    return -1

def domain(string, index):
    while index < len(string):
        index = element(string, index)
        if (index == -1):
            print("element")
            return -1
        elif (string[index] == '.'):
            index += 1
        else:
            return index
    return -1

def localpart(string, index):
    if string[index] == '@':
        return -1
    while index < len(string):
        if (isSpecial(string, index)):
            return index
        else:
            index += 1
    return -1

def mailbox(string, index):
    index = localpart(string, index)
    if (index == -1):
        return -1
    if (string[index] != '@'):
        return -1
    index = domain(string, index + 1)
    if (index == -1):
        return -1
    return index

def checkEmail(string):
    string = string.strip(' \t')
    string = mailbox(string, 0)
    
    return string != -1

def checkMultiple(string):
    strings = string.split(',')

    i = 0
    while i < len(strings) - 1:
        if (not checkEmail(strings[i] + '\n')):
            return False
        i += 1
    if (not checkEmail(strings[-1])):
        return False
    return True

def getBodyMessages(send_address, recipients, sub, bod):
    messages = []

    messages.append("From: <" + send_address[:-1] + ">\n")
    receiver_section = "To: "

    i = 0
    while i < len(recipients):
        receiver_section += "<" + recipients[i] + ">, "
        i += 1

    messages.append(receiver_section[0:len(receiver_section)-2] + '\n')
    messages.append("Subject: " + sub)
    messages.append("MIME-Version: 1.0\n")
    messages.append("Content-Type: multipart/mixed; boundary=tcntoun\n")
    messages.append('\n')
    messages.append("--tcntoun\n")
    messages.append("Content-Transfer-Encoding: quoted-printable\n")
    messages.append("Content-Type: text/plain\n")
    messages.append("\n")
    messages.append(bod)
    messages.append("--tcntoun\n")
    messages.append("Content-Transfer-Encoding: base64\n")
    messages.append("Content-Type: image/jpeg\n")
    messages.append("\n")
    # messages.append("base64 encoded data ")
    # myfile = open(img, 'rb')
    # size = myfile.read()
    # messages.append(str(size))
    # messages.append("base64 encoded data\n")
    # messages.append("\n--tcntoun--\n")
    # messages.append(".\n")
    return messages

# Client

while True:
    if (len(sys.argv) < 3):
        sys.stdout.write("Need server name port number\n")
        sys.exit()

    server = sys.argv[1]
    port = int(sys.argv[2])


    # From message
    sender = ""

    while True:
        sys.stdout.write("From:\n")

        sender = sys.stdin.readline()

        ex = checkEmail(sender)
        
        if (not ex):
            sys.stdout.write("Invalid email, try again\n")
            continue
        else:
            break
    
    sender = sender.strip(' \t')

    # To message(s)
    receivers = ""

    while True:
        sys.stdout.write("To:\n")

        receivers = sys.stdin.readline()

        if (not checkMultiple(receivers)):
            sys.stdout.write("Invalid email(s), try again\n")
            continue
        else:
            break

    receivers = [addr.strip(' \n\t') for addr in receivers.split(',')]

    # Subject message
    sys.stdout.write("Subject:\n")

    subject = sys.stdin.readline()

    # Attachment message
    sys.stdout.write("Attachment:\n")
    image = sys.stdin.readline()

    # Data section
    sys.stdout.write("Message:\n")

    data = ""

    while True:
        msg = sys.stdin.readline()

        if (msg == ".\n"):
            break
        else:
            data += msg

    # Establish connection
    socket_connection = socket(AF_INET, SOCK_STREAM)

    tryagain = True

    while tryagain:
        try:
            sys.stdout.write("Establishing connection...\n")
            tryagain = False
            socket_connection.connect((server, port))
        except:
            sys.stdout.write("Failed to connect\n")
            sys.stdout.write("Try again? (yes/no)\n")
            user = sys.stdin.readline()
            user = user.strip(' \n\t')
            user = user.lower()
            if user == "yes":
                tryagain = True
            else:
                sys.exit()

    # Receive greeting
    greet_msg = socket_connection.recv(1024).decode()
    sys.stdout.write("Server: " + greet_msg)

    # Send HELO message
    helo = "HELO " + gethostname() + '\n'
    sys.stdout.write("Client: " + helo)
    socket_connection.send(helo.encode())

    # Receive connection response
    admit_message = socket_connection.recv(1024).decode()
    sys.stdout.write("Server: " + admit_message)

    # Send From: message
    mailfrom_message = "MAIL FROM: <" + sender[:-1] + ">\n"
    sys.stdout.write("Client: " + mailfrom_message)
    socket_connection.send(mailfrom_message.encode())

    mailfrom_response = socket_connection.recv(1024).decode()
    sys.stdout.write("Server: " + mailfrom_response)
    
    # Send To: message
    receiver_messages = []

    for r in receivers:
        receiver_messages.append("RCPT TO: <" + r[:len(r)] + ">\n")

    i = 0
    while i < len(receiver_messages):
        sys.stdout.write("Client: " + receiver_messages[i])
        socket_connection.send(receiver_messages[i].encode())

        receiver_response = socket_connection.recv(1024).decode()
        sys.stdout.write("Server: " + receiver_response)
        i += 1

    # Send Data
    data_message = "DATA \n"

    sys.stdout.write("Client: " + data_message)
    socket_connection.send(data_message.encode())

    data_response = socket_connection.recv(1024).decode()
    sys.stdout.write("Server: " + data_response)

    body_messages = getBodyMessages(sender, receivers, subject, data)

    for dataMessage in body_messages:
        sys.stdout.write("Client Message: " + dataMessage)
        socket_connection.sendall(dataMessage.encode())

    temp = "base64 encoded data... "
    socket_connection.sendall(temp.encode())
    data = open(image[:-1], 'rb').read()
    socket_connection.sendall(data)
    temp = "\n"
    socket_connection.sendall(temp.encode())
    temp = "...base64 encoded data\n"
    socket_connection.sendall(temp.encode())
    temp = "--tcntoun--\n"
    socket_connection.sendall(temp.encode())
    temp = ".\n"
    socket_connection.sendall(temp.encode())


        # resp = socket_connection.recv(1024).decode()
        # sys.stdout.write("Server Response: " + resp)

    #i = 0
    #while i < len(body_messages):
    #    sys.stdout.write("Message Sent: " + body_messages[i])
    #    socket_connection.send(body_messages[i].encode())
    #    i += 1

    ### data_end = ".\n"
    ### socket_connection.send(data_end.encode())

    data_response = socket_connection.recv(1024).decode()
    sys.stdout.write("Server: " + data_response)

    # QUIT message
    quit_message = "QUIT\n"
    sys.stdout.write("Client: " + quit_message)

    socket_connection.send(quit_message.encode())

    quit_response = socket_connection.recv(1024).decode()
    sys.stdout.write("Server: " + quit_response)

    socket_connection.close()
    sys.exit(0)

