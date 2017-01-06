import socket
import sys
import time
import copy
import smtplib
import csv
import itertools
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sqlite3
import os.path
import os





######

# upon call, sends email to the email list defined below
# with the tags that have disappeared/been found.

def emailNotification(foundTags, lostTags, date, hour):
    if foundTags:
        message = (""" \'Hello.\nTag(s) {} have been found in the lab at {} on {}!\nPlease check the csv file or database for more details.\n\nThis is an automated email, please do not respond to this.\'""").format(list(foundTags), hour, date)
    if lostTags:
        message = (""" \'Hello.\nTag(s) {} have been lost in the lab at {} on {}!\nPlease check the csv file or database for more details.\n\nThis is an automated email, please do not respond to this. \'""").format(list(lostTags), hour, date)
    emailList = """tim.durkin@stfc.ac.uk kristian.harder@stfc.ac.uk"""
    #emailList = """niall.mulkerns@stfc.ac.uk"""
    os.system("echo " + str(message) + " | mail -s 'Alert' -a 'From: Lab 6 Tracker <lab6tracker@stfc.ac.uk>' " + emailList)
    #print ("echo " + str(message) + " | mail -s 'Alert' -a "From: Lab 6 Tracker <lab6tracker@stfc.ac.uk> " + emailList)



######

# timer that calculates when a tag has been lost for a certain amount of time
# then returns a list of tags that are lost (in 'limbo').

def timer(checkLost):
    baseDir = os.path.dirname(os.path.abspath(__file__))
    dbPath = os.path.join(baseDir, "TagDatabase.db")
    connection = sqlite3.connect(dbPath) #gets the path of the database and connects to it.
    #print dbPath

    for i in checkLost:

        hour_cmd = ('SELECT [Time Last Seen] FROM Inventory WHERE Tag = "{}"'.format(i))
        for row in connection.execute(hour_cmd):
            #print row[0]
            last_hour = row[0] #getting hour data from database.

            date_cmd = ('SELECT [Date Last Seen] FROM Inventory WHERE Tag = "{}"'.format(i))
        for row in connection.execute(date_cmd):
            #print row[0]
            last_date = row[0] #getting date data from database

            date_time = last_date + " " + last_hour
            print date_time

        pattern = "%d/%m/%Y %H:%M:%S"
        last_time=int(time.mktime(time.strptime(date_time, pattern)))

        #print (last_time/float(60*60*24*365)

        #print last_time
        cutOff = 300 #number of seconds before a tag is declared lost. #300 (5 min) seems a good time.
        print "{} has been lost for {} seconds!".format(i,(time.time() - last_time))



        if (time.time() - last_time) > cutOff:
            #print "{} is more than {} mins!".format(time.time()-last_time, 1.0*cutOff/60)
            print "{} has been lost! Notifying....".format(i)
            emailNotification([],[i],last_date, last_hour)
            if i in checkLost:
                checkLost.remove(i)
                #print "{} deleted from checkLost!\n".format(i)
                #print checkLost
            else:
                pass
            #print "ERROR: {} not in checkLost!\n".format(i)

        #pass
        else:
            pass
            if i not in checkLost:
                checkLost.append(i)
                print "{} added to list\n".format(i)
    return checkLost


######





# main data collecting loop. Gets data from the reader and performs some sorting/analysis
# on it, getting it into neat forms. Only stores one 'get tag' read worth of data. For more information,
# on how the data is presented, try out the bundled reader interface software. 


def dataLoop(s,tagList,previousTagList):
    #This is the time between cycles and taglist calls.
    #Small correlation between cycle time and strength of detection. 
    sleepTime = 20
    time.sleep(sleepTime)
    
    countList=[]
    tagMessage = "get taglist\n"
    try:
        s.sendall(tagMessage) #tells reader to call taglist.
    except socket.error:
        print ('Send failed') #if it fails, raise errror and exit.
        sys.exit()
    data = s.recv(2**13) #open a continuous data recieve.
    
    #print data
    cutData=data[12:-6] #gets rid of unwanted strings.
    #print cutData
    
    splitLines=[]

    #splits the data into array separated by the newline character.
    splitLines=cutData.split('\n')  # --> ['Line 1', 'Line 2', 'Line 3']
    #print splitLines
    
    global hour, date, count
    print "\nTags Seen \t \t \t \t Counts\n---------------------------------------------------------"
    for i in splitLines: #for each new tag (splitting tags)
        subSplitLines=[i] #make new list
        #print 'subsplitlines:',subSplitLines
        
        tag = i[4:33] #part of the string we need for tag data.
        if tag and (tag.startswith("E") or tag.startswith("201")): #confirming it is a tag.
            date = i[40:50]
            hour = i[50:59] 
            counts = i[93:99] #slicing parts of the string containing correct data.

            
            count = ''.join([j for j in counts if j.isdigit()]) #shows how many times reader has made contact with tag since last call.
            #print "tag {} {}\n".format(date, hour)
            
            print ("Tag = {} \t count = {}\n".format(tag,count))
            
            countList.append(count)
        else:
            hour = time.strftime("%H:%M:%S") #not optimal using 2 different time standards.
            date = time.strftime("%d/%m/%Y")
           
            #print "clock {} {}\n".format(date, hour)
            


        #print 'tag=',tag
        if tag.startswith("E") or tag.startswith("201"): #to ensure genuine tag data.
            tagList.append(tag) #adds to list of tags found in this taglist call.
    if not tagList:
         countList.append(0)
            
    print ("\nNumber of tags found = {}".format(len(tagList))) #number of tags found = length of taglist.
    
    
    difference=set(tagList)^set(previousTagList) #looks to see if anything has changed between the two lists.
    foundTags = set(tagList)-set(previousTagList)
    lostTags = set(previousTagList)-set(tagList) #set operators are slightly different - look them up for more info.
    
    
    if difference and (tagList or previousTagList): #if diff != 0 and one of the taglists also != 0 then...
        #print ("\n\nSomething has changed at {} on {}! Difference: {} \n\n".format(hour, date, list(difference)))
        if lostTags:
            #time.sleep(0.01) #placeholder
            print ("Tags {} have been lost from view at {}!".format(list(lostTags), hour))
        elif foundTags:
            #time.sleep(0.01) #placeholder
            print ("Tags {} have been found at {}!".format(list(foundTags), hour))
            emailNotification(foundTags, [], date, hour) #triggers email notification of what has been found.
        #print "something changed"
    

    print ("\n\n")
    updater(tagList, date, hour, foundTags, lostTags) #triggers updater to update the database and .csv files.

    
    return  tagList, previousTagList, date, hour, lostTags, foundTags, countList





######


# opens up the SQLite3 database, updates the variables that need to be, closes file.
# copies the database to a .csv file which is easier to handle.


def updater(tagList, date, hour, foundTags, lostTags):

    baseDirectory = os.path.dirname(os.path.abspath(__file__))
    dbPath = os.path.join(baseDirectory, "TagDatabase.db")
    connection = sqlite3.connect(dbPath) #gets the path of the database and connects to it.
    #print (dbPath)


    cursor = connection.cursor() #defines cursor to the database.
    connection.text_factory = str
    dbTagList=[]
    
    
    for row in cursor.execute("SELECT Tag FROM Inventory"):
        dbTagList.append(row[0]) #gets the known taglist from the database.


    #defines a new taglist containing all those tags that are in both the database and current taglist.
    matching = [] 
    matching = list(set(tagList).intersection(set(dbTagList)))
    #print "matching = {}".format(matching)
    
    for i in tagList: #loop over taglist from reader.
        if i not in matching: #if it's not in database, create entry for it.
            #print "got here"
            cmd = ("""INSERT INTO Inventory VALUES('{}','{}','{}', '{}', '{}')
                    """.format(i,time.strftime("%d/%m/%Y"),time.strftime("%H:%M:%S"), "Yes", "NULL"))
            connection.execute(cmd) #execute command in database


##    if lostTags:    
##        for i in lostTags: #if tag is lost then set 'visible' field of tag to NO.
##            print ("lostTags")
##            cmd = ("""UPDATE Inventory SET 'Visible' = 'NO'
##                        WHERE Tag = '{}'""".format(i))
##            connection.execute(cmd) 


    if foundTags:    
        for i in foundTags: #if tag is found then set 'visible' field of tag to YES.
            #print ('foundTags')
            do = ("""UPDATE Inventory SET 'Visible' = 'YES'
                        WHERE Tag = '{}'""".format(i))
            connection.execute(do)
    

       
    for i in matching: #if tag in both reader taglist and database then update it's last seen time.
        
        todo = ("""UPDATE Inventory SET 'Time Last Seen'
                    = '{}', 'Date Last Seen' = '{}'
                    WHERE Tag = '{}'""".format(time.strftime("%H:%M:%S"),time.strftime("%d/%m/%Y"),i))
        #print todo
        connection.execute(todo) 
    
    
    connection.commit() #commit to the changes which can't be undone.


    baseDir = os.path.dirname(os.path.abspath(__file__))
    csvPath = os.path.join(baseDir, "database.csv") #getting the path to the csv file.
    #print (csvPath)

    
    csvData = cursor.execute("""SELECT * FROM Inventory ORDER BY Visible DESC""") #gets all data from database.

    
    with open(csvPath, 'wb') as databaseCsv:
        databaseWriter = csv.writer(databaseCsv, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        databaseWriter.writerow(["Tag" , "Date Last Seen" ,"Time Last Seen", "Visible", "Product"])
        for row in csvData:
            databaseWriter.writerow(row) #prints copied data from database to csv.
            
            

    
    connection.close() #close connection to database.
    





#####







###### Start of code.

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    #create an AF_INET, STREAM socket (TCP)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #try to create socket to machine.
except socket.error, msg:
    print ('Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]) #raises error if it fails
    sys.exit();                                                                                    #and exits system.

print ('socket created!')

remote_ip = '130.246.42.7' #ip address of the Alien reader.
port = 23 #port of Alien reader.
s.connect((remote_ip , port)) #use the socket to connect to the reader.

print ('socket connected to IP ' + remote_ip)


#giving reader the basic instructions needed:
message = ("""alien\npassword\n """) #this is the password needed to access the reader.
try :
    s.sendall(message) #try to send the instructions to reader.
except socket.error:
    print ('Send failed.') #if it fails, raise errror and exit.
    sys.exit()

message = ("""antennasequence=0,1\n
             acquiremode=inventory\n
             taglistantennacombine=on\n
             notifyaddress=130.246.41.39:80\n
             notifytrigger=change\n
             persisttime=-1\n
             acqg2count=2\n
             acqg2q=3\n
             acqg2cycles=30\n""") #settings for the reader, look in the user guides for more info.
             #notifymode=on\n
             #automode=on\n"""
 
try :
    s.sendall(message) #try to send the instructions to reader.
    print ('send succeeded!')
except socket.error:
    print ('Send failed.') #if it fails, raise errror and exit.
    sys.exit()
 
print ('Message sent successfully.') 

reply = s.recv(2**13) #use socket to recieve reply from the reader.
 
#print reply


open("data","w").close() #opens up data and then closes it to erase the contents.
    
tagList=[]
previousTagList=[]
countList=[]
checkLost=[]

while (True): #looping over infinite calls of 'taglist'...
#for i in range (180):
    #print "i = {}".format(i)
    tagList, previousTagList, date, hour, lostTags, foundTags,countList = dataLoop(s,tagList,previousTagList) #starts the data mining process and returns variables needed for analysis.
    #print tagList
    union = list(set(checkLost).union(set(lostTags)))
    diff = list(set(union).difference(set(tagList)))
    #print "diff = {}".format(diff)
    #print "union = {}".format(diff)
    if diff:
        checkLost=timer(diff)
    else:
        #print "checkList empty!"
        pass
    
    with open(r'data', 'ab') as csvFile: #appending to data file in form of csv.
        dataWriter = csv.writer(csvFile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        dataWriter.writerow(["Tag List", "Counts Registered", "Lost Tags", "Found Tags","Time Last Seen","Date Last Seen"]) #writes data to excel file (csv).

        
        for i in itertools.izip_longest(tagList,countList,lostTags,foundTags, [hour], [date]): #zips the columns together and then prints them to the file.
            dataWriter.writerow(i)
            
    #if not checkLost:
        #print "checkLost empty!\n"
            
    del previousTagList[:]
    previousTagList=copy.copy(tagList)
    del tagList[:]
    del lostTags
    del foundTags
    del countList #resetting the lists for the next run.

 
s.close()
sys.exit()


##### end of code -- functions above.

