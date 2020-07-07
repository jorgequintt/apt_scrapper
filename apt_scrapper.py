# -*- coding: utf-8 -*-
debug = False
debug = True

#################### IMPORTS #####################################
from lxml import html
from random import choice
import queue
import requests
import urllib
import time
import sys
import requests.packages.urllib3
import csv
import os
import ast
import re
from PIL import Image
import pytesseract
import datetime
import json

args = sys.argv
if len(args) > 1:
	args[0] = args[1]
else:
	args = False

now = datetime.datetime.now()
pytesseract.pytesseract.tesseract_cmd = 'Tesseract-OCR/tesseract'
##################### GLOBAL VARS ####################################

desktop_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']
 
def random_headers():
    return {'User-Agent': choice(desktop_agents),'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

######################## FUNCTIONS #################################
def dbug(msg):
	if debug:
		print(msg)

def dbug2(msg):
	if debug:
		print(msg)
		input()


def update_progress(progress, extra_text):
    barLength = 16 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Espera...\r\n"
    if progress >= 1:
        progress = 1
        status = "Listo...\r\n"
    block = int(round(barLength*progress))
    text = "\r{3} - Porcentaje: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), int(progress*100), status, extra_text)
    sys.stdout.write(text)
    sys.stdout.flush()

def get_tree(url):
	response = False
	while True:
		try:
			dbug(url)
			time.sleep(0)
			r = requests.get(url, headers=random_headers(), timeout=50)
			dbug(r)
			response = html.fromstring( r.content.decode('UTF-8') )
			break
		except:
			print("Problema de conexión, intentando de nuevo en 7 segundos...")
			time.sleep(7)
	return response

def request_page(url):
	response = False
	while True:
		try:
			dbug(url)
			time.sleep(0)
			r = requests.get(url, headers=random_headers(), timeout=50)
			dbug(r)
			response = r
			break
		except:
			print("Problema de conexión, intentando de nuevo en 7 segundos...")
			time.sleep(7)
	return response

class App:
	appName = "OlxScrapper"
	urls_file = "f"+args[0]+"/olx_ready_urls.txt" if args else "olx_ready_urls.txt"
	first_csv_file = "f"+args[0]+"/olx_data.csv" if args else "olx_data.csv"

	def __init__(self):
		#check if we should resume or start from the beginning
		#if urls_file already exists, offer to resume or start from scratch
		#else, go to "start" step

		if not os.path.exists(self.urls_file):
			open(self.urls_file, 'a').close()
		if not os.path.exists(self.first_csv_file):
			open(self.first_csv_file, 'a').close()

		if self.get_amount_of_lines_from_file() > 0 and not self.is_csv_empty():
			print("Parece que el proceso de captura anterior no se completó. ¿Desea resumirlo?")
			print('Escriba "Si" para resumir la captura anterior. Escriba "No" para comenzar una nueva captura. Luego presione Enter')
			self.start_capture()
			return
			if action.lower() in ['si', 'sí']:
				print("Resumiendo captura anterior...")
				self.start_capture()
			elif action.lower() == "no":
				print("Comenzando nueva captura de datos desde cero...")
				#self.bootstrap()
		else:
			print('Presione Enter para comenzar la captura de datos.')
			input()
			#self.bootstrap()

	def bootstrap(self):
		if os.path.exists(self.urls_file):
			os.remove(self.urls_file)
		if os.path.exists(self.first_csv_file):
			os.remove(self.first_csv_file)

		print("Iniciando, por favor, espere. Esto podria tomar un par de minutos...")
		self.find_last_pages()
		dbug("Creando lista de apartamentos a capturar...")
		self.get_all_urls()

		print('Se ha creado la lista de apartamentos a capturar, se procede a capturar la información...')
		self.start_capture()

	def start_capture(self):
		lines_file = self.get_amount_of_lines_from_file()
		i = 1

		update_progress((float(i)/float(lines_file)), ("Restantes {}/{}".format(i, lines_file)))
		
		while self.get_amount_of_lines_from_file() > 0:
			dbug("get data from apartment URL")
			self.get_data_from_apartment_url()
			self.delete_first_line_from_file()
			i += 1
			update_progress((float(i)/float(lines_file)), ("Restantes {}/{}".format(i, lines_file)))

		new_csv_name = 'data_'+str(now.day)+'-'+str(now.month)+'-'+str(now.year)+'.csv'
		os.rename(self.first_csv_file, new_csv_name)
		os.remove(self.urls_file)
		
		print("Se han terminado de capturar todos los datos en el archivo \""+new_csv_name+"\". Presione Enter para salir.")
		input()

	def find_last_pages(self):
		self.urls = []
		#self.urls.append(["https://www.fincaraiz.com.co/apartamento-casa-apartaestudio/venta/medellin/?ad=30|", 1,"||||1||8,9,22|||55|5500006||105000000|5000000000||||||||||||||||1||griddate%20desc||||-1|3,4,5,6|"])
		#self.urls.append(["https://www.fincaraiz.com.co/apartamento-casa-apartaestudio/venta/envigado/?ad=30|", 1,"||||1||8,9,22|||55|5500001||105000000|5000000000||||||||||||||||1||griddate%20desc||||-1|3,4,5,6|"])
		#self.urls.append(["https://www.fincaraiz.com.co/apartamento-casa-apartaestudio/venta/sabaneta/?ad=30|", 1,"||||1||8,9,22|||55|5500016||105000000|5000000000|||||||||||||1|||1||griddate%20desc||||-1|3,4,5,6|"])
		#self.urls.append(["https://www.fincaraiz.com.co/apartamento-casa-apartaestudio/venta/itagui/?ad=30|", 1,"||||1||8,9,22|||55|5500002||105000000|5000000000|||||||||||||1|||1||griddate%20desc||||-1|3,4,5,6|"])
		#self.urls.append(["https://www.fincaraiz.com.co/apartamento-casa-apartaestudio/venta/la-estrella/?ad=30|", 1,"||||1||8,9,22|||55|5500003||105000000|5000000000|||||||||||||1|||1||griddate%20desc||||-1|3,4,5,6|"])
		#self.urls.append(["https://www.fincaraiz.com.co/apartamento-casa/venta/caldas/?ad=30|", 1,"||||1||8,9|||55|5500011||105000000|5000000000|||||||||||||1|||1||griddate%20desc||||-1|3,4,5,6|"])
		self.urls.append(["https://www.fincaraiz.com.co/finca-raiz/venta/antioquia/?ad=30|", 1,"||||1||8,9,7,3,4,22,21,5,18|||55|||||||||||||||||1|||1||griddate%20desc||||-1||"])

		self.last_pages = []

		for url in self.urls:
			last_page_found = False
			step = 1000
			p = 3000
			while not last_page_found:
				url[1] = p
				page = get_tree(''.join(str(x) for x in url))
				page_buttons_xpath = '//a[contains(@class,"link-pag")]'
				page_buttons = page.xpath(page_buttons_xpath)
				
				dbug(len(page_buttons))
				
				is_last_page_found = len(page_buttons) > 1
				if is_last_page_found:
					p = p + step
					step = step / 10
					step = int(step)
				else:
					p = p - step
					
				if step < 1 and is_last_page_found:
					true_last_page = page.xpath('//a[contains(@class,"link-pag")][last()]/text()')[0].strip()
					true_last_page = int(true_last_page)
					last_page_found = True
			dbug('last page found: '+str(true_last_page))
			self.last_pages.append(true_last_page)
				
	def get_all_urls(self):
		i = 0
		
		ii = 1
		total_pages = sum(self.last_pages)

		update_progress((float(ii)/float(total_pages)), ("Pagina {}/{}".format(ii, total_pages)))

		for u in self.urls:
			last_page = self.last_pages[i]
			p = 1
			while p <= last_page: 
				u[1] = p
				url = ''.join(str(x) for x in u)
				page = get_tree(url)
				apartment_urls = page.xpath('//div[@class="span-title"]/a/@href')
				with open(self.urls_file, 'a') as f:
					for a in apartment_urls:
						f.write(a+'\n')
				p += 1
				ii += 1

				#show progress
				update_progress((float(ii)/float(total_pages)), ("Pagina {}/{}".format(ii, total_pages)))
			i += 1

	def get_data_from_apartment_url(self):
		try:
			url = self.read_first_line_from_file()
			url = "https://m.olx.com.co/" + url.split('/')[-1]

			page = get_tree(url)

			title = '//*[contains(@class, "item-title")]/text()[1]'
			precio = '//*[contains(@class, "item-price-gallery")]/text()[1]'
			ciudad = '//*[contains(@class, "item-publication-gallery")]/text()[3]'
			telefono = '//*[contains(@class, "phone")]/@href[1]'
			marca_modelo = '//*[contains(text(), "Marca / Modelo")]/following-sibling::strong/text()[1]'
			ano_condicion = '//*[contains(text(), "Año / Condición")]/following-sibling::strong/text()[1]'
			kilometraje = '//*[contains(text(), "Kilometraje")]/following-sibling::strong/text()[1]'
			combustible = '//*[contains(text(), "Combustible")]/following-sibling::strong/text()[1]'
			transmisión = '//*[contains(text(), "Transmisión")]/following-sibling::strong/text()[1]'
			placa = '//*[contains(text(), "Placa")]/following-sibling::strong/text()[1]'
			color = '//*[contains(text(), "Color")]/following-sibling::strong/text()[1]'
			tipo_de_vendedor = '//*[contains(text(), "Tipo de Vendedor")]/following-sibling::strong/text()[1]'

			to_capture = [title, precio, ciudad, telefono, marca_modelo, ano_condicion, kilometraje, combustible, transmisión, placa, color, tipo_de_vendedor]
			captured = [""] * len(to_capture)

			for i in range(len(to_capture)):
			    dat = page.xpath(to_capture[i])

			    if dat:
			        if i == 0: dat[0] = dat[0].replace(',', '')
			        if i == 1: dat[0] = dat[0].replace('$', '').replace('.', '')
			        if i == 3: dat[0] = dat[0].replace('tel:+', '')
			        captured[i] = dat[0]

			self.write_data_in_csv(captured + [url])
		except Exception as e:
			dbug("omitted cause of problem")


	def get_phone_from_key(self, url):
		temp_file_name = "temp.png"
		phone_img = request_page("https://www.fincaraiz.com.co"+url)
		#phone_img = request_page('https://www.fincaraiz.com.co/GenImage.ashx?key='+key)
		#ocr
		dbug('GOT image from phone')
		with open(temp_file_name, 'wb') as f:
		    f.write(phone_img.content)
		im = Image.open(temp_file_name)
		text = pytesseract.image_to_string(im, lang = 'eng')
		os.remove(temp_file_name)
		return text

	def write_data_in_csv(self, data):
		with open(self.first_csv_file, 'a') as csvfile:
			swriter = csv.writer(csvfile, dialect='excel', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_NONE)
			#swriter = csv.writer(csvfile, dialect='excel', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_NONNUMERIC)
			#swriter = csv.writer(csvfile, dialect='excel', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
			swriter.writerow(data)

	def get_amount_of_lines_from_file(self):
		return sum(1 for line in open(self.urls_file))

	def is_csv_empty(self):
		csv_data = sum(1 for line in open(self.first_csv_file))
		if csv_data > 0:
			return False
		return True

	def read_first_line_from_file(self):
		return open(self.urls_file, 'r').readline().strip()

	def delete_first_line_from_file(self):
		filePath = self.urls_file
		file_str = ""
		with open(filePath,'r') as f:
		        next(f)  # skip header line
		        for line in f:
		            file_str = file_str + line

		with open(filePath, "w") as f:
		    f.write(file_str)




print("##############################################")
print("#                                            #")
print("#               AptScrapper v1.02            #")
print("#                                            #")
print("##############################################")
print("")
try:
	init = App()
except Exception as e: 
	print("Error: "+str(e))
	with open('error_log.txt', 'a') as f:
		f.write(str(e)+'\n\n')
		f.write('\n\n')

	input()
	input()

#input() 
