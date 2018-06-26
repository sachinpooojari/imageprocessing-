
import cv2
import csv
import sys
import time
import os 

import numpy as np
try:

    import Image
except ImportError:
    from PIL import Image
    
import pytesseract
from Adafruit_IO import Client
import pyocr
import pyocr.builders
from collections import deque


stack=deque([0,0,0,0])
flags={"KA 22 F 9805":1,"KA 22 F 9806":1,"KA 22 F 9807":1,"KA 22 A 2525":1,"KA 22 A 2527":1,"KA 22 B 1234":1}


aio = Client('ac75665fe8a14107bde9a138f2a4ec01')

test_number=["KA 22 F 9805","KA 22 F 9806","KA 22 F 9807","KA 22 A 2525","KA 22 A 2527","KA 22 B 1234"]

th=70

tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
# The tools are returned in the recommended order of usage
tool = tools[0]
print("Will use tool '%s'" % (tool.get_name()))
# Ex: Will use tool 'libtesseract'

langs = tool.get_available_languages()
print("Available languages: %s" % ", ".join(langs))
lang = langs[0]
print("Will use lang '%s'" % (lang))


def read(img):    
     txt = tool.image_to_string(
        
        Image.fromarray(img),
        #Image.open(img),
        lang=lang,
       
        builder=pyocr.builders.TextBuilder()
      )
     return txt


def cut(dilation):
    

    _,contours, hierarchy = cv2.findContours(dilation,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE) # get contours


# for each contour found, draw a rectangle around it on original image
    for contour in contours:
  # get rectangle bounding contour
        [x,y,w,h] = cv2.boundingRect(contour)
        rect=cv2.minAreaRect(contour)
        box=cv2.boxPoints(rect)
        
        box = np.int0(box)
        
        aspect=1
        try:
            aspect=float(w)/h
            #print aspect
        except :
            pass
        #  to check for aspect ration of number plate and lenth of lenth 
       # if (aspect>2.5 and aspect<3 ) and w>50 and  h<300  :
        if((aspect>3 and aspect<5) and h>10):
            
            global b
            b=box[0]
            cv2.drawContours(image,[box],0,(0,0,255),2)
            cx=int(x+w/2)
            cy=int(y+h/2)
            #print(ht,cy)
            # send the y axis value to stack and take the previous frame y axis value 

            stack.appendleft(cy)
            dir1=stack.pop()
            # check direction by prevous Y value - currunt Y value
            
                    #print(y,dir1)
            dir2=cy-dir1
            #print(stack,dir2)
                  
            if dir2>0:
                 pr="ARRIVEL"
            elif dir2<0:
                 pr="DEPARTURE"
            else:
                 pr="still"
                 
            #print(pr)
                 

            
            
            
            # print(aspect,w,h)
            
            roi = image[y:y + h, x:x + w]
            
            
            roi1 = cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
            kernel3 =np.ones((2,2),np.uint8)
   
            blur = cv2.blur(roi1,(2,2))
            #median = cv2.medianBlur(blur,3)
            _,roi1 = cv2.threshold(blur,th,255,cv2.THRESH_BINARY)
            cv2.imshow("plate",roi1)
            cv2.circle(image,(cx,cy), 3, (255,0,0), -1)
#_________________________________-
            
            pts_L1= np.array([[wt,0],[cx, cy]])
            pts_L2= np.array([[0,ht],[cx, cy]])
            frame = cv2.polylines( image, [pts_L1], True, (0,255,255),thickness=2)

            frame = cv2.polylines( image, [pts_L2], True, (0,255,255),thickness=2)
            
            #font = cv2.FONT_HERSHEY_SIMPLEX
            font=cv2.FONT_HERSHEY_SIMPLEX   
            txt=read(roi1)
           # print(txt)
            if (txt.startswith( 'KA' ) and (len(txt)>9 and len(txt )<14 )):
                
                try:
                    
                  
                    #enter(txt)
                    #txt="Number"
                   # print (txt)
                    
                    t=0;
                    if txt in  test_number:
                        #print("College bus ")
                                               
                        if ((pr=="ARRIVEL") and flags[txt]==1):#and (dirflag==1)):
                            
                          
                            t=enter(txt,"ARRIVEL")
                            flags[txt]=2
                            try:
                                aio.send('Numberplate', txt+" | ARRIVAL" )
                                pass
                            except Exception as e:
                               # print(e)
                                pass
                                    
                            print("TIME: ",t[1]," |DATE: ",t[2]," |ARRIVE : ",txt)
                        elif ((pr=="DEPARTURE")and flags[txt]==2):# and (dirflag==-1)):
                           
                            flags[txt]=1
                           
                            t=enter(txt,"DEPARTURE")
                            try:
                               aio.send('Numberplate', txt+" | DEPARTURE" )
                               pass
                            except Exception as e:
                                #print(e)
                                pass
                            print("TIME: ",t[1]," |DATE: ",t[2]," |DEPARTURE :",txt)
                   # else :
                    #    print("Visitors")
                     #   print(txt)
                   
                    cv2.putText(image,txt,(x-20,y-20), font, 1,(0,0,255),2)
                   # cv2.putText(image,pr,(x-50,y-50), font, 1,(255,255,0),1)
                except Exception as e:
                    print (e)
                    #print ("NONE")
                    pass

        
    return image 

i=0


def enter(number,status):
    global i,t
    global Time,date
 
    t=time.time()
    local=time.localtime(t)
    date=time.strftime('%I-%h-%Y')
    Time=time.strftime('%I:%M:%S:%p')

    
    
    with open('event.csv','a') as myfile:
        
        wr=csv.writer(myfile,dialect='excel')
        wr.writerow([i,Time,date,number,status])
        i=i+1;

        t=i,Time,date,number,status
    return t 

# for each contour found, draw a rectangle around it on original image
tu={}       
#main program
ht=0
wt=0
def fill(gray,a,b):
    
    #kernel =np.ones((a,b),np.uint8)
    kernel2 =np.ones((5,5),np.uint8)
   
    blur = cv2.blur(gray,(a,b))
    median = cv2.medianBlur(blur,5)
    _,thresh = cv2.threshold(blur,th,255,cv2.THRESH_BINARY)
   # dilation=cv2.dilate(thresh,kernel,iterations=1)
    erosion=cv2.erode(thresh,kernel2,iterations=1)
    
    
    cv2.imshow('thresh ',thresh)
    cv2.imshow('median ',median)
    #cv2.imshow('dilation ',dilation)
    
    
    cv2.imshow('blur ',blur)
    cv2.imshow('erosion ',erosion)
    #edges = cv2.Canny(dilation,150,200)
    #cv2.imshow('edges ',edges)
    return erosion

#___________________________________________________________________________
#main program

cap=cv2.VideoCapture(0)
#ret = cap.set(3,300)
#ret = cap.set(4,300)

while (True):
    
    
    ret,image=cap.read()
    image = cv2.resize(image,(400,400), interpolation = cv2.INTER_AREA)
    try :
        height = np.size(image,0)        
        width = np.size(image,1)
        
    except:
        pass
        
 
 
       
    image = cv2.resize(image,(400,400), interpolation = cv2.INTER_AREA)
    #cv2.imshow('image',image)
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        

    dilation=fill(gray,3,3)
   # print(image)
    j=cut(dilation)
    k=cv2.waitKey(1)
    #print k
   
    ht=int(height/2)
    wt=int(width/2)
    
    pts_L3= np.array([[0,ht],[width, ht]])
    frame = cv2.polylines( image, [pts_L3], True, (255,255,0),thickness=1)
    pts_L4= np.array([[ht,0],[ht, width]])
    frame = cv2.polylines( image, [pts_L4], True, (255,255,0),thickness=1)
    cv2.imshow('image', image)
   # cv2.imshow('dilation', dilation)
    if k==ord('w'):
        th=50
    if k==ord('e'):
        th=150
    if k==ord('r'):
        th=200
    if k==ord('m'):
        th=th-10
    if k==ord('n'):
        th=th+10
    if k==ord('q'):
    
        break
cap.release()
cv2.destroyAllWindows()

    
    #cv2.imshow('ima '+str(i),j)
    
#to OCRR
    
#ocr(j)
    




    


 





