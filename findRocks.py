#!/usr/bin/env python3

from flask import Flask
import os
import cv2
import numpy as np
import imutils
from PIL import Image, ImageEnhance
import random as rng
import math



UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

#
def imageAlter(image):
   alteredImage = Image.open(image)   
   contrast = ImageEnhance.Contrast(alteredImage)
   color = ImageEnhance.Color(alteredImage)
   alteredImage = contrast.enhance(1.1)
   alteredImage = color.enhance(0.8)
   alteredImage.save("altered.jpg", "JPEG")
   return



def imageAnalyze(image, debug=True):
   cv2.destroyAllWindows()
   img = cv2.imread(image)
   cv2.namedWindow("original", cv2.WINDOW_NORMAL)
   #cv2.namedWindow("CV", cv2.WINDOW_NORMAL)
   #cv2.namedWindow("edges", cv2.WINDOW_NORMAL)
   img = cv2.bilateralFilter(img,9,75,75)
   hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

   # Accepted Colors
   #-----------
   #defining the Range of purple wall color
   wall_upper = np.array([156,110,131])
   wall_lower = np.array([86,44,63])

   #defining the Range of Yellow color
   yellow_upper = np.array([30, 255, 255])
   yellow_lower = np.array([6,38,61])
   
   yellow_alt_upper = np.array([212,192,121])
   yellow_alt_lower = np.array([130,102,28])

   #defining the Range of Purple color
   purple_upper = np.array([125,104,161])
   purple_lower = np.array([49,39,63])

   #defining the Range of Green color
   green_upper = np.array([49,96,62])
   green_lower = np.array([23,48,29])

   #defining the Range of Red color
   red_upper = np.array([200,94,96])
   red_lower = np.array([51,22,26])

   #defining the Range of Black color
   black_upper = np.array([32,30,36])
   black_lower = np.array([26,25,31])

   #defining the Range of Blue color
   blue_upper = np.array([115,161,221])
   blue_lower = np.array([36,52,77])

   #-----------
   #additive masks
   mask_alt_yellow = cv2.inRange(hsv,yellow_alt_lower, yellow_alt_upper)
   mask_blue = cv2.inRange(hsv,blue_lower,blue_upper)
   mask_green = cv2.inRange(hsv,green_lower,green_upper)
   mask_red = cv2.inRange(hsv,red_lower,red_upper)
   mask_yellow = cv2.inRange(hsv,yellow_lower,yellow_upper)
   mask_purple = cv2.inRange(hsv,purple_lower,purple_upper)

   #layering additive masks
   temp1 = cv2.addWeighted(mask_blue, 1, mask_green, 1,0)
   temp1 = cv2.addWeighted(temp1, 1, mask_alt_yellow, 1,0)
   temp2 = cv2.addWeighted(mask_yellow, 1, mask_red, 1,0)
   temp2 = cv2.addWeighted(temp2, 1, mask_purple, 1,0)
   mask_master = cv2.addWeighted(temp1, 1, temp2, 1,0)

   mask_wall = cv2.inRange(hsv,wall_lower,wall_upper)

   #subtracting wall mask from mask master
   mask_master = cv2.subtract(mask_master, mask_wall)

   imS = cv2.resize(img, (960, 540))
   #imM = cv2.resize(mask_master, (960, 540))
   

   # copy all masks to orignal image
   new_image = cv2.copyTo(img, mask_master)
   
   edges = cv2.Canny(new_image,100,200, apertureSize=7)
   edges = cv2.blur(edges, (5,5))

   new_edges = cv2.copyTo(img, edges)
   new_edges = cv2.Canny(new_edges,100,200, apertureSize=7)
   #hsv_edges = cv2.cvtColor(new_edges, cv2.COLOR_BGR2HSV)

   threshold = 500
   ret,thresh = cv2.threshold(mask_master,250,255,cv2.THRESH_BINARY_INV)
   contours,hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
   canny_output = cv2.Canny(mask_master, threshold, threshold * 2)

   contours_poly = [None]*len(contours)
   boundRect = [None]*len(contours)
   centers = [None]*len(contours)
   radius = [None]*len(contours)
   for i, c in enumerate(contours):

      contours_poly[i] = cv2.approxPolyDP(c, 5, True)
      boundRect[i] = cv2.boundingRect(contours_poly[i])
      centers[i], radius[i] = cv2.minEnclosingCircle(contours_poly[i])

   drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
   
   objects=[]

   hierarchy = hierarchy[0]
   tempObjects = []
   print(len(contours))
   for i in range(len(contours)):
      currentHierarchy = hierarchy[i]
      color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
      if int(radius[i]) > 10 and int(radius[i]) < 500:
         cv2.circle(edges, (int(centers[i][0]), int(centers[i][1])), int(radius[i]), color, 2)
         objects.append((int(centers[i][0]), int(centers[i][1]), int(radius[i])))

  
   def mouse_drawing(event, x, y, flags, params):
      if event == cv2.EVENT_LBUTTONDOWN:
         for hold in objects:
               x2 = hold[0]
               y2 = hold[1]
               rad = hold[2]
               red = (0,0,255)
               dist = math.sqrt((x2 - x)**2 + (y2 - y)**2)
               font = cv2.FONT_HERSHEY_SIMPLEX
               if (dist < rad):
                  org = (x-50, y-50)
                  cv2.putText(img,"O", org, font, 5, red, 10,cv2.LINE_AA, True)
                  print (org)
                  cv2.imshow('original', img)
                  print(flags)
         print("Left click", x, y)


   cv2.setMouseCallback('original', mouse_drawing)

   #cv2.imshow("CV", mask_master)
   cv2.imshow('original', img)
   #cv2.imshow("edges", edges)
  
   out_file = outfile(image)
   cv2.imwrite(os.path.join(UPLOAD_DIR, out_file), img)

   while(debug):
      k = cv2.waitKey(5) & 0xFF
      if k == 27:
         break

   cv2.destroyAllWindows()

   return


def outfile(fname):
   comps = os.path.basename(fname).rsplit(".", 1)
   outfname = comps[0] + "-CV." + comps[1]
   return outfname


def main():
      # For everyone else
      imageAlter('RockPictures/IMG_20200116_143855.jpg')
      imageAnalyze('altered.jpg', debug=True)


def flaskTest():
   string = "If you can read this, you're viewing it from a Flask server"

   return string


if __name__ == "__main__":
   main()

