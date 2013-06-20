AcousticModem
=============

Teledyne Benthos ATM-900 and UDB-9400 series modem interface.

It's this easy:

    import AcousticModem
    
    modem = ATM900('com1')
    modem.write('Hello, World!')

    # set remote modem properties
    modem.remotePower(249, 3)
    
    # Get modem properties like this:
    modem.temp
    
    # run the modem link test
    print modem.linkTest(255)
    
    

