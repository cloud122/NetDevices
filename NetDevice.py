#!/usr/bin/env

'''
NetDevices is a class created to automate SSH connections to multiple devices.


usage:
        ./NetDevices.py devicelist commmandlist
        devicelist file contains list of devices to SSH to
        commandlist file contains list of commands to send to all devices.
        use variable_change function to send specific command to different 
        devices like specific config files

main script:
            asks user to login must be same across all devices
            checks password after 3 attempts script is stopped to prevent lock out.

logging:
        error log shows detailed logs
        debug log shows simple success and failures
        hostname.log shows device output stream.

'''

import os.path
import datetime
import time
import traceback
import paramiko
from paramiko_expect import SSHClientInteraction
import readline
from getpass import getpass
import sys
import threading
from multiprocessing.dummy import Pool as ThreadPool

#import pdb; pdb.set_trace()

class NetDevices(object):
    
    #currentDateTime = datetime.datime.now()
    number_of_devices = 0
    failed_login_attempts = 0
    max_failed_login = 3
    successList = []
    failedList = []
    startTime = time.time()

    debugLock = threading.Lock()
    errorLock = threading.Lock()
    successLock = threading.Lock()
    failedLock = threading.Lock()
    resultsLock = threading.Lock()
    outputLock = threading.Lock()
    
    maxNumberOfThreads = 5
    threadLimiter = threading.BoundedSemaphore(maxNumberOfThreads)

    threadCounter = 0

    def locking(cls):
        lock = thread.Lock()
        lock.acquire()
        lock.release()


    @classmethod
    def set_configs(cls , configs):
        pass

    @staticmethod
    def model_check(show_verison):
        pass

    @classmethod
    def promptUserCred(cls):
        from getpass import getpass
        username = get_input("Please enter your username: ")
        password = getpass()

    @classmethod
    def logger_error(cls, *messages):
        import logging
        
        cls.errorLock.acquire()
        try:
            for message in messages:

                cls.formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s') 
                cls.error_logger = logging.getLogger(__name__)
                cls.error_logger.setLevel(logging.WARNING)
                cls.error_file_handler = logging.FileHandler('error.log')
                cls.error_file_handler.setFormatter(cls.formatter)
                cls.error_logger.addHandler(cls.error_file_handler)

                cls.error_logger.error(message)
        finally:
            cls.errorLock.release()

    @classmethod
    def logger_debug(cls, *messages):

        import logging

        cls.debugLock.acquire()
        try:
            for message in messages:

                cls.formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s') 
                cls.debug_logger = logging.getLogger(__name__)
                cls.debug_logger.setLevel(logging.DEBUG)
                cls.debug_file_handler = logging.FileHandler('debug.log')
                cls.debug_file_handler.setFormatter(cls.formatter)
                cls.debug_logger.addHandler(cls.debug_file_handler)

                cls.debug_logger.debug(message)

        finally:
            cls.debugLock.release()



    @classmethod
    def displayOutput(cls, self):
        
        cls.outputLock.acquire()

        print('-'*79 + '\n')
        print('Hostname: ' + self.hostname)
        print('------------' + datetime.datetime.now().strftime('%c') + '------------------\n')
        print('------------------------------<---Output Screen--->----------------------------\n')
        print('-'*79 + '\n')

        for output in self.stdout:
            print(output)

        cls.outputLock.release()


    @classmethod
    def displayResults(cls):

        try:

            with open(os.path.join('./results.log'), 'a') as resultFile:

                print('-'*79 + '\n')
                print('------------------------------<---Results Screen--->---------------------------\n')
                print('-------------------- [' + datetime.datetime.now().strftime('%c') + ' ]-------------------------------\n')
                print('-'*79 + '\n')

                resultFile.write('-'*79 + '\n')
                resultFile.write('------------------------------<---Results Screen--->---------------------------\n')
                resultFile.write('-------------------- [' + datetime.datetime.now().strftime('%c') + ' ]-------------------------------\n')
                resultFile.write('-'*79 + '\n')



                for result in cls.successList:
                    print(result)
                    resultFile.write(result + '\n')

                resultFile.write('\n------------------------------<---Failures--->---------------------------------\n')
                print('\n------------------------------<---Failures--->---------------------------------\n')

                for result in cls.failedList:
                    print(result)
                    resultFile.write(result + '\n')


        except IOError:
            NetDevices.logger_error('results.log file created.')
            NetDevices.logger_debug('results.log file created.')

            with open(os.path.join('results.log'), 'w') as resultFile:

                print('-'*79 + '\n')
                print('------------' + datetime.datetime.now().strftime('%c') + '--------------------------\n')
                print('------------------------------<---Results Screen--->---------------------------\n')
                print('-'*79 + '\n')

                resultFile.write('-'*79 + '\n')
                resultFile.write('------------' + datetime.datetime.now().strftime('%c') + '--------------------------\n')
                resultFile.write('------------------------------<---Results Screen--->---------------------------\n')
                resultFile.write('-'*79 + '\n')

                for result in cls.successList:
                    print(result)
                    resultFile.write(result + '\n')

                resultFile.write('------------------------------<---Failures--->---------------------------------\n')
                print('------------------------------<---Failures--->---------------------------------\n')
                for result in cls.failedList:
                    print(result)
                    resultFile.write(result + '\n')

        print("\nScript took --- %s seconds ---" % (time.time() - cls.startTime) + '\n')

    def threadMethod(function):
        '''
        @threadMethod
        def func_to_be_threaded(self):
            #main body

            see ---> https://stackoverflow.com/questions/19846332/python-threading-inside-a-class
        '''
        def wrapper(*args, **kwargs):

             thread = threading.Thread(target=function, args=args, kwargs=kwargs)
             thread.start()
             return thread

        return wrapper

    def __init__(self, hostname='generic', model='generic', configs="generic", user = 'admin', password = '',timeout=10,display=True):
        self.hostname = hostname
        self.model = model
        self.configs = configs
        self.user = user
        self.password = password
        self.timeout= timeout
        self.display= display
        self.stdout = []
        self.commandList = None
        self.debugList = []
        self.errorList = []


        ###expect prediction
        #self.expect_predict = expect_predict

        ###methods to connect, SSH, telnet, console
        #self.connect_method = connect_method

        NetDevices.number_of_devices +=1

    @threadMethod
    def connect(self, method='SSH'):

        NetDevices.threadLimiter.acquire()
        NetDevices.threadCounter +=1
        NetDevices.logger_debug("\nNumber of threads active: " + str(NetDevices.threadCounter))

        try:
            if method == 'SSH':
                self.remote_conn_pre = paramiko.SSHClient()
                self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                try:
                    self.remote_conn_pre.connect(hostname=self.hostname, port=22, username=self.user,
                                                 password=self.password,timeout=self.timeout,look_for_keys=False)

                except paramiko.ssh_exception.socket.gaierror:
                    print('Connection Timeout or unknown host on: [{}]'.format(self.hostname))
                    NetDevices.failedLock.acquire()
                    NetDevices.failedList.append('Connection Timeout or unknown host on: [{}]'.format(self.hostname))
                    NetDevices.failedLock.release()
                    NetDevices.logger_error('Connection Timeout or unknown host on: [{}]'.format(self.hostname))
                    NetDevices.logger_debug('Connection Timeout or unknown host on: [{}]'.format(self.hostname))
                    return

                except paramiko.ssh_exception.socket.timeout:
                    print('Connection Timeout or unknown host on:  [{}]'.format(self.hostname))
                    NetDevices.failedLock.acquire()
                    NetDevices.failedList.append('Connection Timeout or unknown host on: [{}]'.format(self.hostname))
                    NetDevices.failedLock.release()
                    NetDevices.logger_error('Connection Timeout or unknown host on: [{}]'.format(self.hostname))
                    NetDevices.logger_debug('Connection Timeout or unknown host on: [{}]'.format(self.hostname))
                    return

                ###-----catches authentication failures, limit 2 failures and script will stop

                except paramiko.ssh_exception.AuthenticationException:
                    print('Authentication failed on: ' + self.hostname)
                    NetDevices.failedLock.acquire()
                    NetDevices.failedList.append('Authentication failed on: [{}]'.format(self.hostname))
                    NetDevices.failedLock.release()           
                    NetDevices.logger_error('Authentication failed on: [{}]'.format(self.hostname))
                    NetDevices.logger_debug('Authentication failed on: [{}]'.format(self.hostname))

                    NetDevices.failed_login_attempts += 1

                    print('Number of failed attempts: ',NetDevices.failed_login_attempts)
                    if (NetDevices.failed_login_attempts > NetDevices.max_failed_login):
                        print('Warning!!! Too many authentication failures, danger of your account being locked out!!!')
                        NetDevices.logger_error('Too many failed authentication' + NetDevices.failed_login_attempts  
                                      + 'number of failed attempts, script cancelled.')
                        NetDevices.logger_debug('Too many failed authentication' + NetDevices.failed_login_attempts  
                                      + 'number of failed attempts, script cancelled.')

                        sys.exit('!!!!!!Script will stop!!!!!!')

                except Exception as e:
                    NetDevices.logger_error("Exception: connection error: [{}] Traceback error: {}".format(self.hostname, str(e)))
                    NetDevices.logger_debug()
                    NetDevices.failedLock.acquire()
                    NetDevices.failedList.append('Exception: connection error: [{}]'.format(self.hostname, str(e)))
                    NetDevices.failedLock.release()

                    return

                ###------interact expect starts and enable mode
                try:
                    self.interact = SSHClientInteraction(self.remote_conn_pre, timeout = self.timeout, display = False)
                    print('Connection established on: : [{}]'.format(self.hostname))
                    self.stdout.append(self.interact.current_output)

                    NetDevices.logger_debug('Connection established on: [{}]'.format(self.hostname))
                    
                    self.interact.expect(['.*\#', '.*\>'], timeout=self.timeout)
                    if self.interact.last_match == '.*\>':
                        self.interact.send('enable')
                        self.stdout.append(self.interact.current_output)

                        self.interact.expect('.*assword:*.',timeout=self.timeout)
                        self.interact.send(self.password)
                        self.stdout.append(self.interact.current_output)

                    self.interact.expect(['.*\#', '.*\>'])
                    self.interact.send('terminal length 0')
                    self.stdout.append(self.interact.current_output)

                    if self.interact.last_match == '.*\>':
                        time.sleep(1)
                        self.interact.send('enable')
                        self.interact.expect('.*assword:*.')
                        time.sleep(1)
                        self.stdout.append(interact.current_output)
                        self.interact.send(self.password)
                        self.interact.expect(['.*\#', '.*\>'])
                        self.interact.send('terminal length 0')
                        self.stdout.append(interact.current_output)
                        if self.interact.last_match == '.*\>':
                            self.stdout.append(self.interact.current_output)
                            self.interact.close()
                            print('Failed to enter Enable mode on: [{}]'.format(self.hostname))
                            NetDevices.failedList.append('Failed to enter Enable mode on: [{}]'.format(self.hostname))
                            NetDevices.logger_error('Failed to enter Enable mode on: [{}]'.format(self.hostname))
                            NetDevices.logger_debug('Failed to enter Enable mode on: [{}]'.format(self.hostname))
                            self.remote_conn_pre.close()

                except paramiko.ssh_exception.socket.timeout:
                    self.interact.close()
                    self.remote_conn_pre.close()
                    print('Connection lost...Exception Socket Timeout on: [{}]'.format(self.hostname))
                    NetDevices.failedLock.acquire()
                    NetDevices.failedList.append('Connection lost...Exception Socket Timeout on: [{}]'.format(self.hostname))
                    NetDevices.failedLock.release()
                    NetDevices.logger_error('Connection lost...Exception Socket Timeout on: [{}]'.format(self.hostname))
                    NetDevices.logger_debug('Connection lost...Exception Socket Timeout on: [{}]'.format(self.hostname))
                    return
                
                ###-------------------------------------sending commands------------------------------------------------------------

                if self.model == 'linux':
                    pass
            
                '''
                can pass commands single or pass *commands list
                '''
                if self.remote_conn_pre.get_transport() == None:
                    return
                try:

                    for command in self.commandList:
                        self.interact.send(command)
                        #time.sleep(1)
                        #self.stdout.append(self.interact.current_output)
                        #print(self.interact.current_output)
                        self.interact.expect(['.*\#', '.*\(y/n\) '])
                        #print(self.interact.current_output)
                        self.stdout.append(self.interact.current_output)
                        if self.interact.last_match == '.*\(y/n\) ':
                            self.interact.send('y')
                            self.stdout.append(self.interact.current_output)
                            time.sleep(2)
                            self.interact.expect('.*\#', timeout=180)
                            self.stdout.append(self.interact.current_output)

                    NetDevices.successLock.acquire()
                    try:        
                        NetDevices.successList.append('Commands successful on: [{}]'.format(self.hostname))
                    finally:
                        NetDevices.successLock.release()


                except Exception as e:
                    NetDevices.logger_error("Exception: on sending command on: [{}] Traceback error: {}".format(self.hostname, str(e)))
                    NetDevices.logger_debug()
                    self.stdout.append(self.interact.current_output)
                    NetDevices.failedLock.acquire()
                    NetDevices.failedList.append('Exception: on sending command on: [{}]'.format(self.hostname))
                    NetDevices.failedLock.release()
                    raise
                    #traceback.print_exc()

                self.log_output()

                print('\n' + '-'*79 )
                print('\n' + '-'*79 + '\n')
                print('                   Hostname: ' + self.hostname.strip())
                print('                   ' + datetime.datetime.now().strftime('%c') + '\n')
                print('-'*79 + '\n')
                print('----------------------------<---Commands completed--->-------------------------\n')

                if self.display == True:
                    NetDevices.displayOutput(self)

            NetDevices.logger_error(*self.errorList)
            NetDevices.logger_debug(*self.debugList)
        finally:
            NetDevices.threadLimiter.release()
            NetDevices.threadCounter -= 1

            NetDevices.logger_debug("\nNumber of threads active: " + str(NetDevices.threadCounter))


    def setCommands(self, *commands):
        self.commandList = [command for command in commands]



    def send(self, *commands):
        pass
    

    def log_output(self):
        import datetime
        #currentDateTime = datetime.datime.now()
        
        try:
            if not os.path.exists('./device-logs/'):
                os.makedirs('./device-logs/')
                NetDevices.logger_error('Path created:  ./device-logs/')
                NetDevices.logger_debug('Path created:  ./device-logs/')

            with open(os.path.join('./device-logs/',self.hostname + '.log'), 'a') as outputFile:
                outputFile.write('-'*79 + '\n')
                outputFile.write('Hostname: ' + self.hostname)
                outputFile.write('------------' + datetime.datetime.now().strftime('%c') + '------------------\n')
                outputFile.write('------------------------------<---Output Screen--->----------------------------\n')
                outputFile.write('-'*79 + '\n')

                for outline in self.stdout:
                    outputFile.write(outline + '\n')
            outputFile.close()

        except IOError:
            NetDevices.logger_error(self.hostname + '.log file created.')
            NetDevices.logger_debug(self.hostname + '.log file created.')

            with open(os.path.join('./device-logs/',self.hostname + '.log'), 'w') as outputFile:
                outputFile.write('-'*79 + '\n')
                outputFile.write('Hostname: ' + self.hostname)
                outputFile.write('------------' + datetime.datetime.now().strftime('%c') + '------------------\n')
                outputFile.write('------------------------------<---Output Screen--->----------------------------\n')
                outputFile.write('-'*79 + '\n')

                for outline in self.stdout:
                    outputFile.write(outline + '\n')
            outputFile.close()


    def make_excel(self, command,search_string):
        '''
        function to send a command and capture specific data and enter into excel file.
        '''
        pass

    def variable_change(self, currentDevice, *commands):
        '''
        function to use variable to loop through different devices.  Example: tftp different configs to specific matching device.
        '''
        pass


    def reboot_wait(numberOfDevices, waitTime):
        '''
        function to set a wait time for stagger reboots on hosts to prevent network being overburdened.
        '''
        pass


    def prompt_yes_no(answer='y'):
        '''
        function to pass in y or n when prompt with entering yes or no example, erasing configs.
        '''
        pass


    def tftpServer():

        pass

    def upgradeFirmware():
        if model == x:
            pass


    def file_transfer(method='tftp'):
        pass

    
    def read_output(self):
        pass


    def print_output(self):
        pass

        ##something

    def log_file(self):
        pass

    def login(self):
        pass

    def read_file(self, filename):
        pass

    def write_file(self, filename):
        pass

def main():
    
    threadList = []


    with open(sys.argv[2]) as cmd_file:               
        cmdList = [cmd.strip() for cmd in cmd_file]
                
    cmd_file.close()


    with open(sys.argv[1]) as device_file:
        for device in device_file:
            if not device.strip() or device.startswith('#'):
                continue
            else:
                currentDevice = device.strip()
                commodity_sw = NetDevices(hostname=currentDevice, user='georchan', password='cisco',display=True)
                commodity_sw.setCommands(*cmdList)
                threadList.append(commodity_sw.connect())


        '''lists of threads runs through threads and joins to main '''
        for threadHandle in threadList:
            threadHandle.join()


    NetDevices.displayResults()


main()