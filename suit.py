

# Suit Code
# Author: Caleb Wolfe
# Date of Creation: 6/2/2018
import time
import Adafruit_MCP3008
import numpy as np
from neopixel import *
import animation #animation abstract class
import section #sections of the suit to light up
from stepanimation import * #simple step animation
from spectrumanalyzer import SpectrumAnalyzer
from Queue import Queue
from multiprocessing import Process, Pipe
from multiprocessing import  Queue as MQueue 
from multiprocessing import  Lock


class Suit:

	def __init__(self):
		# LED strip configuration:
        	LED_COUNT      = 442    # Number of LED pixels.
    		LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
    		LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
    		LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
    		LED_BRIGHTNESS = 64     # Set to 0 for darkest and 255 for brightest
    		LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
    		LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
    		LED_STRIP      = ws.SK6812_STRIP_GRBW
		self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL) # RGB Strip
		#self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP) # RGBW Strip
		self.backRightTop = section.Section("backRight", 0,26,True,"StepGreen")#Starting point Up
		self.backRightBottom = section.Section("backRight", 26,53,False,"StepGreen") #Starting point Up
		
		self.backLeftTop = section.Section("backLeft", 53,79,True,"MeteorRainRed") #Up
		self.backLeftBottom = section.Section("backLeft", 79,106,False,"MeteorRainRed") #Down
		
		self.lapelLeftTop = section.Section("lapelLeft", 106,141,True,"StepRed") #Up
		self.lapelLeftBottom = section.Section("lapelLeft", 141,175,False,"StepRed") #Down
		
		self.collarLeftBottom = section.Section("collarLeft",175,207,True,"StepGreen") #Up 65
		self.collarLeftTop = section.Section("collarLeft",207,240,False,"StepGreen") #Down
		
		self.collarRightTop = section.Section("collarRight",240,272,True,"StepGreen") #Up
		self.collarRightBottom = section.Section("collarRight",272,305,False,"StepGreen") #Down
		
		self.lapelRightBottom = section.Section("lapelRight",305,331,True,"StepRed") #Up
		self.lapelRightTop = section.Section("lapelRight",331,374,False,"StepRed") #Down
		
		
		
		self.__senistivity = 0.5
		self.spectrumanalyzer = SpectrumAnalyzer(1000000,self.__senistivity,1024) #Creat new spectum analyzer (Sample Hz Rate, Senistive in amplitude, sample size)
		self.sectionsList = [self.backLeftTop,self.backLeftBottom,self.backRightTop,self.backRightBottom, self.lapelRightTop, self.lapelRightBottom,self.collarRightTop,self.collarRightBottom,self.collarLeftTop,self.collarLeftBottom,self.lapelLeftTop,self.lapelLeftBottom] #Populate the list of LED sections (in shared memory
		self.__name = "Suit"
	
	def blackout(self):
        	for i in range(0, strip.numPixels()):
            		self.strip.setPixelColor(i, Color(0,0,0))
            		
	def blackoutPixel(self,p):
		self.strip.setPixelColor(p, Color(0,0,0))
		
def getFreqInfo(suit,mqtriggers):
		
		while True: #This takes apx. .12 secs 
			
			if not mqtriggers.full():
				
				suit.spectrumanalyzer.analyzeSpectrum()
				
				buckets = suit.spectrumanalyzer.getSpectrumBuckets()
				
				mqtriggers.put_nowait(buckets)
			
def ampCheck(conns):
	#Adjusts the amplitude sensitivity to ajust for different environments
	ampinit = np.array([61.0, 5.0, 5.0, 5.0, 3.0,3.0,3.0,3.0,3.0,2.0,2.0,2.0,2.0]) #Persisting array that gets updated
	start = np.array([55.0, 5.0, 5.0, 5.0, 3.0,3.0,3.0,3.0,3.0,2.0,1.0,1.0,1.0]) # Original values and minimum amplitudes
	dropval = np.array([3.0, .5, .5, .5, 2.0,2.0,2.0,1.0,.2,.2,.5,.1,.1])
	lastrun = time.clock()
	
	count = 1
	while True: 
		
		if conns.poll(.1):
			tmp = []
			amp=conns.recv()
			if amp.size > 0 and time.clock() - lastrun >.000001:
				for i in range(0,start.size): #decrement the amplitude by one "decibel" every .003 seconds	
					val = amp[i]
					
					if  val-dropval[i] > start[i]: #If the current amplitude can be decremented and still be above the minimum sensitivity, decrement
				 		tmp.append(val -dropval[i])
			 		else:
			 			tmp.append(val)		#Else, append the current amplitude 
				lastrun = time.clock() # Validate the last time the amplitude values were decremented
				
				amp = np.append([],tmp)
				
				ampinit = amp
				conns.send(amp)
		
		else:	
			conns.send(ampinit)

				
def buildAnimations(mqtriggers,mqaminations,connr):

		amp=np.array([60.0, 5.0, 5.0, 5.0, 3.0,3.0,3.0,3.0,3.0,2.0,2.0,2.0,2.0])
		while True:
			amp = []
			if connr.poll():
				ampcheckvals =connr.recv()
				if not mqtriggers.empty() and not mqaminations.full() and  ampcheckvals.size > 0: #check to see if animation queue is full and if so wait until opening
					buckets = mqtriggers.get_nowait()
					list = []
					#--------------Generate Frame---------------
					count = 0
					
					for b in buckets:
						if count == 0: 							
							if b > ampcheckvals[count] :						
								amp.append(b)
								list.append(("subbass","Sparkle",b))
							else:
								 amp.append(ampcheckvals[count])	
						elif count == 1:
							if b > ampcheckvals[count] : 
								amp.append(b)
								list.append(("basslow","Sparkle",b))
							else:
								 amp.append(ampcheckvals[count])									

						elif count == 2: 

								if b > ampcheckvals[count]:
									amp.append(b)
									list.append(("basshigh","Sparkle",b))
									
								else:
								 	amp.append(ampcheckvals[count])										
						elif count == 3:
							
								 if b > ampcheckvals[count]:
								 	amp.append(b)
								 	
									list.append(("lowmid1","StepPink",b)) #Most used range
								 else:
								 		amp.append(ampcheckvals[count])										
						elif count == 4:
							 if  b > ampcheckvals[count]: 
							 	amp.append(b)
								list.append(("lowmid2","StepLightBlue",b))
								
							 else:
								 amp.append(ampcheckvals[count])									
						elif count == 5:
							if b > ampcheckvals[count]:
								amp.append(b)
								list.append(("lowmid3","StepBlue",b))
							else:
								 amp.append(ampcheckvals[count])										
						elif count == 6:
							 if  b > ampcheckvals[count]: 
							 	amp.append(b)
								list.append(("lowmid4","StepPurple",b))
								
							 else:
								 amp.append(ampcheckvals[count])									
						elif count == 7:
							 if  b > ampcheckvals[count]: 
							 	amp.append(b)
								list.append(("mid1","Step",b))
							 else:
								 amp.append(ampcheckvals[count])									
						elif count == 8:
							if b > ampcheckvals[count]:
								amp.append(b)
								list.append(("mid2","StepRose",b))
							else:
								 amp.append(ampcheckvals[count])									
						elif count == 9:
							if b > ampcheckvals[count]:
								amp.append(b)
								list.append(("mid3","StepGreen",b))
							else:
								 amp.append(ampcheckvals[count])									
						elif count == 10:
							if b > ampcheckvals[count]:
								amp.append(b)
								list.append(("mid4","StepYellow",b))
							else:
								 amp.append(ampcheckvals[count])									
						elif count == 11:
							if b > ampcheckvals[count]:
								amp.append(b)
								list.append(("highlow","StepOrange",b))
							else:
								 amp.append(ampcheckvals[count])									
						elif count == 12:
							if b > ampcheckvals[count]:
								amp.append(b)
								list.append(("highhigh","Step",b))																	
								
							else:
								 amp.append(ampcheckvals[count])									
						count +=1
					if list and not mqaminations.full(): #if list is full and animation q is not full
						mqaminations.put_nowait(list)
				
				
					ampArr = np.append([],amp)
				
					connr.send(ampArr)
	
def playAnimations(suit,mqanimation):
	suit.strip.begin()
	count = 0
	while True:
		st = time.clock()
		suit.blackout()
		
		if not mqanimation.empty():
			
			animations = mqanimation.get_nowait()
			#pydevd.settrace('192.168.1.19',port=5678)

			for animation in animations:
				if animation[0] == "highhigh":
					suit.backLeftTop.addAnimation(animation[1],animation[2])
					suit.backLeftBottom.addAnimation(animation[1],animation[2])
					
					
					suit.backRightTop.addAnimation(animation[1],animation[2])
					suit.backRightBottom.addAnimation(animation[1],animation[2])	


					
				if animation[0] == "highlow": #list is not empty in this bucket

					suit.backLeftTop.addAnimation(animation[1],animation[2])
					suit.backLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.backRightTop.addAnimation(animation[1],animation[2])
					suit.backRightBottom.addAnimation(animation[1],animation[2])	

				if animation[0] == "mid1":

					suit.lapelRightTop.addAnimation(animation[1],animation[2])
					suit.lapelRightBottom.addAnimation(animation[1],animation[2])

				if animation[0] == "mid2":
					

					suit.lapelLeftTop.addAnimation(animation[1],animation[2])
					suit.lapelLeftBottom.addAnimation(animation[1],animation[2])

				if animation[0] == "mid3":
					
					suit.backLeftTop.addAnimation(animation[1],animation[2])
					suit.backLeftBottom.addAnimation(animation[1],animation[2])

					suit.backRightTop.addAnimation(animation[1],animation[2])
					suit.backRightBottom.addAnimation(animation[1],animation[2])					
				if animation[0] == "mid4": #list is not empty in this bucket

					suit.lapelLeftTop.addAnimation(animation[1],animation[2])
					suit.lapelLeftBottom.addAnimation(animation[1],animation[2])

				if animation[0] == "lowmid1":

					suit.collarLeftTop.addAnimation(animation[1],animation[2])

					
					suit.collarRightTop.addAnimation(animation[1],animation[2])

				if animation[0] == "lowmid2":
					

					suit.collarLeftBottom.addAnimation(animation[1],animation[2])

					suit.collarRightBottom.addAnimation(animation[1],animation[2])																			

				if animation[0] == "lowmid3":
					

					suit.lapelRightTop.addAnimation(animation[1],animation[2])
					suit.lapelRightBottom.addAnimation(animation[1],animation[2])	

				if animation[0] == "lowmid4":

					suit.lapelLeftTop.addAnimation(animation[1],animation[2])
					suit.lapelLeftBottom.addAnimation(animation[1],animation[2])

				if animation[0] == "basslow":

					
					suit.lapelLeftTop.addAnimation(animation[1],animation[2])
					suit.lapelLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.lapelRightTop.addAnimation(animation[1],animation[2])
					suit.lapelRightBottom.addAnimation(animation[1],animation[2])
					
					suit.collarLeftTop.addAnimation(animation[1],animation[2])
					suit.collarLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.collarRightTop.addAnimation(animation[1],animation[2])
					suit.collarRightBottom.addAnimation(animation[1],animation[2])
					
					
					suit.backLeftTop.addAnimation(animation[1],animation[2])
					suit.backLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.backRightTop.addAnimation(animation[1],animation[2])
					suit.backRightBottom.addAnimation(animation[1],animation[2])
					
				if animation[0] == "basshigh":

					
					suit.lapelLeftTop.addAnimation(animation[1],animation[2])
					suit.lapelLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.lapelRightTop.addAnimation(animation[1],animation[2])
					suit.lapelRightBottom.addAnimation(animation[1],animation[2])
					
					suit.collarLeftTop.addAnimation(animation[1],animation[2])
					suit.collarLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.collarRightTop.addAnimation(animation[1],animation[2])
					suit.collarRightBottom.addAnimation(animation[1],animation[2])
					
					
					suit.backLeftTop.addAnimation(animation[1],animation[2])
					suit.backLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.backRightTop.addAnimation(animation[1],animation[2])
					suit.backRightBottom.addAnimation(animation[1],animation[2])
				if animation[0] == "subbass":

					suit.collarLeftTop.addAnimation(animation[1],animation[2])
					suit.collarLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.collarRightTop.addAnimation(animation[1],animation[2])
					suit.collarRightBottom.addAnimation(animation[1],animation[2])
					
					suit.lapelLeftTop.addAnimation(animation[1],animation[2])
					suit.lapelLeftBottom.addAnimation(animation[1],animation[2])
					suit.lapelRightTop.addAnimation(animation[1],animation[2])
					suit.lapelRightBottom.addAnimation(animation[1],animation[2])
					
					suit.backLeftTop.addAnimation(animation[1],animation[2])
					suit.backLeftBottom.addAnimation(animation[1],animation[2])
					
					suit.backRightTop.addAnimation(animation[1],animation[2])
					suit.backRightBottom.addAnimation(animation[1],animation[2])


		for sect in suit.sectionsList : #Assumption here is that no 2 sections share pixels
				while sect.getNextAnimation(): #animation queue is not empty
			

					for pixels in sect.playAnmimation():

							strip.setPixelColor(pixels[0], pixels[1]) # Setting a pixel is constant time 
		
		strip.show() 
		count += 1

		for sect in suit.sectionsList:
			sect.progressAnimations() 		
			
			#--------------Generate Frame V1------------------

if __name__ == '__main__':
    s = Suit()
    connr,conns = Pipe()
    strip = s.strip
    mqtrigger = MQueue(maxsize = 3)
    mqanimation = MQueue(maxsize = 2)
    pa = Process(target=getFreqInfo, args=(s,mqtrigger))
    pb = Process(target=buildAnimations, args=(mqtrigger,mqanimation,connr))
    p2 = Process(target=playAnimations, args=(s,mqanimation))
    pc = Process(target=ampCheck,args=(conns,))
    pa.start()
    pb.start()
    p2.start()
    pc.start()
    pa.join()
    pb.join()
    p2.join()
    pc.join()
