# This is the content of the script in my CSV Point Cook HDA. The writing to file logic in the export() function is adapted from
# https://github.com/sideeffects/GameDevelopmentToolset/blob/Development/otls/rop_csv_exporter.hda/gamedev_8_8Driver_1rop__csv__exporter/PythonModule
# 
# The values inputted in the HDA are then passed into this node and the CSV is cooked. The user is able to include and exclude
# point attributes with the same logic as in other nodes using asterisks and carets.

import hou, csv, os

toremove, attrlist, finalattribs, attribs, inputList = [], [], [], [], []
component_suffixes = ['.x', '.y', '.z', '.w']
path = ""

def setup():
    global node
    node = hou.pwd()
    global geo
    geo = node.geometry()

    connection = node.inputConnections()[0]

    # get everything from Houdini
    selfNode = connection.outputNode()
    global inputList
    inputList = selfNode.parm("attrs").eval().split()
    global path
    path = selfNode.parm("path").eval()
    nodeToExport = connection.inputNode()
    global attribs
    attribs = nodeToExport.geometry().pointAttribs()
    
    # Asterisk comes first, then caret in the sorted list
    inputList.sort()
    if(len(inputList) == 0):
        inputList = ["P"]

    # Make directories if they do not already exist
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    return nodeToExport

# Returns a list of two lists. Values that had an asterisk first (*value) are in
# the first list, and the values that had an asterisk last (value*) are in
# the second list.
def getAsteriskedValues(toeval):
    startStrings = [x[1:] for x in toeval if x[0] == "*"]
    endStrings = [x[:len(x)-1] for x in toeval if x[len(x)-1] == "*"]
    return [startStrings, endStrings]

def startswithany(word, tocheck):
    for pre in tocheck:
        if word.startswith(pre):
            return True
    return False

def endswithany(word, tocheck):
    for suf in tocheck:
        if word.endswith(suf):
            return True
    return False

def buildList(tocheck):
    # Evaluate strings that have an asterisk in them
    values = getAsteriskedValues(tocheck)
    startStrings = values[0]
    endStrings = values[1]
    
    # Make list of attributes that need to be isolated and make the final list
    buildList = [x for x in attribs if x.name() in tocheck]
    buildList += [x for x in attribs if startswithany(x.name().lower(), endStrings)]
    buildList += [x for x in attribs if endswithany(x.name().lower(), startStrings)]

    return buildList

def getAttrs():
    # Check if there is an *
    if "*" in inputList:
        # Step 1: check for carats
        toremove = [x[1:] for x in inputList if "^" in x]

        attrsToRemove = buildList(toremove)
        
        finalattribs = [x for x in attribs if x not in attrsToRemove]
        
    else:
        toInclude = [x for x in inputList if not "^" in x]
        attrsToInclude = buildList(toInclude)
        
        finalattribs = [x for x in attribs if x in attrsToInclude]
    exportattrs = [x.name() for x in finalattribs]
    return exportattrs
        
def export():
    nodeToExport = setup()
    exportattrs = getAttrs()

    pts = nodeToExport.geometry().points()

    global path
    # open the file for writing
    with open(path, 'w') as csvfile:
        # construct the csv writer object
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # write the first line, which is the header with all of the attributes
        attributes = ["ptnum"]

        # grab all of the point attributes, and if it's a vector attribute, add multiples
        for point_attr_name in exportattrs:
            point_attr = None
            if geo.findPointAttrib(point_attr_name) != None:
                point_attr = geo.findPointAttrib(point_attr_name)
                if point_attr.size()>1:
                    for i in range(point_attr.size()):
                        attributes.append(point_attr.name() + component_suffixes[i])
                else:
                    attributes.append(point_attr.name())

        # write the first row to file
        writer.writerow(attributes)

        # iterate through each point in the geo and write out a line per point
        for point in geo.points():

            # build an array of data
            point_data = [point.number()]

            # iterate through all attributes breaking up vector attributes if needed
            for point_attr_name in exportattrs:
                point_attr = None
                if geo.findPointAttrib(point_attr_name) != None:
                    point_attr = geo.findPointAttrib(point_attr_name)
                    if point_attr.size()>1:
                        for i in range(point_attr.size()):
                            point_data.append(point.attribValue(point_attr)[i])
                    else:
                        point_data.append(point.attribValue(point_attr))

            # write the line out to the file
            writer.writerow(point_data)
