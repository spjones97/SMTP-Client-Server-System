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

def isDomain(string, index):
    while index < len(string):
        index = element(string, index)
        if (index == -1):
            return -1
        elif(string[index] == '.'):
            index += 1
        else:
            return index
    return -1
    

def nullspace(string, index):
    while (index < len(string)):
        if (string[index] == '\t' or string[index] == ' '):
            index += 1
        else:
            return index
    return -1

def whitespace(string, index):
    if (string[index] != ' ' and string[index] != '\t'):
        return -1
    return nullspace(string, index + 1)

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
        return 501
    if (string[index] != '@'):
        return 501
    index = isDomain(string, index + 1)
    if (index == -1):
        return 501
    return index

def path(string, index):
    if (string[index] != '<'):
        return 501
    index = mailbox(string, index + 1)
    if (index == 501):
        return 501
    if string[index] != '>':
        return 501
    out = index
    index = nullspace(string, index + 1)
    # if (string[index] != '\n'):
    #    print("3")
    #    return 501
    return out

def checkHELO(string):
    if (string[0:4] != "HELO"):
        return -1
    index = whitespace(string, 4)

    if (index == -1):
        return -1

    # Get domain start index
    dom_start = index

    index = isDomain(string, index)
    if (index == -1):
        return -1

    # Get domain last index
    dom_end = index

    index = nullspace(string, index)

    if index == -1 and string[index] != '\n':
        return -1

    return string[dom_start:dom_end]

def mailfrom(string):
    if (string[0:8] == "RCPT TO:" or string[0:4] == "DATA"):
        return 503
    if string[0:4] != "MAIL":
        return 500
    index = whitespace(string, 4)
    if (index == -1):
        return 500
    if (string[index:index + 5] != "FROM:"):
        return 500
    index = nullspace(string, index+5)
    out = path(string, index)
    if out == 501:
        return 501
    return string[index+1:out]

def getErrorMessage(num):
    if num == 500:
        return "500 Synax error: command unrecognized\n"
    elif num == 501:
        return "501 Syntax error in parameters or arguments\n"
    elif num == 503:
        return "503 Bad sequence of commands\n"

def rcptTo(string, first):
    if first and string[0:4] == "DATA":
        return 503
    if string[0:4] != "RCPT":
        if string[0:10] == "MAIL FROM:":
            return 503
        return 500
    index = whitespace(string, 4)
    if string[index:index + 3] != "TO:":
        return 500
    index = nullspace(string, index + 3)
    out = path(string, index)
    if out == 501:
        return 501
    return string[index+1:out]

def data(string):
    if string[0:4] != "DATA":
        if (string[0:4] == "MAIL"):
            return 503
        return 500
    index = nullspace(string, 4)
    if string[index] != '\n':
        return 500
    return 354

def checkMessage(string):
    if len(string) < 2:
        return string
    elif string[0] == '.' and string[1] == '\n':
        return 250

def logMessages(sending, receiving, messageData):
    msg = ""

    for mdata in messageData:
        msg += mdata

    domainArr = []

    for r in receiving:
        d = r[r.find('@')+1:]

        if d not in domainArr:
            domainArr.append(d)

    if not os.path.exists('forward'):
        os.system("mkdir forward")

    for d in domainArr:
        file = open('forward/' + d, 'a')
        file.write(msg)

# Server

while True:
    if (len(sys.argv) != 2):
        sys.stdout.write("Need port number\n")
        sys.exit()

    port = int(sys.argv[1])

    socket_server = socket(AF_INET, SOCK_STREAM)
    socket_server.bind(('', port))
    
    while True:
        socket_server.listen(1)
        socket_connection, addr = socket_server.accept()

        # Send greeting message
        message = "220 " + gethostname() + '\n'
        # sys.stdout.write("Server: " + message)
        socket_connection.send(message.encode())

        while True:
            hello_message = socket_connection.recv(1024).decode()
            # sys.stdout.write("Client: " + hello_message)
            domain = checkHELO(hello_message)
            if (domain == -1):
                continue
            # Send confirm message
            message = "250 " + domain + " pleased to meet you\n"
            # sys.stdout.write("Server: " + message)
            socket_connection.send(message.encode())
            break

        sender = ""
        receivers = []
        messages = []

        while True:

            mail_from = socket_connection.recv(1024).decode()

            if mail_from:
                # sys.stdout.write("Client: " + mail_from)
                sender = mailfrom(mail_from)
                if (sender == 500 or sender == 501 or sender == 503):
                    err = getErrorMessage(sender)
                    socket_connection.send(err.encode())
                    continue
                message = "250 " + sender + " Sender ok\n"
                # sys.stdout.write("Server: " + message)
                socket_connection.send(message.encode())
                first = True
                
                while True:
                    rcpt_to = socket_connection.recv(1024).decode()

                    if (first):
                        # sys.stdout.write("Client: " + rcpt_to)
                        recipient = rcptTo(rcpt_to, first)
                        if recipient == 500 or recipient == 501 or recipient == 503:
                            err = getErrorMessage(recipient)
                            # sys.stdout.write("Server: " + err)
                            socket_connection.send(err.encode())
                            socket_connection.close()
                        else:
                            receivers.append(recipient)
                            msg = "250 " + recipient + " Recipient ok\n"
                            # sys.stdout.write("Server: " + msg)
                            socket_connection.send(msg.encode())
                            first = False
                    elif rcpt_to[0:4] == "RCPT":
                        # sys.stdout.write("Client: " + rcpt_to)
                        recipient = rcptTo(rcpt_to, first)
                        if recipient == 500 or recipient == 501 or recipient == 503:
                            err = getErrorMessage(recipient)
                            # sys.stdout.write("Server: " + err)
                            socket_connection.send(err.encode())
                            socket_connection.close()
                        else:
                            receivers.append(recipient)
                            msg = "250 " + recipient + " Recipient ok\n"
                            socket_connection.send(msg.encode())
                            continue
                    else:
                        data_tag = rcpt_to
                        # sys.stdout.write("Client: " + data_tag)
                        ex = data(data_tag)

                        if (ex == 500 or ex == 501 or ex == 503):
                            err = getErrorMessage(ex)
                            socket_connection.send(err.encode())
                            socket_connection.close()
                        
                        msg = "354 Start mail input; end with <CRLF>.<CRLF>\n"
                        # sys.stdout.write("Server " + msg)
                        socket_connection.send(msg.encode())

                        while True:
                            msg = socket_connection.recv(1024).decode()
                            # sys.stdout.write("Client Message: " + msg)
                            # sys.stdout.write("Message 0:[" + msg[0] + "] 1[" + msg[1] + "]\n")
                            out = "Received Data\n"
                            # sys.stdout.write("Server Response: " + out)

                            socket_connection.send(out.encode())
                        
                            if len(msg) > 1:
                                if msg[0] == "." and msg[1] == "\n":
                                    break
                            # socket_connection.send(out.encode())
                            # if temp[-1] == '\n' and temp[-2] == '.' and temp[-3] == '\n':
                                # break
                            messages.append(msg)
                        break
                        #i = 0
                        #while True:
                        #    bod = socket_connection.recv(1024).decode()
                        #    sys.stdout.write("Message: [" + str(i) + "] " + bod)
                        #    ex = checkMessage(msg)
                        #    i += 1
                        #    if bod[-1] == '\n' and bod[-2] == '.' and bod[-3] == '\n':
                        #        break
                        #    messages.append(bod)
                        #break
                # Send confirmation
                code_message = "250 OK\n"
                # sys.stdout.write("Server: " + code_message)
                socket_connection.send(code_message.encode())

                # Log messages
                msg = ""

                for m in messages:
                    msg += m

                domainArr = []

                for r in receivers:
                    d = r[r.find('@')+1:]
                    if d not in domainArr:
                        domainArr.append(d)

                if not os.path.exists('forward'):
                    os.system("mkdir forward")

                for d in domainArr:
                    file = open('forward/' + d, 'a')
                    file.write(msg)
        
                quit = socket_connection.recv(1024).decode()
                # sys.stdout.write("Client: " + quit)

                close_message = "221 " + gethostname() + " closing connection\n"
                # sys.stdout.write("Server: " + close_message)
                socket_connection.send(close_message.encode())
                socket_connection.close()
                break
