#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    AcousticModem.ATM900
    ~~~~~~~~~~~~~~~~~~~~

    An ATM-900/UDB-9400 Acoustic Modem interface
    .. moduleauthor:: Hamilton kibbe
    :copyright: (c) 2012
    :license: All Rights Reserved.

"""
from time import sleep

# debian: apt-get install pyserial
from serial import Serial as ser

class ATM900(object):
    """Teledyne Benthos ATM-900 Acoustic Modem Class.

    Class for interfacing with a Teledyne Benthos ATM-900 and UDB-9400
    series Acoustic Telemetry Modems.
    """
    def __init__(self, serial_port, baud_rate=None):
        """Initializes an acoustic modem.

        :param serial_port: The serial port that the modem is connected to.
        :type serial_port: str.
        :param baud_rate: The current baud rate setting of the modem.
        :type baud_rate: int.
        :returns: An initialized and connected AcousticModem.
        :rtype: AcousticModem.
        :raises: ValueError, IOError
        """
        self.available_baud_rates = [1200, 2400, 4800, 9600, 19200,
                                     57600, 115200]
        self._config_mode = False
        self.serial_port = serial_port
        if baud_rate in self.available_baud_rates:
            self.baud_rate = baud_rate
        else:
            raise ValueError('Invalid baud rate selected. Valid rates are \
            1200, 2400, 4800, 9600, 19200, 57600, or 115200')
        if baud_rate is None:
            for rate in self.available_baud_rates:
                self.modem = ser(self.serial_port, rate, timeout=1.0)
                if self._isConnected():
                    break
                else:
                    self.modem.close()
            if not self.modem.isOpen():
                raise IOError('Failed to detect acoustic modem')
        else:
            self.modem = ser(self.serial_port, self.baud_rate, timeout=1.0)
        self.modem.write('ATO\r\n')
        self._config_mode = False
        self.P1EchoChar = False


    def _configMode(self):
        """ Put the modem into config mode.

        :raises: IOError
        """
        # Check current mode.
        if self._config_mode:
            return
        # Switch to config mode
        sleep(1.0)  # Required timing
        self.modem.write('+++')
        sleep(0.5)  # Wait for response

        # Check the modem's response
        response = self.modem.read(self.modem.inWaiting())
        if '\r\n' in response:
            self._config_mode = True
        else:
            self._config_mode = False
            raise IOError('Entering configuration mode failed.')


    def _onlineMode(self):
        """ Put the modem into online mode.

        :raises: IOError
        """
        # Check current mode
        if not self._config_mode:
            return

        # Switch to online mode
        self.modem.write('ATO\r\n')
        sleep(0.5)

        # Check the modem's response
        response = self.modem.read(self.modem.inWaiting())
        if response.find('\r\n') != -1:
            self._config_mode = False
        else:
            self._config_mode = True
            raise IOError('Entering online mode failed.')


    def _atCommand(self, command, value=None):
        """ Executes an AT Command.

        Puts the modem into config mode if necessary and sends an AT command.
        Returns the response from the modem as a list of strings corresponding
        to each line received.

        :param command: An AT command. <CR><LF> is appended if needed
        :type command: str.
        :param value: If a value is passed to the function, it will set the 
            passed parameter to 'value', e.g. ``_atCommand('@P1Baud',9600)`` 
            sends ``@P1Baud=9600`` to the modem.
        :type value: str, int, float.
        :returns: The lines received from the modem.
        :rtype: list.
        """
        # Switch to config mode if we aren't already'
        if not self._config_mode:
            try:
                self._configMode()
            except IOError:
                return

        # If a value is passed, add the value to the modem AT command string
        if value is not None:
            command.rstrip('\r\n')
            command += ('=' + str(value))
        # Append return
        if '\r\n' not in command:
            command += '\r\n'
        self.modem.write(command)
        sleep(0.5)  # Wait for response

        # Return the modem's'
        return [x.rstrip(' ') for x in self.modem.read(self.modem.inWaiting())\
        .strip('\r\n ').split('\r\n')]


    def _isConnected(self):
        """ Check for connected modem

        :returns: True if the modem is connected, false otherwise
        :rtype: bool.
        """
        self._configMode()
        if self._config_mode is True:
            self._onlineMode()
            return True
        else:
            return False


    def _setEnable(self, cmd, enable):
        if enable is True:
            self._atCommand(cmd, 'Ena')
        elif enable is False:
            self._atCommand(cmd, 'Dis')
        else:
            raise TypeError('Invalid parameter, enable must be a bool')
            
    def close(self):
        """ Close the serial port
        """
        self.modem.close()


    def write(self, data):
        """ Transmit data over the acoustic modem.
        
        :raises: ValueError
        """
        if self._config_mode:
            try:
                self._onlineMode()
            except IOError:
                return
        self.modem.write(data)


    def read(self, chars=None):
        """ Read from modem.

        :param chars:   the number of characters to read. will read all
            available characters if chars is not specified
        :type chars: int.
        :returns: Characters read from modem
        :rtype: str.
        :raises: ValueError
        """
        if self._config_mode:
            try:
                self._onlineMode()
            except IOError:
                return
        if chars is None:
            chars = self.modem.inWaiting()
        return self.modem.read(chars)


    def readline(self):
        """Read a line from the modem.

        :returns: A single line read from the modem
        :rtype: str.
        :raises: ValueError
        """
        if self._config_mode:
            try:
                self._onlineMode()
            except IOError:
                return
        return self.modem.readline()


    def reboot(self):
        """ Reboot the firmware of the local modem
        
        """
        self._atCommand('ATES')


    def writeSettings(self):
        """ Write current modem settings to flash
        
        """
        self._atCommand('AT&W')


    @property
    def serialNo(self):
        """ The modem's serial number (read-only)

        :rtype: int.
        """
        version = self.version
        serStr = version[3]
        return int(serStr.split(':')[1].strip(' '))


    @property
    def version(self):
        """The modem's firmware version (read-only)

        :rtype: list.
        """
        return self._atCommand('ATI')[0:-1]


    @property
    def voltage(self):
        """ The modem's battery voltage (read-only)

        :rtype: float.
        """
        return float(self._atCommand('ATV')[1].split('=')[1].strip(' V'))


    @property
    def temp(self):
        """ The modem's temperature in degrees C(read-only)

        :rtype: float.
        """
        return float(self._atCommand('ATV')[2].split('=')[1].strip(' C'))


    @property
    def mode(self):
        """ The modem's mode (read-only)

        :rtype: list
        """
        return self._atCommand('ATC')


    @property
    def P1Baud(self):
        """ Serial port 1 baud rate

        :param rate: 
            Available baud rates are:
                * 1200
                * 2400
                * 4800
                * 9600
                * 19200
                * 57600
                * 115200

        :type rate: int.
        :rtype: int.
        :raises: ValueError.
        """
        return int(self._atCommand('@P1Baud')[0])


    @P1Baud.setter
    def P1Baud(self, rate):
        if rate not in self.available_baud_rates:
            raise ValueError('Invalid baud rate selected. Valid rates are \
            1200, 2400, 4800, 9600, 19200, 57600, or 115200')
        else:
            self.baud_rate = rate
            self._atCommand('@P1Baud', rate)
            self.modem.close()
            self.modem = ser(self.serial_port, self.baud_rate, timeout=1.0)


    @property
    def P1EchoChar(self):
        """Serial port 1 echo enable/disable

        .. note::
            This should be set to *False* if you are using this API to read
            modem parameters.  If it is set to *TRUE* you will be unable to
            read parameters from the modem.

        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@P1EchoChar')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False


    @P1EchoChar.setter
    def P1EchoChar(self, enable):
        self._setEnable('@P1EchoChar', enable)

    @property
    def P1FlowCtrl(self):
        """ Serial port 1 flow control.

        .. note::
            The ATM-900 Series Acoustic Telemetry Modems User's manual (Rev. A)
            lists this command as P1FlowCtrl, when the actual command is
            P1FlowCtl.  This method uses ``@P1FlowCtl`` when communicating with
            the modem, but the method name remains ``P1FlowCtrl`` for
            consistency with the User's Manual 
                
        :param setting: 
            Options are:
            
                0  (None):
                    Selects no handshaking and turns off the RS_232 driver for 
                    serial port 1 when the modem is in the lowpower state.
                1  (SW):
                    Selects software XON/XOFF handshaking and turns off the
                    RS-232 driver for serial port 1 when the modem is in the 
                    lowpower state.
                2  (HW):
                    Selects hardware RTS/CTS handshaking and leaves the RS-232 
                    driver for serial port 1 turned on when the modem is in the 
                    lowpower state. However, the modem draws an additional 2mA 
                    of current which shortens the modem battery pack life.
                3  (HW-LP):
                    Selects hardware RTS/CTS handshaking and turns off the 
                    RS-232 driver for serial port 1 when the modem is in the 
                    lowpower state. Therefore when the modem is in the lowpower 
                    state, there is no handshaking.
                    
        :type setting:  int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@P1FlowCtl')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @P1FlowCtrl.setter
    def P1FlowCtrl(self, setting):
        if setting not in range(0,4):
            raise ValueError('Invalid parameter, valid settings are 0-3')
        else:
            self._atCommand('@P1FlowCtl', setting)


    @property
    def P1Protocol(self):
        """ Serial port 1 protocol.
        
        :param protocol: 
            Options are:
            
                0
                    RS-232
                1
                    RS-422
        :type protocol: int.
        :rtype: int, str.
        :raises:        ValueError
        """
        response =self._atCommand('@P1Protocol')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @P1Protocol.setter
    def P1Protocol(self, protocol):
        if protocol not in range(0,2):
            raise ValueError('Invalid parameter, valid protocols are 0 or 1')
        else:
            self._atCommand('@P1Protocol', protocol)


    @property
    def P1StripB7(self):
        """ Serial port 1 strip bit 7 enable
        
        :type enable: bool.
        :rtype: bool
        :raises: TypeError
        """
        response = self._atCommand('@P1StripB7')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @P1StripB7.setter
    def P1StripB7(self, enable):
        self._setEnable('@P1StripB7', enable)

    @property
    def P2Baud(self):
        """ Serial port 2 baud rate

        :param rate: 
            Available baud rates are:
                * 1200
                * 2400
                * 4800
                * 9600
                * 19200
                * 57600
                * 115200

        :type rate: int.
        :rtype: int.
        :raises: ValueError.
        """
        return int(self._atCommand('@P2Baud')[0])


    @P2Baud.setter
    def P2Baud(self, rate):
        if rate not in self.available_baud_rates:
            raise ValueError('Invalid baud rate selected. Valid rates are \
            1200, 2400, 4800, 9600, 19200, 57600, or 115200')
        else:
            self.baud_rate = rate
            self._atCommand('@P2Baud', rate)
            self.modem.close()
            self.modem = ser(self.serial_port, self.baud_rate, timeout=1.0)


    @property
    def P2EchoChar(self):
        """ Serial port 2 echo enable/disable

        .. note::
            This should be set to *False* if you are using this API to read
            modem parameters.  If it is set to *TRUE* you will be unable to
            read parameters from the modem.
            
        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@P2EchoChar')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @P2EchoChar.setter
    def P2EchoChar(self, enable):
        self._setEnable('@P2EchoChar', enable)

    @property
    def P2FlowCtrl(self):
        """ Serial port 2 flow control.

        .. note::
            The ATM-900 Series Acoustic Telemetry Modems User's manual (Rev. A)
            lists this command as P2FlowCtrl, when the actual command is
            P1FlowCtl.  This method uses ``@P2FlowCtl`` when communicating with
            the modem, but the method name remains ``P2FlowCtrl`` for
            consistency with the User's Manual

        :param setting: 
            Options are:
            
                0  (None):
                    Selects no handshaking and turns off the RS_232 driver for 
                    serial port 1 when the modem is in the lowpower state.
                1  (SW):
                    Selects software XON/XOFF handshaking and turns off the
                    RS-232 driver for serial port 1 when the modem is in the 
                    lowpower state.
                2  (HW):
                    Selects hardware RTS/CTS handshaking and leaves the RS-232 
                    driver for serial port 1 turned on when the modem is in the 
                    lowpower state. However, the modem draws an additional 2mA 
                    of current which shortens the modem battery pack life.
                3 (HW-LP):
                    Selects hardware RTS/CTS handshaking and turns off the 
                    RS-232 driver for serial port 1 when the modem is in the 
                    lowpower state. Therefore when the modem is in the lowpower 
                    state, there is no handshaking.
                    
        :type setting:  int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@P2FlowCtl')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @P2FlowCtrl.setter
    def P2FlowCtrl(self, setting):
        if setting not in range(0,4):
            raise ValueError('Invalid parameter, valid settings are 0-3')
        else:
            self._atCommand('@P2FlowCtl', setting)


    @property
    def P2StripB7(self):
        """ Serial port 2 strip bit 7 enable
        
        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@P2StripB7')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @P2StripB7.setter
    def P2StripB7(self, enable):
        self._setEnable('@P2StripB7', enable)
        
    @property
    def SyncPPS(self):
        """ PPS clock source.

        :param setting: 
            Options are:
                0  (Off):
                    The date and time are driven from the internal real-time 
                    clock, and the RX and TX time stamps, which are shown at 
                    verbose level 3, will be at a 1.56 ms time accuracy.
                1  (Ext0):
                    The real-time clock is externally driven. Contact Teledyne 
                    Benthos for further information.
                2  (RTC):
                    The date and time are driven from the internal real-time 
                    clock, and the RX and TX time stamps, which are shown at 
                    verbose level 3, will be at a 0.1 ms time accuracy. With 
                    this setting the modem is prevented from entering the 
                    lowpower state, which allows the modem to maintain a high 
                    accuracy on the time stamps.
                3  (Ext1):
                    The real-time clock is externally driven. Contact Teledyne 
                    Benthos for further information.
        :type setting:  int.
        :rtype: int, str.
        :raises: ValueError
        """
        response =  self._atCommand('@SyncPPS')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @SyncPPS.setter
    def SyncPPS(self, setting):
        if setting not in range(0, 4):
            raise ValueError('Invalid parameter, valid settings are 0-3')
        else:
            self._atCommand('@SyncPPS', setting)


    @property
    def IdleTimer(self):
        """ Low Power Idle Timer.
        
        :param time: timer as HH:MM:SS
        :type time: str.
        :rtype: str.
        :raises: ValueError
        """
        return self._atCommand('@IdleTimer')[0]


    @IdleTimer.setter
    def IdleTimer(self, time):
        ints = [int(x) for x in time.split(':')]
        if (ints[0] > 23) or (ints[1] > 59) or (ints[2] > 59):
            raise ValueError('Invalid parameter, time must be less than \
            23:59:59')
        else:
            self._atCommand('@IdleTimer', time)


    @property
    def Verbose(self):
        """ Display verbosity.

        :param setting: 
            Options are:
                0 (data):   
                    Only data are displayed
                1 (data/diag):
                    Data and some diagnostic messages are displayed
                2 (data/diag/rcv):
                    Data, most diagnostic messages, and received data 
                    statistics are displayed
                3 (data/diag/rcv/stat):
                    Data, additional diagnostic messages, and received data 
                    statistics are displayed
                4 (factory):
                    For factory use only
                
        :type setting:  int.
        :rtype: int, str.
        :raises: ValueError
        """
        response =  self._atCommand('@Verbose')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @Verbose.setter
    def Verbose(self, setting):
        if setting not in range(0, 5):
            raise ValueError('Invalid parameter, valid settings are 0-4')
        else:
            self._atCommand('@Verbose', setting)


    @property
    def Prompt(self):
        """ Prompt setting.

        :param setting: 
            Options are:
                0 ( ):
                    No command prompt
                1 (>):   
                    The ">" character
                2 (user):  
                    Privilege level
                3 (user>): 
                    Privilege level and ">"
                4 (:1):   
                    Command history  number
                5 (:1>):  
                    Command history number and ">"
                6 (user:1):  
                    Privilege level and command history number
                7 (user:1>):   
                    Privilege level, command history number and ">"
        :type setting:  int.
        :rtype: int, str.
        :raises: ValueError
        """
        response =  self._atCommand('@Prompt')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @Prompt.setter
    def Prompt(self, setting):
        if value not in range(0, 8):
            raise ValueError('Invalid parameter, valid values are 0-7')
        else:
            self._atCommand('@Prompt', value)


    @property
    def CMWakeHib(self):
        """ Compact modem wakeup period.

        :param period: 
            Options are::
            
                -1   Off
                0    2sec.
                1    3sec.
                2    4sec.
                3    6sec.
                4    8sec.
                5    12sec.
                6    16sec.
                7    24sec.
                8    32sec.
                9    48sec.
                11  96sec.
                
        :type period: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@CMWakeHib')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @CMWakeHib.setter
    def CMWakeHib(self, period):
        if value not in [range(-1,10),11]:
            raise ValueError('Invalid parameter, valid values are 0-9 or 11')
        else:
            self._atCommand('@CMWakeHib', value)


    @property
    def CMFastWake(self):
        """Fast compact modem wakeup scheme enable/disable.
        
        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@CMFastWake')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @CMFastWake.setter
    def CMFastWake(self, enable):
        self._setEnable('@CMFastWake', enable)


    @property
    def CPBoard(self):
        """ Coprocessor board presence

        :param setting: 
            Options are:
                0  (Off):
                    Disables the coprocessor board.
                1  (Powersave):
                    Enables the coprocessor board, but places it in a low power 
                    state in between receiving data packets. The board will be 
                    powered up in full when a newdata packet is received and 
                    put back into its low power state after receiving the 
                    packet.
                2  (AlwaysOn):
                    Enables the coprocessor board, keeping it fully powered at 
                    all times.
                3  (Program):
                    Enables the coprocessor board but does not establish 
                    communications with it. This setting is used only for 
                    updating the firmware on the board.
        :type setting:  int.
        :rtype: int, str.
        :raises: ValueError
        """
        response =  self._atCommand('@CPBoard')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @CPBoard.setter
    def CPBoard(self, setting):
        if setting not in range(0, 4):
            raise ValueError('Invalid parameter, valid settings are 0-3')
        else:
            self._atCommand('@CPBoard', setting)


    @property
    def AcData(self):
        """ Output or store received data

        :param setting: 
            Options are:
                0  (UART):
                    Data received over the acoustic link are output over the 
                    serial interface.
                1  (Datalog):
                    Data received over the acoustic link are stored in the data 
                    logger.
                2  (UART+Datalog):
                    Data received over the acoustic link are both output over 
                    the serial interface and stored in the data logger.
        :type setting:  int.
        :rtype: int, str.
        :raises:        ValueError
        """
        response = self._atCommand('@AcData')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @AcData.setter
    def AcData(self, setting):
        if setting not in range(0, 3):
            raise ValueError('Invalid parameter, valid settings are 0-3')
        else:
            self._atCommand('@AcData', setting)


    @property
    def AcStats(self):
        """ Store received data and time stamps.

        :param setting: 
            Options are:
                0  (Off):
                    Statistics and time stamps for data received over the 
                    acoustic link are not stored in the data logger memory.
                1  (Stats):
                    Statistics for data received over the acoustic link are 
                    stored in the data logger memory.
                4  (TimeStamp):
                    Time stamps for data received over the acoustic ink are 
                    stored in the data logger memory.
                5  (Stats+Time): 
                    Statistics and time stamps for data received over the 
                    acoustic link are stored in the data logger memory.
                    
        :type setting:  int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@AcStats')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @AcStats.setter
    def AcStats(self, setting):
        if setting not in [0, 1, 4, 5]:
            raise ValueError('Invalid parameter, valid settings are 0, 1, 4 \
            or 5')
        else:
            self._atCommand('@AcStats', setting)


    @property
    def RingBuf(self):
        """ Ring buffer enable/disable.
        
        :type enable:   bool.
        :rtype: bool.
        :raises: TypeError.
        """
        response = self._atCommand('@RingBuf')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @RingBuf.setter
    def RingBuf(self, enable):
        self._setEnable('@RingBuf', enable)

    @property
    def SubBlks(self):
        """ The number of sub-blocks to transmit

        :type count: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@SubBlks')[0])


    @SubBlks.setter
    def SubBlks(self, count):
        if count not in range(1, 16):
            raise ValueError('Invalid parameter, valid counts are 0-16')
        else:
            self._atCommand('@SubBlks', count)


    @property
    def LogMode(self):
        """ Data storage mode.

        :param mode: 
            Options are:
                0  (FwdDelay):
                    Once characters are received on the serial interface, if no 
                    more characters are received for the amount of time 
                    configured by the FwdDelay configuration parameter, a 
                    discrete record is created and the characters are stored in 
                    the data logger memory.
                1  (Sentinel):
                    When the ASCII code of a character received on the serial 
                    interface matches the setting of the Sentinel configuration 
                    parameter, a discrete record is created and subsequently 
                    received characters are stored in the data logger memory.
                2  (ChrCount):
                    When the number of characters received on the serial 
                    interface matches the number configured by the setting of 
                    the ChrCount configuration parameter, a discrete record is 
                    created and the characters are stored in the data logger 
                    memory.
        :type mode: int
        :rtype: int, str.
        :raises:    ValueError
        """
        response = self._atCommand('@LogMode')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @LogMode.setter
    def LogMode(self, mode):
        if mode not in range(0, 3):
            raise ValueError('Invalid parameter, valid modes are 0-2')
        else:
            self._atCommand('@LogMode', mode)


    @property
    def Sentinel(self):
        """ Character for data partitioning.

        :type value: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@Sentinel')[0])

    @Sentinel.setter
    def Sentinel(self, value):
        if value not in range(0, 256):
            raise ValueError('Invalid parameter, valid values are 0-255')
        else:
            self._atCommand('@Sentinel', value)


    @property
    def ChrCount(self):
        """ Character count for data partitioning.

        :type count: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@ChrCount')[0])


    @ChrCount.setter
    def ChrCount(self, count):
        if count not in range(0, 4097):
            raise ValueError('Invalid parameter, valid counts are 0-4096')
        else:
            self._atCommand('@ChrCount', count)


    @property
    def LogStore(self):
        """ Data logger storage medium.

        :param medium: 
            Options are:
                0  (Local):  
                    Data are stored in the data logger memory of the modem.
                1  (SDHC):
                    Data are stored in a secure digital high capacity(SDHC) 
                    card. Currently not supported.
        :type medium:   int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@LogStore')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @LogStore.setter
    def LogStore(self, medium):
        if medium not in range(0, 2):
            raise ValueError('Invalid parameter, valid media are 0 or 1')
        else:
            self._atCommand('@LogStore', medium)


    @property
    def DataRetry(self):
        """ Data retry enable/disable.

        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@DataRetry')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @DataRetry.setter
    def DataRetry(self, enable):
        self._setEnable('@DataRetry', enable)
    
    @property
    def AcRspTmOut(self):
        """ Acoustic response time out in seconds.

        :type value: float.
        :rtype: int.
        :raises: ValueError.
        """
        return float(self._atCommand('@AcRspTmOut')[0])


    @AcRspTmOut.setter
    def AcRspTmOut(self, value):
        if value not in [x * 0.5 for x in range(4, 200)]:
            raise ValueError('Invalid parameter, valid timeouts are 2-99.5 in \
            0.5 second intervals')
        else:
            self._atCommand('@AcRspTmOut', value)


    @property
    def OpMode(self):
        """ Modem operating Mode.

        :param mode: 
            Options are:
                0 (Command):
                    Command mode
                1 (Online): 
                    Online mode
                2 (Datalog):
                    Datalog mode
        :type mode: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@OpMode')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @OpMode.setter
    def OpMode(self, mode):
        if mode not in range(0, 3):
            raise ValueError('Invalid parameter, valid modes are 0-2')
        else:
            self._atCommand('@Opmode', mode)


    @property
    def DevEnable(self):
        """ Device Enable Performance.

        :param mode: 
            Options are:
                0  (Auto):
                    The device enable output is set automatically for character 
                    output and chan also be set with the local device enable 
                    (ATTDm) and Remote Device Enable(AT$Xn,m) commands.
                1  (MBARI):
                    Reserved and should not be used
                2  (Manual):
                    The device enable output is set only with the local device 
                    enable(ATTDm) and remote device enable (AT$Xn,m) commands. 
                    It will not be set automatically.
        :type mode: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@DevEnable')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @DevEnable.setter
    def DevEnable(self, mode):
        if mode not in range(0, 3):
            raise ValueError('Invalid parameter, valid modes are 0-2')
        else:
            self._atCommand('@DevEnable', mode)


    @property
    def FwdDelay(self):
        """ Modem forwarding delay in seconds

        :type delay: float.
        :rtype: float.
        :raises: ValueError
        """
        return float(self._atCommand('@FwdDelay')[0])


    @FwdDelay.setter
    def FwdDelay(self, delay):
        if delay not in [x * 0.05 for x in range(0, 101)]:
            raise ValueError('Invalid parameter, valid delays are 0.05-5s in \
            50ms increments')
        else:
            self._atCommand('@FwdDelay', delay)


    @property
    def LocalAddr(self):
        """ Local modem address

        :type addr: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@LocalAddr'))[0]


    @LocalAddr.setter
    def localAddr(self, addr):
        if addr not in range(0, 250):
            raise ValueError('Invalid parameter, valid addresses are 0-249')
        else:
            self._atCommand('@LocalAddr', addr)


    @property
    def RemoteAddr(self):
        """ Remote modem address.

        :type addr: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@LocalAddr'))[0]


    @RemoteAddr.setter
    def RemoteAddr(self, addr):
        if addr not in [range(0, 250), 255]:
            raise ValueError('Invalid parameter, valid addresses are 0-249 or \
            255')
        else:
            self._atCommand('@RemoteAddr', addr)


    @property
    def ShowBadData(self):
        """ Display packet errors enable/disable.

        :type enable:bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@ShowBadData')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @ShowBadData.setter
    def ShowBadData(self, enable):
        self._setEnable('@ShowBadData', enable)
    
    @property
    def StartTones(self):
        """ Play start tones enable/disable.

        :type enable:bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@StartTones')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @StartTones.setter
    def SartTones(self, enable):
        self._setEnable('@StartTones', enable)

    @property
    def TxRate(self):
        """ Transmitting acoustic bit rate.

        :param rate: 
            Options are:
                2  (140): 
                    140 bits/sec MFSK repeated twice with rate 1/2 
                    convolutional coding and 25ms multipath guard period
                3  (300):
                    300 bits/sec MFSK repeated twice with rate 1/2 
                    convolutional coding and 25ms multipath guard period
                4  (600):
                    600 bits/sec MFSK, with rate 1/2 convolutional coding and 
                    25ms multipath guard period
                5  (800):
                    800 bits/sec MFSK, with rate 1/2 convolutional coding and 
                    12.5ms multipath guard period
                6  (1066):
                    1,066 bits/sec MFSK, with rate 1/2 convolutional coding and 
                    3.125ms multipath guard period
                7  (1200):
                    1,200 bits/sec MFSK, with rate 1/2 convolutional coding
                8  (2400):
                    2,400 bits/sec MFSK
                9  (2560):
                    2,560 bits/sec PSK, with rate 1/2 convolutional coding
                10  (5120):
                    5,120 bits/sec PSK, with rate 1/2 convolutional coding
                11  (7680):
                    7,680 bits/sec PSK, with rate 1/2 convolutional coding
                12  (10240):
                    10,240 bits/sec PSK
                13  (15360):
                    15,360 bits/sec PSK
                    
        :type rate: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@TxRate')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @TxRate.setter
    def TxRate(self, rate):
        if rate not in range(2, 14):
            raise ValueError('Invalid parameter, valid rates are 2-13')
        else:
            self._atCommand('@TxRate', rate)


    @property
    def TxPower(self):
        """ Transmit power level.
        
        :param level: 
            Options are:
                1  
                    -21 dB
                2
                    -18 dB
                3
                    -15 dB
                4
                    -12 dB
                5
                    -9 dB
                6 
                    -6 dB
                7
                    3 dB
                8
                    0 dB
                
        :type level:    int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@TxPower')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @TxPower.setter
    def TxPower(self, level):
        if level not in range(1, 9):
            raise ValueError('Invalid parameter, valid levels are 1-8')
        else:
            self._atCommand('@TxPower', level)


    @property
    def WakeTones(self):
        """ Wakeup signal enable/disable.

        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@WakeTones')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @WakeTones.setter
    def WakeTones(self, enable):
        self._setEnable('@WakeTones', enable)

    @property
    def PrintHex(self):
        """ Display data in hex enable/disable.

        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@PrintHex')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return

    @PrintHex.setter
    def PrintHex(self, enable):
        self._setEnable('@PrintHex', enable)
        
    @property
    def StrictAT(self):
        """ AT commands enable/disable.

        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@StrictAT')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @StrictAT.setter
    def StrictAT(self, enable):
        self._setEnable('@StrictAT', enable)
        
    @property
    def InputMode(self):
        """ Single/Dual serial port selection.

        :param mode: 
            Options are:
                1 (Single):
                    The modem will allow only one instrument to be connected to 
                    the modem for the in put of data when the modem is in 
                    Online or Datalogger mode. The instrument must be connected 
                    to serial port 1. Transport information will be transmitted 
                    with the data packets only if @TPortMode=Always.
                2 (Dual):
                    Two instruments can be connected to the modem, one to 
                    serial port 1 and the other to serial port 2. Both serial 
                    ports will input data when the modem is in Online or 
                    Datalogger mode. Transport information will be transmitted 
                    with the data packets.
        :type mode: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@InputMode')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @InputMode.setter
    def InputMode(self, mode):
        if mode not in range(1, 3):
            raise ValueError('Invalid parameter, valid modes are 0 or 1')
        else:
            self._atCommand('@InputMode', mode)


    @property
    def TimedRelease(self):
        """ Elapsed time to release activation in hours.

        :type value: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@TimedRelease'))[0]


    @TimedRelease.setter
    def TimedRelease(self, value):
        if value not in range(0, 1000):
            raise ValueError('Invalid parameter, valid values are 0-999')
        else:
            self._atCommand('@TimedRelease', value)


    @property
    def TPortMode(self):
        """ Routing of data input on serial port 1 and serial port 2.

        :param mode:
            Options are:
                0 (InpMode):
                    Transport addressing is in accordance with the setting of 
                    the InputMode configuration parameter.
                1 (AlwaysOn):
                    Transport addressing is always enabled regardless of the 
                    setting of the InputMode configuration parameter.
        :type mode: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@TPortMode')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @TPortMode.setter
    def TPortMode(self, mode):
        if mode not in range(0, 2):
            raise ValueError('Invalid parameter, valid modes are 0 or 1')
        else:
            self._atCommand('@TPortMode', mode)


    @property
    def SrcP1(self):
        """ Transport address that will be attached to transmitted data that
        are input to serial port 1.

        :param addr: 
            Options are:
                1 (1):
                    The transport address for data input on serial port 1 is 1.
                2 (2):
                    The transport address for data input on serial port 1 is 2.
                3 (3):
                    Reserved
                4 (4):
                    Reserved
        :type addr: int.
        :rtype: int.
        :raises: ValueError
        """
        return self._atCommand('@SrcP1')[0]


    @SrcP1.setter
    def SrcP1(self, addr):
        if addr not in range(1,5):
            raise ValueError('Invalid parameter, valid addresses are 1-4')
        else:
            self._atCommand('@SrcP1', addr)


    @property
    def SrcP2(self):
        """ Transport address that will be attached to transmitted data that
        are input to serial port 2.

        :param addr: 
            Options are:
                1 (1):
                    The transport address for data input on serial port 2 is 1.
                2 (2):
                    The transport address for data input on serial port 2 is 2.
                3 (3):
                    Reserved
                4 (4):
                    Reserved
        :type addr: int.
        :rtype: int.
        :raises: ValueError
        """
        return self._atCommand('@SrcP2')[0]


    @SrcP2.setter
    def SrcP2(self):
        if value not in range(1,5):
            raise ValueError('Invalid parameter, valid addresses are 1-4.')
        else:
            self._atCommand('@SrcP2', value)


    @property
    def Dst1(self):
        """ Serial port on which data received over the acoustic link with
        transport address 1 will be output.

        :param port:
            Options are:
                1 (P1):
                    Data received over the acoustic link with transport address 
                    1 will be output on serial port 1.
                2 (P2): 
                    Data received over the acoustic link with transport address 
                    1 will be output on serial port 2.
        :type port: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@Dst1')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @Dst1.setter
    def Dst1(self, port):
        if port not in range(1, 3):
            raise ValueError('Invalid parameter, valid ports are 1 or 2.')
        else:
            self._atCommand('@Dst1', port)


    @property
    def Dst2(self):
        """ Serial port on which data received over the acoustic link with
        transport address 2 will be output.

        :param port:
            Options are:
                1 (P1):
                    Data received over the acoustic link with transport address 
                    2 will be output on serial port 1.
                2 (P2): 
                    Data received over the acoustic link with transport address 
                    2 will be output on serial port 2.
        :type port: int.
        :rtype: int, str.
        :raises: ValueError
        """
        response = self._atCommand('@Dst2')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @Dst2.setter
    def Dst2(self, port):
        if port not in range(1, 3):
            raise ValueError('Invalid parameter, valid ports are 1 or 2.')
        else:
            self._atCommand('@Dst2', port)


    @property
    def Dst3(self):
        pass


    @Dst3.setter
    def Dst3(self, port):
        pass


    @property
    def Dst4(self):
        pass


    @Dst4.setter
    def Dst4(self, port):
        pass


    @property
    def SimAcDly(self):
        """ Simulated Acoustic Delay in ms

        :type delay: int.
        :returns: int.
        :raises: ValueError
        """
        return int(self._atCommand('@SimAcDly'))


    @SimAcDly.setter
    def SimAcDly(self, delay):
        if delay not in range(0,30001):
            raise ValueError('Invalid parameter, valid delays are 0-30000 ms')
        else:
            self._atCommand('@SimAcDelay', delay)


    @property
    def PktEcho(self):
        """ Test message display enable/disable.

        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@PktEcho')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @PktEcho.setter
    def PktEcho(self, enable):
        if enable is True:
            self._atCommand('@PktEcho', 'Ena')
        elif enable is False:
            self._atCommand('@PktEcho', 'Dis')
        else:
            raise TypeError('Invalid parameter, enable must be a bool')


    @property
    def PktSize(self):
        """ Test message size

        :param size: 
            Options are:
                0 (8B):
                    8-byte message
                1 (32B):
                    32-byte message
                2 (128B):
                    128-byte message
                3 (256B):
                    256-byte message
                4 (512B):
                    512-byte message
                5 (1024):
                    1024-byte message
                6 (2048):
                    2048-byte message
                7 (4096):
                    4096-byte message
        :type size: int.
        :rtype: int, str
        :raises: ValueError
        """
        response = self._atCommand('@PktSize')[0].split('')
        return int(response[0]), response[1].strip(' ()')


    @PktSize.setter
    def PktSize(self, size):
        if size not in range(0,8):
            raise ValueError('Invalid parameter, valid sizes are 0-7')
        else:
            self._atCommand('@PktSize', size)


    @property
    def RcvAll(self):
        """ Test message display enable/disable.

        :type enable: bool.
        :rtype: bool.
        :raises: TypeError
        """
        response = self._atCommand('@RcvAll')[0]
        if 'Ena' in response:
            return True
        elif 'Dis' in response:
            return False
        else:
            return


    @RcvAll.setter
    def RcvAll(self, enable):
        self._setEnable('@RcvAll', enable)

    @property
    def RxFreq(self):
        """ Modem receive frequency.

        :type freq: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@RxFreq'))


    @RxFreq.setter
    def RxFreq(self, freq):
        if freq not in [x*250 for x in range(28, 65)]:
            raise ValueError('Invalid parameter, valid frequencies are \
            7000-16000 in increments of 250')
        else:
            self._atCommand('@RxFreq', freq)


    @property
    def RxThresh(self):
        """ Detected signal standard deviation

        :type threshold: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@RxThresh'))


    @RxThresh.setter
    def RxThresh(self, threshold):
        if threshold not in range(10,257):
            raise ValueError('Invalid parameter, valid thresholds are 10-256')
        else:
            self._atCommand('@RxThresh', threshold)


    @property
    def RxToneDur(self):
        """ Modem receive pulse width

        :param duration: 
            Options are:
                0 (12.5ms): 
                    12.5ms
                1 (6.25ms): 
                    6.25ms
                5 (5ms):    
                    5ms
                6 (6ms):    
                    6ms
                7 (7ms):    
                    7ms
                8 (8ms):    
                    8ms
                9 (9ms):    
                    9ms
                10 (10ms):  
                    10ms
                11 (11ms):  
                    11ms
                12 (12ms):  
                    12ms
                13 (13ms):  
                    13ms
                14 (14ms):  
                    14ms
                15 (15ms):  
                    15ms
        :type duration: int.
        :rtype: int, str.
        :raises:        ValueError
        """
        response = self._atCommand('@RxToneDur')[0].split(' ')
        return int(response[0]), response[1].strip(' ()')


    @RxToneDur.setter
    def RxToneDur(self, duration):
        if duration not in [0,1,range(5,16)]:
            raise ValueError('Invalid parameter, valid durations are 0, 1, \
            5-15')
        else:
            self._atCommand('@RxToneDur', duration)


    @property
    def RxLockout(self):
        """ Modem lockout time in ms

        :type time: int.
        :rtype: int.
        :raises: ValueError
        """
        return int(self._atCommand('@RxLockout'))

    @RxLockout.setter
    def RxLockout(self, time):
        if time not in range(0,1001):
            raise ValueError('Invalid parameter, valid times are 0-1000ms')
        else:
            self._atCommand('@RxLockout', time)


    @property
    def TxToneDur(self):
        """ Modem transmit pulse width in milliseconds

        :type duration: float.
        :rtype: float.
        :raises: ValueError
        """
        return float(0.1 * int(self._atCommand('@TxToneDur')))


    @TxToneDur.setter
    def TxToneDur(self, duration):
        if duration not in [x*0.1 for x in range(100,251)]:
            raise ValueError('Invalid parameter, valid durations are 10.0 to \
            25.0ms in 0.1ms increments')
        else:
            self._atCommand('@TxToneDur', int(10 * duration))


    @property
    def TAT(self):
        """ Transponder turn-around time

        :type time: float.
        :rtype: float.
        :raises: ValueError
        """
        return float(0.1 * int(self._atCommand('@TAT')))


    @TAT.setter
    def TAT(self, time):
        if time not in [x*0.1 for x in range(0,1001)]:
            raise ValueError('Invalid parameter, valid times are 0 to 100.0ms \
            in 0.1ms increments')
        else:
            self._atCommand('@TAT', int(10 * time))



