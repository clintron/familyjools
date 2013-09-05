import csv

#output to csv format
def file_output(dictList,csvFilename):
        with open(csvFilename, 'w', newline='') as csvFile:
                listHeaders = []        
                for productDict in dictList:
                        tempHeaders = []
                        tempHeaders = productDict.keys()
                        for header in tempHeaders:
                                if header not in listHeaders:
                                        listHeaders.append(header) #add unique headers to running list

                listHeadersDict = dict(zip(listHeaders, listHeaders))
                writer = csv.DictWriter(csvFile, listHeaders, restval="", extrasaction="ignore", dialect="excel")
                writer.writerow(listHeadersDict)

                for productDict in dictList:
                        writer.writerow(productDict)                

#if __name__== "__main__":
#        dictList = [{"finish":"rough", "cut":"princess"}, {"cat":"shorthaired", "cut":"bald", "color":"red"}]
#        file_output(dictList, "test3.csv")
