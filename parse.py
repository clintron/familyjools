from html.parser import HTMLParser
import requests
import re

session = requests.session()

def setSession(newSession):
	session = newSession

class GemParser(HTMLParser):
	pageSize = 2000

	def parseLinks(self, html):
		'''
		Parse HTML for product types

		Returns a list of dictionaries of the form: {"url": "http://whatever.com/esfef", "special data": {"some var": 234}}
		'''
		self.feed(html)

		return self.linksToFollow

	def parseItems(self, html):
		# Classes which aren't meant to return items will raise an exception if this is called.
		if self.items is None:
			raise Exception("parseItems() called on a class which isn't intended to return items")
		self.feed(html)
		return self.items

	def addLink(self, href, specialData={}):
		if 0 != href.find("http"):
			href = "http://www.stuller.com" + href

		self.linksToFollow.append({"url": href + ("?pageSize=%d" % self.pageSize if self.pageSize > 0 else ""), "special data": specialData})

	def __init__(self, strict=False, specialData={}):
		super().__init__(strict=strict)
		self.linksToFollow = []
		self.specialData = specialData
		self.items = None

	def getAttributeDictionary(self, attrs):
		return {key: value for key, value in attrs}

	def handle_starttag(self, tag, attrs):
		#print("Encountered a start tag :", tag)
		pass

	def handle_endtag(self, tag):
		#print("Encountered an end tag :", tag)
		pass
	def handle_data(self, data):
		#print("Encountered some data  :", data)
		pass


class ProductCategoriesParser(GemParser):
	def handle_starttag(self, tag, attrs):
		#<a onclick="TrackNavigationClick('MiddleBar','stuff');" href="http://youporn.com">penis house</a>
		if (tag == 'a'):
			isALinkWeWant = False
			href = None

			for attribute, value in attrs:
				if attribute == "onclick" and value.find("TrackNavigationClick('MiddleBar'") == 0:
					isALinkWeWant = True
				elif attribute == "href":
					href = value
				
			if isALinkWeWant and href is not None:
				self.addLink(href)


class CategoryParser(GemParser):
	pageSize = 0

	def __init__(self, **extras):
		self.isInCategoryResults = False
		self.isInProductLink = False
		super().__init__(**extras)

	def handle_starttag(self, tag, attrs):
		attributes = self.getAttributeDictionary(attrs)

		if tag == "table" and "id" in attributes and attributes["id"] == "category_results":
			# Determine if we're in the category_table
			self.isInCategoryResults = True
		elif "a" == tag and self.isInCategoryResults:
			self.addLink(attributes["href"])
			self.isInProductLink = True
		elif "img" == tag and self.isInProductLink:
			m = re.search('StullerRender/([^?]+)\?', attributes["src"])
			if m is not None:
				# The most recently added link is associated with this image
				self.linksToFollow[-1]["special data"]["category image id"] = m.group(1)


	def handle_endtag(self, tag):
		if self.isInCategoryResults and tag == "table":
			self.isInCategoryResults = False
		elif self.isInProductLink and tag == "a":
			self.isInProductLink = False


class ProductTypeParser(GemParser):
	pageSize = 0
	
	def __init__(self, **extras):
		super().__init__(**extras)
		self.isInProductTable = False
		self.isInMainDiv = False
		self.isInAGTACell = False
		self.isInForm = False
		self.divDepth = 0
		self.headers = []
		self.items = []
		self.columnId = 0
		self.rowId = 0
		self.currentProduct = {}
		self.productType = None
		self.wantData = False
		self.wantHeader = False
		self.wantH3 = False
		self.detailsLink = None

	def handle_starttag(self, tag, attrs):
		attributes = self.getAttributeDictionary(attrs)
		#print ("Attributes dictionary: " + str(attributes))

		if tag == "table" and "class" in attributes and -1 != attributes["class"].find("nestedTable"):
			# Determine if we're in the data table
			self.isInProductTable = True
			self.rowId = 0
		elif self.isInProductTable:
			if tag == "tr":
				self.detailsLink = None
				self.rowId = self.rowId + 1
				self.columnId = 0
				self.currentProduct = {}
			elif tag == "td" or tag == "th":
				if "td" == tag:
					self.wantData = True
					if "AGTA" == self.headers[self.columnId]:
						self.isInAGTACell = True
				elif "th" == tag:
					self.wantHeader = True
					self.headers.append("header %d" % self.columnId if self.columnId != 1 else "image url")
			elif "a" == tag and self.columnId == 1 and "href" in attributes:
				# This is the link to the page with details for this item
				href = attributes["href"]
				if 0 != href.find("http"):
					href = "http://www.stuller.com" + href
				self.detailsLink = href
		elif tag == "div":
			if "id" in attributes and attributes["id"] == "main":
				self.isInMainDiv = True
				self.divDepth = 0
			else:
				self.divDepth = self.divDepth + 1
		elif tag == "form":
			self.isInForm = True
		elif tag == "h3" and self.isInMainDiv and self.isInForm:
			self.wantH3 = True


	def handle_endtag(self, tag):
		if self.isInProductTable:
			if tag == "table":
				self.isInProductTable = False
			elif tag == "tr":
				if len(self.currentProduct.keys()) > 0:
					if "Quality" in self.currentProduct.keys() \
					and (self.currentProduct["Quality"] == "AA" or self.currentProduct["Quality"] == "AAA"):
						self.currentProduct["Product type"] = self.productType
						if self.detailsLink != None:
							print("\t\t\tGetting image url for product configuration from " + self.detailsLink)
							response = session.get(self.detailsLink)

							# Now extract the URL for the big image
							m = re.search('"ZoomUrl":\\s*"([^"]+?)"', response.text)
							if m is not None:
								url = m.group(1)
								if 0 == url.find("//"):
									url = "http:" + url
								elif 0 == url.find('/'):
									url = "http://www.stuller.com" + url
								elif 0 != url.find("http"):
									#probably a domain without a protocol
									url = "http://" + url
									
								self.currentProduct["image url"] = url
							else:
								print("WARNING: Couldn't find a ZoomUrl at " + href)
						print ("\t\t\tProduct: " + str(self.currentProduct))
						self.items.append(self.currentProduct)
			elif tag == "td" or tag == "th":
				self.columnId = self.columnId + 1
				if tag == "td":
					self.wantData = False
					if self.isInAGTACell:
						self.isInAGTACell = False
				elif tag == "th":
					self.wantHeader = False
			elif tag == "span" and self.isInAGTACell:
				# The span is the only piece of data we want here
				self.wantData = False
		elif tag == "form":
			self.isInForm = False
		elif self.isInMainDiv and tag == "div":
			self.divDepth = self.divDepth - 1
			if self.divDepth == 0:
				self.isInMainDiv = False

	def handle_data(self, data):
		if self.isInProductTable:
			if self.wantHeader:
				self.headers[self.columnId] = data.strip()
			elif self.wantData:
				try:
					self.currentProduct[self.headers[self.columnId]] = data.strip()
				except Exception as e:
					print("Got data failed.  ColumnId: %d headers: %s" % (self.columnId, str(self.headers)))
					raise e
		elif self.wantH3:
			self.productType = data.strip()
			self.wantH3 = False



class PiecePermutationsParser(GemParser):
	'''
	Find request URLs for all the configurations of metals (with stones set) at a page like this:
	http://www.stuller.com/products/122066/?groupId=117430
	'''
	pageSize = 0
	
	def __init__(self, **extras):
		super().__init__(**extras)
		
		self.currentProduct = {}

	def handle_starttag(self, tag, attrs):
		attributes = self.getAttributeDictionary(attrs)
		

	def handle_endtag(self, tag):
		pass


	def handle_data(self, data):
		pass


class PieceParser(GemParser):
	'''
	From the same sort of page parsed by the PiecePermutationsParser, dig out the price and the metal,
	and fill out the .items list.

	http://www.stuller.com/products/122066/?groupId=117430
	'''
	pageSize = 0
	
	def __init__(self, **extras):
		super().__init__(**extras)
		
		self.currentProduct = {}

	def handle_starttag(self, tag, attrs):
		attributes = self.getAttributeDictionary(attrs)
		

	def handle_endtag(self, tag):
		pass

	def handle_data(self, data):
		pass