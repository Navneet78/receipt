'''
Import All Libraries
'''

from PIL import Image 
import pytesseract 
import sys 
from pdf2image import convert_from_path 
import os 
import cv2
import codecs
from lxml import etree, objectify
import datetime

'''
A utility function to get maximum of ammounts represented
in form of list of strings. 
'''

def findMaximum(arr):
  arr = [x.replace('$', '').replace(',','').replace(" ", '') for x in arr]
  arr = [float(x) for x in arr]
  return max(arr)


'''
A function that converts list of string representations of dates to 
list of date time object such that later it will be easy for comparision.
'''

def find_date(arr):
  n = len(arr)
  for i in range(n):
    try:
      arr[i]=  datetime.datetime.strptime(arr[i], '%m/%d/%Y')
    except ValueError as ve:
      arr[i]=  datetime.datetime.strptime(arr[i], '%m/%d/%y')
    except ValueError:
      pass

'''
A Function to find confidence of any feature having no of possibality n.
'''

def find_confidence(n):
  if (n==0):
    return 0
  return (1/n)*100


'''
To Get text in the form of string from pdf file we used pytesseract 
As it is having multiple page segmentation modes Although pytesseract 
works only upon images so we first converted pdf into images using 
pdf2image and use PIL-Image to read that image. After reading image we
used 4th Page segmentation mode which means it assumes a single column 
of text of variable sizes. Then saved text in text variable for further 
analysis. Also removed image that we have created earlier.
'''


PDF_file = "/content/invoices/5_CIOX_0248727220.pdf"
pages = convert_from_path(PDF_file, 500) 
image_counter = 1

for page in pages:
  file_name = "page"+str(image_counter)+".jpg"
  page.save(file_name, 'JPEG')
  image_counter+=1

filelimit = image_counter-1
custom_oem_psm_config = r'--oem 3 --psm 4'
#pytesseract.image_to_string(image, config=custom_oem_psm_config)
text = ''

for i in range(1, filelimit+1):
  filename = "page"+str(i)+".jpg"
  ##print("##################################################"+"          "+file_name)
  text+=str(((pytesseract.image_to_string(Image.open(filename), config=custom_oem_psm_config))))
  if os.path.exists(filename):
    os.remove(filename)

'''
other methods to get Text :-

'''


'''
Precised Regex Pattern to get different fields. we can also train
spacy model on these text but it requires lots of manpower in labeling 
huge dataset,  So I think regex is most efficient way to get all other 
fields.  
'''

import re 
amount_pattern = r'\$\s?[\d\,]{1,15}(?:\.\d{2})?'
invoice_no_pattern = r'Invoice\s*?(?:Number)?(?:No)?\.?\s*?#?:?\s*?\d+'
invoice_no_pattern_1 = r'Invoice\s*?(?:Number)?(?:No)?\.?\s*?#?:?\s*?\d+(?:.*)?'
#invoice_no_pattern = r'Invoice\s*?(Number)?(No)?\.?\s*?#?:?\s*?\d+(.*)?'
invoice_no_pattern_2 = r'Invoice(?:\s*)?(?:Number)?(?:No)?\.?(?:\s*)?(?:[:#])?.{1,18}'
#invoice_no_pattern_2 = r'Invoice(\s*)?(Number)?(No)?\.?(\s*)?(?:[:#])?.{1,18}'
date_pattern = r'\d{1,2}\/\d{1,2}\/\d{1,4}'
date_pattern_1 = r'\d{1,2}\-\d{1,2}\-\d{1,4}'
date_pattern_2= r'\d{1,2}\s?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s?\d{4}' 
terms_pattern = r'Terms?\s?:?\s?.*'
# print(text)

'''
Total due amount must be (Most of the cases) the maximum of all the amounts extracted 
in text
'''
amounts = re.findall(amount_pattern, text)
total_due_ammount = findMaximum(amounts)
'''
invoice_no_1, invoice_no_2, invoice_no_3 are all invoice no pattern in order of priority.
'''
invoice_no_count = 0
invoice_no = []
invoice_no_1 = list(set(re.findall(invoice_no_pattern, text, re.IGNORECASE)))
invoice_no_count+= len(invoice_no_1)
invoice_no.extend(invoice_no_1)
invoice_no_2 = re.findall(invoice_no_pattern_1, text, re.IGNORECASE)
invoice_no_2 = list(set(invoice_no_2))
invoice_no_count+= len(invoice_no_2)
invoice_no.extend(invoice_no_2)
invoice_no_3 = re.findall(invoice_no_pattern_2, text, re.IGNORECASE)
invoice_no_3 = list(set(invoice_no_3))
invoice_no_count+= len(invoice_no_3)
invoice_no.extend(invoice_no_3)
invoice_no = list(set(invoice_no))
if (len(invoice_no)>0):
  invoice_no_ = invoice_no[0]
else:
  invoice_no_ = ''
invoice_no_confidence = find_confidence(invoice_no_count)


dates = list(set(re.findall(date_pattern, text, re.IGNORECASE)))
date_confidence = 0

try:
  find_date(dates)
except:
  date_confidence = 30
  pass
dates = list(set(dates))

invoice_date = ''
due_date = ''
try:
  dates.sort()
  date_confidence = 85
except:
  date_confidence = 50
  pass
if (len(dates)>1):
  try:
    invoice_date = dates[0].strftime("%m/%d/%Y")
    due_date = dates[-1].strftime("%m/%d/%Y")
  except AttributeError:
    invoice_date = dates[0]
    due_date = dates[-1]

elif (len(dates)==1):
  try:
    invoice_date = dates[0].strftime("%m/%d/%Y")
  except AttributeError:
    invoice_date = dates[0]

terms = list(set(re.findall(terms_pattern, text, re.IGNORECASE)))
terms_confidence = find_confidence(len(terms))*0.9

'''
To get Lined items(In the table) from Pdf we used corresponding xml file 
and to handle xml file and get desired items we used etree of LXML 
and get all table rows and columns.
'''

files = "/content/ocr_output/5_CIOX_0248727220.pdf.xml"
text = ''


'''
In all these xml files in the root tag it contains xmlns property which is creating problem for 
getting nodes by xpath so first we removed unwanted properties from root node. Then saved as modified.xml. 
'''

with open(files, 'r') as f:
  text+= f.read()
text = text.replace('''xmlns="http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml" version="1.0" producer="ABBYY FineReader Engine 11" languages="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml"''', '')
#print (text)
file = codecs.open("modified.xml", "w", "utf-8")
file.write(text)
file.close()

tree = etree.parse(r'modified.xml')
root = tree.getroot()
table = root.xpath("//block[@blockType='Table']")    #getting all tables
rows = []
for t in table:
  rows.extend(t.findall('row'))                      #Getting all rows
res = []

"""Storing all the rows in a a list res"""
for row in rows:
  res.append(''.join(row.xpath('.//cell/text/par/line/formatting/charParams/text()')))
  print(''.join(row.xpath('.//cell/text/par/line/formatting/charParams/text()')))

'''
Writing Output file in Json
'''


final_output = {} 
final_output['Invoice Total'] = {}
final_output['Invoice Total']['amount'] = '$ ' + str(total_due_ammount)
final_output['Invoice Total']['confidence']= '90 %'

final_output['Invoice Number']  = {}
if (invoice_no_ != ''):
  final_output['Invoice Number']['Invoice'] = invoice_no_
  final_output['Invoice Number']['confidence'] = invoice_no_confidence
  final_output['Invoice Number']['Other Possibalities'] = invoice_no[1:]

final_output['Important Dates'] = {}
final_output['Important Dates']['Invoice Date'] = invoice_date
final_output['Important Dates']['Due Date'] = due_date
final_output['Important Dates']['Date Confidence'] = date_confidence
final_output['Terms']= {}
final_output['Terms']['Payment Terms'] = terms
final_output['Terms']['confidence'] = terms_confidence
final_output['Lined Items'] = res

import json
with open('output.json', 'w') as fp:
  json.dump(final_output, fp, sort_keys=True, indent=4)