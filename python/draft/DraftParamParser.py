# DraftParamParser.py
# Copyright Thinkbox Software 2011-2012
# Author: Mike Yurick
# Edited by: Jon Gaudet
# 
# This script provides functionality for parsing Draft related parameters.
# Essentially, you provide a dict with param names and the type of param
# that you are expecting, and it searches the provided file or command line
# for those arguments and makes an output dict of them.  It throws errors
# when params are missing or when they don't match what is expected.
#
# The two main functions to be used externally are ParseParamFile and
# ParseCommandLine.  They both take an input param dict with entries
# of the form:
#   expectedTypes['<paramName>'] = '<type>'
# where the keys are strings of parameter names, and the values are the
# expected type of the associated parameter.  
#
# These functions will return parameters in a dictionary of the form:
#   params['<paramName>'] = '<value>'
# where '<value>' is type-cast to be of the expected value type.
#
# Alternately, if you don't want to specify the expected parameters, you can
# instead use ParseParamFile_TypeAgnostic or ParseCommandLine_TypeAgnostic
#
# TODO:
# ParseCommandLine will check for a paramFile='<path>' argument and will
# call ParseParamFile if it is present, overriding any arguments in the
# parameter file with any commandline arguments of the same name/type.

import string
import re
import os
import xml.etree.ElementTree as ElemTree

# A utility function for converting strings that are tuples of strings 
# into a list of strings while handling any malformations and tossing 
# informative errors
def StringTupleToStringList( s, n ) :
    if ( not (s[0] == '(') or not (s[-1] == ')') ) :
        raise StandardError('Tuple must be enclosed in parentheses: "( )".');
    sList = s[1:-1].split(',')
    if ( not (len(sList) == n) ) :
        raise StandardError('Tuple must have ' + str(n) + ' elements.');
    return sList;

# A utility function for converting strings that are tuples of ints 
# into a list of ints while handling any malformations and tossing 
# informative errors
def StringTupleToNumList( s, n ) :
    if ( not (s[0] == '(') or not (s[-1] == ')') ) :
        raise StandardError('Tuple must be enclosed in parentheses: "( )".');
    sList = s[1:-1].split(',')
    if ( not (len(sList) == n) ) :
        raise StandardError('Tuple must have ' + str(n) + ' elements.');
    for i in range(0,n) :
        try :
            sList[i] = int(sList[i]);
        except ValueError :
            try :
                sList[i] = float(sList[i])
            except ValueError :
                raise StandardError('Tuple elements must be integers or floats.  Element ' + str(n) + ' is not: ' + sList[i]) ;
    return sList;

#This function will tokenize a string representation of a tuple, skipping commas that are inside of sub-tuples
def TokenizeTupleString( strTuple ):
    tokens = []
    stackCounter = 0
    lastComma = -1
    
    #go through the string char by char, and keep track of parentheses
    for i in range( 0, len(strTuple) ):
        if strTuple[i] == '(':
            stackCounter += 1
        elif strTuple[i] == ')':
            stackCounter -= 1
        elif strTuple[i] == ',' and stackCounter == 0:
            tokens.append( strTuple[ lastComma + 1 : i ] )
            lastComma = i
            
    tokens.append( strTuple[ lastComma + 1 : len(strTuple) ] )
            
    return tokens

#Will try to parse the given argument as the type
def TypeCastArg( expectedType, arg ):
    arg = arg.strip()
    
    if expectedType == '<string>':
        return str(arg)
    elif expectedType == '<int>':
        return int(arg)
    elif expectedType == '<float>':
        return float(arg)
    elif expectedType[0] == '(' and expectedType[-1] == ')':
        if not (arg[0] == '(' and arg[-1] == ')'):
            raise StandardError( "ERROR: Expected a tuple, but found: '%s'" % arg )
        
        #Grab the list of types expected within the tuple
        expectedTypeList = TokenizeTupleString( expectedType[1:-1] )
        argList = TokenizeTupleString( arg[1:-1] )
        
        if ( not len(expectedTypeList) == len(argList) ):
            raise StandardError( "ERROR: Expected a tuple of length %d, but found a tuple of length %d" % ( len(expectedTypeList), len(argList) ) )
        
        list = []
        for i in range( 0, len( argList ) ):
            #recursion!
            list.append( TypeCastArg( expectedTypeList[i], argList[i] ) )
        return list
    else:
        raise StandardError( "ERROR: Unknown or malformed parameter type '%s'" % expectedType )

#Goes through the provided param dictionary and ensures it matches expectations
def ParseParams( expectedTypes, params ):
    
    for key in expectedTypes:
        if ( not key in params ):
            raise StandardError( "ERROR: Expected parameter '%s' was not found." % key )
            
        try:
            params[key] = TypeCastArg( expectedTypes[key], params[key] )
        except:
            raise
            print( "WARNING: Parameter '%s' does not match expected type: %s != %s" % (key, params[key], expectedTypes[key]) )

    return params

#Parses a param file WITHOUT enforcing expected arguments or expected argument types
def ParseParamFile_TypeAgnostic( paramFile ) :
    print "ParseParamFile " + paramFile
    params = {}
    
    try :
        f = open( paramFile, 'r' )
    except :
        print 'Could not open ' + paramFile
        raise
    
    arg = f.readline();
    print( 'Parameter file args:' )
    while ( arg ):
        if arg[-1] == '\n':
            arg = arg[:-1]
        if arg and not arg[0] == '#':
            print ( "arg: " + arg + " " )
            argParts = arg.split( '=', 1 )
            
            if ( len(argParts) < 2 ):
                raise StandardError("Bad argument: " + arg + ".  Should be in the form 'arg=value'.");
            
            key = argParts[0]
            value = argParts[1]
            params[key] = value
            
        arg = f.readline()
        
    return params

#Parses the command line arguments WITHOUT enforcing expected arguments or expected argument types
def ParseCommandLine_TypeAgnostic( argv ):
    params = {}
    
    print( 'Command line args:' )
    for i in range(1, len(argv)):
        print argv[i]
        
        argTokens = argv[i].split( '=', 1 )
        if len( argTokens ) < 2:
            raise StandardError("Bad argument: " + argv[i] + ".  Should be in the form 'arg=value'.")
        
        key = argTokens[0]
        value = argTokens[1]
        params[ key ] = value
        
    if ( 'paramFile' in params ) :
        return ParseParamFile_TypeAgnostic( params['paramFile'] )
        
    return params 

#Parses a param file while enforcing expected arguments or expected argument types
def ParseParamFile( expected, paramFile ) :
    params = ParseParamFile_TypeAgnostic( paramFile )
    
    return ParseParams( expected, params )

#Parses the command line arguments while enforcing expected argument types
def ParseCommandLine( expected, argv ) :
    params = ParseCommandLine_TypeAgnostic( argv )
    
    if ( 'paramFile' in params ) :
        paramFile = params['paramFile']
        del params['paramFile']
        return ParseParamFile( expected, paramFile )
    else :
        return ParseParams( expected, params )

#Replaces Hashs in a Filename with a zero-padded number
def ReplaceFilenameHashesWithNumber( path, n ) :
    sSplit = re.split('#*',path)
    
    # no hashes, just put it in before the file extension
    if ( len(sSplit) > 2 ) :
        raise StandardError("Provided sequence must contain no more than one contiguous sequence of '#' symbols to be replaced.")
    
    s = path
    s.replace( "%", "%%" ) #make sure any existing '%'s are escaped
    if ( len(sSplit) == 2 ) :
        numHashes = len(s) - len(sSplit[0]) - len(sSplit[1])
        s = (sSplit[0] + '%' + str(numHashes) + '.' + str(numHashes) + 'd' + sSplit[1]) % n
    else :
        s = os.path.splitext(s)
        s = (s[0] + "%4.4d" + s[1]) % n
    
    return s

#Converts a FrameRange string (e.g. '1-100') to a list of frame numbers
def FrameRangeToFrames( frameString ):
    frames = []
    frameRangeTokens = re.split( '\s+|,+', frameString )
    
    for token in frameRangeTokens:
        try:
            if ( len(token) > 0 ):
                dashIndex = string.find( token, '-', 1)
                
                if ( dashIndex == -1 ):
                    startFrame = int(token)
                    frames.append( startFrame )
                else:
                    startFrame = int(token[0:dashIndex])
                    
                    m = re.match( "(-?\d+)(?:(x|step|by|every)(\d+))?", token[dashIndex + 1:] )
                    if ( m == None ) :
                        raise StandardError( "Second part of Token failed regex match" )
                    else:
                        endFrame = int(m.group(1))
                        
                        if ( m.group(2) == None ):
                            frames.extend( range(startFrame, endFrame + 1 ))
                        else:
                            dir = 1
                            if startFrame > endFrame:
                                dir = -1
                                
                            byFrame = int(m.group(3));
                            
                            frame = startFrame
                            while (frame * dir) <= (endFrame * dir):
                                frames.append( frame )
                                frame += byFrame * dir
                                
        except:
            print "ERROR: Frame Range token '" + token + "' is malformed. Skipping this token."
            raise
    
    frames = list(set(frames))
    frames.sort()
    
    return frames

#Returns a Dictionary containing the given Job's Property values
def GetDeadlineJobProperties( repoPath, jobID ):
    #normalize the repo path first
    repoPath = os.path.normpath( repoPath )
    
    #build up the xml file name
    jobFileName = os.path.join( repoPath, "jobs", jobID, jobID + ".job" )
    
    #Check to make sure our path leads to an actual file
    if not os.path.isfile( jobFileName ):
        print "ERROR: Could not find the Job File at path: '%s'." % jobFileName
        return {}
    else:
        #read in the data from thefile
        data = None
        file = open( jobFileName, 'r' )
        try:
            strData = file.read()
        except:
            file.close()
            raise
        
        #parse the job file and return the dictionary
        root = ElemTree.fromstring( strData )
        
        jobProps = {}
        for element in root:
            if len( element ) > 0: #has sub elements
                #ExtraInfo KVPs are a bit more complex
                if element.tag == "ExtraInfoKeyValues":
                    propDict = {}
                    for child in element:
                        key = child.findtext( 'Key', None )
                        value = child.findtext( 'Value', '' )
                        
                        if key != None:
                            propDict[key] = value
                    jobProps[ element.tag ] = propDict
                else: #just treat it as a list
                    propList = []
                    for child in element:
                        propList.append( child.text )
                        
                    jobProps[ element.tag ] = propList
            else: #simple element
                jobProps[ element.tag ] = element.text
        
        return jobProps

def SplitDataType( dataTypeString ):
    m = re.match( r"^([0-9]+)([a-z]*)$", dataTypeString, re.I )
    if ( m == None or m.group(1) == '0' ) :
        raise StandardError( "Error: Invalid data type: " + dataTypeString + ". A valid data type is made of a strictly positive number followed by an optional group of letters." )
    
    return  m.groups()

