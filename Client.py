from socket import *
import sys 
import os

def errorMessage(error):
    sys.stdout.write("ERROR -- " + error + '\n')
    return

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
        errorMessage("mailbox")
        return -1
    if (string[index] != '@'):
        errorMessage("mailbox")
        return -1
    index = domain(string, index + 1)
    if (index == -1):
        errorMessage("domain")
        return -1
    return index

def checkMailFrom(string):
    string = string.strip(' \t')
    string = mailbox(string, 0)

    return string != -1


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
    messages.append('\n')
    messages.append(bod)
    messages.append(".\n")
    return messages

# Client

while True:
    if (len(sys.argv) < 3):
        sys.stdout.write("Need server name and port number\n")
        sys.exit()

    server = sys.argv[1]
    port = int(sys.argv[2])


    # From message
    sender = ""

    while True:
        sys.stdout.write("From:\n")

        sender = sys.stdin.readline()

        check = [addr.strip('\n\t') for addr in sender.split(',')]
        if len(check) > 1:
            sys.stdout.write("ERROR -- domain\n")
            continue

        ex = checkMailFrom(sender)
        
        if (not ex):
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
            continue
        else:
            break

    receivers = [addr.strip(' \n\t') for addr in receivers.split(',')]

    # Subject message
    sys.stdout.write("Subject:\n")

    subject = sys.stdin.readline()

    # Data section
    sys.stdout.write("Message:\n")

    data = ""
    f = True
    while True:
        msg = sys.stdin.readline()

        if (msg == '.\n' and f):
            data += msg
            break
        elif (msg == ".\n"):
            # data += msg
            break
        else:
            data += msg
        f = False

    # Establish connection
    socket_connection = socket(AF_INET, SOCK_STREAM)

    tryagain = True

    while tryagain:
        try:
            # sys.stdout.write("Establishing connection...\n")
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
    if greet_msg[0:3] != "220":
        sys.stderr.write(greet_msg)
        socket_connection.close()
        sys.exit(-1)

    # Send HELO message
    helo = "HELO " + gethostname() + '\n'
    socket_connection.send(helo.encode())

    # Receive connection response
    admit_message = socket_connection.recv(1024).decode()
    if admit_message[0:3] != "250":
        sys.stderr.write(admit_message)
        socket_connection.close()
        sys.exit(-1)

    # Send From: message
    mailfrom_message = "MAIL FROM: <" + sender[:-1] + ">\n"
    socket_connection.send(mailfrom_message.encode())

    mailfrom_response = socket_connection.recv(1024).decode()
    if mailfrom_response[0:3] != "250":
        sys.stderr.write(mailfrom_response)
        sys.exit(-1)
    
    # Send To: message
    receiver_messages = []

    for r in receivers:
        receiver_messages.append("RCPT TO: <" + r[:len(r)] + ">\n")

    i = 0
    while i < len(receiver_messages):
        socket_connection.send(receiver_messages[i].encode())

        receiver_response = socket_connection.recv(1024).decode()
        if receiver_response[0:3] != "250":
            sys.stderr.write(receiver_response)
        i += 1

    # Send Data
    data_message = "DATA \n"

    socket_connection.send(data_message.encode())

    data_response = socket_connection.recv(1024).decode()
    if data_response[0:3] != "354":
        sys.stderr.write(data_response)
        socket_connection.close()
        sys.exit(-1)

    body_messages = getBodyMessages(sender, receivers, subject, data)

    resp = ""
    for dataMessage in body_messages:
        socket_connection.send(dataMessage.encode())

        resp = socket_connection.recv(1024).decode()

    #i = 0
    #while i < len(body_messages):
    #    sys.stdout.write("Message Sent: " + body_messages[i])
    #    socket_connection.send(body_messages[i].encode())
    #    i += 1

    if resp[0:3] != "250":
        data_end = ".\n"
        socket_connection.send(data_end.encode())

        data_response = socket_connection.recv(1024).decode()
        if data_response[0:3] != "250":
            sys.stderr.write(data_response)
            socket_connection.close()
            sys.exit(-1)

    # QUIT message
    quit_message = "QUIT\n"

    socket_connection.send(quit_message.encode())

    quit_response = socket_connection.recv(1024).decode()
    if quit_response[0:3] != "221":
        sys.stderr.write(quit_response)
        socket_connection.close()
        sys.exit(-1)

    socket_connection.close()
    sys.exit(0)

