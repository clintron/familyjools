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
	"calibrated-gems-by-type":					{"url": "http://www.stuller.com/browse/gemstones/shop-by-stone-type/calibrated-gems-by-type/", "parsers": [parse.ProductCategoriesParser, parse.CategoryParser, parse.ProductTypeParser]},
	# "wedding-and-engagement-engagements": 		{"url": "http://www.stuller.com/browse/mountings/wedding-and-engagement/engagements/", "parsers": [parse.CategoryParser, parse.PiecePermutationsParser, parse.PieceParser]}, 
	# "wedding-and-engagement-solitaire": 		"http://www.stuller.com/browse/mountings/wedding-and-engagement/solitaire/",
	# "wedding-and-engagement-3-stone": 			"http://www.stuller.com/browse/mountings/wedding-and-engagement/3-stone/",
	# "rings-gemstone-fashion": 					{"url": "http://www.stuller.com/browse/jewelry/rings/gemstone-fashion/", "parsers": [parse.CategoryParser, parse.ProductTypeParser]},
	# "necklaces-and-pendants-gemstone-fashion": 	"http://www.stuller.com/browse/jewelry/necklaces-and-pendants/gemstone-fashion/",
	# "necklaces-and-pendants-diamond-fashion": 	"http://www.stuller.com/browse/jewelry/necklaces-and-pendants/diamond-fashion/",
	# "diamond-stud-earrings": 					"http://www.stuller.com/diamond-stud-earrings/",
	# "earrings-gemstone-fashion": 				"http://www.stuller.com/browse/jewelry/earrings/gemstone-fashion/",
	# "diamond-fashion-button": 					"http://www.stuller.com/browse/jewelry/earrings/diamond-fashion/button/",
	# "diamond-fashion-drop": 					"http://www.stuller.com/browse/jewelry/earrings/diamond-fashion/drop/",
	# "diamond-fashion-jackets": 					"http://www.stuller.com/browse/jewelry/earrings/diamond-fashion/jackets/",
	# "wedding-and-engagement-anniversary-and-eternity-bands": "http://www.stuller.com/browse/mountings/wedding-and-engagement/anniversary-and-eternity-bands/",
}

for section, sectionParams in sections.items():
	print ("Starting section '%s' at %s" % (section, sectionParams["url"]))

	linksToFollow = [ {"url": sectionParams['url'], "special data": {}} ]
	lastParserClass = sectionParams["parsers"][-1]
	productResults = []

	for parserClass in sectionParams["parsers"]:
		# Links for the next round
		newLinks = []
		for linkData in linksToFollow:
			parser = parserClass(specialData=linkData["special data"])
			print("Downloading parser link: " + linkData["url"])
			response = session.get(linkData["url"])
			
			if parserClass != lastParserClass:
				# Keep adding to the list of links to parse in the next round
				newLinks += parser.parseLinks(response.text)
				break
			else:
				productResults += parser.parseItems(response.text)

		linksToFollow = newLinks
		


	file_output(productResults, section + ".csv")