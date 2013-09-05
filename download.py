#/usr/bin/env python

import requests
import parse
from getpass import getpass
from file_output import file_output

session = requests.session()
parse.setSession(session)

username = input("Username: ")
password = getpass("Password for %s: " % username)

loginResponse = session.post("https://www.stuller.com/login/?returnUrl=%2F", data={"userName":username, "password":password})

if loginResponse.text.find("The username and password combination you entered is invalid.") != -1:
	print("Login failed.")
	exit()

sections = {
	"calibrated-gems-by-type":					"http://www.stuller.com/browse/gemstones/shop-by-stone-type/calibrated-gems-by-type/",
	"wedding-and-engagement-engagements": 		"http://www.stuller.com/browse/mountings/wedding-and-engagement/engagements/",
	"wedding-and-engagement-solitaire": 		"http://www.stuller.com/browse/mountings/wedding-and-engagement/solitaire/",
	"wedding-and-engagement-3-stone": 			"http://www.stuller.com/browse/mountings/wedding-and-engagement/3-stone/",
	"rings-gemstone-fashion": 					"http://www.stuller.com/browse/jewelry/rings/gemstone-fashion/",
	"necklaces-and-pendants-gemstone-fashion": 	"http://www.stuller.com/browse/jewelry/necklaces-and-pendants/gemstone-fashion/",
	"necklaces-and-pendants-diamond-fashion": 	"http://www.stuller.com/browse/jewelry/necklaces-and-pendants/diamond-fashion/",
	"diamond-stud-earrings": 					"http://www.stuller.com/diamond-stud-earrings/",
	"earrings-gemstone-fashion": 				"http://www.stuller.com/browse/jewelry/earrings/gemstone-fashion/",
	"diamond-fashion-button": 					"http://www.stuller.com/browse/jewelry/earrings/diamond-fashion/button/",
	"diamond-fashion-drop": 					"http://www.stuller.com/browse/jewelry/earrings/diamond-fashion/drop/",
	"diamond-fashion-jackets": 					"http://www.stuller.com/browse/jewelry/earrings/diamond-fashion/jackets/",
	"wedding-and-engagement-anniversary-and-eternity-bands": "http://www.stuller.com/browse/mountings/wedding-and-engagement/anniversary-and-eternity-bands/",
}

for section, requestURL in sections.items():
	print ("Starting section '%s' at %s" % (section, requestURL))
	productConfigurations = []

	response = session.get(requestURL)
	parser = parse.ProductCategoriesParser()
	categoryLinksToFollow = parser.parseLinks(response.text)

	for categoryLink in categoryLinksToFollow:
		parser = parse.CategoryParser()
		print ("Getting category list at " + categoryLink)
		response = session.get(categoryLink)
		productTypeLinksToFollow = parser.parseLinks(response.text)

		for typeLink in productTypeLinksToFollow:
			print("\tGetting product type list at " + typeLink)
			parser = parse.ProductTypeParser()
			response = session.get(typeLink)
			productConfigurations += parser.parseItems(response.text)

		# 	break
		# break


	file_output(productConfigurations, section + ".csv")