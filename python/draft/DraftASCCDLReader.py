import Draft
import xml.dom.minidom

def ReadASCCDL( filename, raiseExceptionOnError=True ):
    '''Read an xml-formatted ASC CDL file, extract the slope, offset, power and 
    saturation, and return a Draft ASC CDL LUT.  
    Parameters:  
        filename:  name of the ASC CDL file.
        raiseExceptionOnError (optional):  whether to raise an exception 
            (default), or warn and continue, if there are any problems with the 
            ASC CDL file.
    Returns:  a Draft.LUT object, or None
    '''
    
    asccdllut = None
    try:
        cdl = xml.dom.minidom.parse( filename )
        
        slope = cdl.getElementsByTagName( "Slope" )[0].firstChild.nodeValue.split()
        offset = cdl.getElementsByTagName( "Offset" )[0].firstChild.nodeValue.split()
        power = cdl.getElementsByTagName( "Power" )[0].firstChild.nodeValue.split()
        saturation = cdl.getElementsByTagName( "Saturation" )[0].firstChild.nodeValue.split()
        
        for i in range( 0,3 ): 
            slope[i]=float( slope[i] )
            offset[i]=float( offset[i] )
            power[i]=float( power[i] )
        
        saturation = float( saturation[0] )
        
        asccdllut = Draft.LUT.CreateASCCDL( slope, offset, power, saturation )
    except Exception as e:
        if raiseExceptionOnError:
            raise e
        else:
            print "WARNING:  unable to process requested ASC CDL file, continuing without one.  Error message: ", e
    
    return asccdllut
