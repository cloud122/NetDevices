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


class NetDevices:
    
    #currentDateTime = datetime.datime.now()
    number_of_devices = 0
    failed_login_attempts = 0
    max_failed_login = 3
    

    @classmethod
    def set_configs(cls , configs):
    	pass

    @staticmethod
    def model_check(show_verison):
    	pass

    def __init__(self, hostname='generic', model='generic', configs="generic", user = 'admin', password = '',timeout=15):
    	self.hostname = hostname
    	self.model = model
    	self.configs = configs
        self.user = user
        self.password = password
        self.timeout= timeout
        self.stdout = []




        ###expect prediction
        #self.expect_predict = expect_predict

        ###methods to connect, SSH, telnet, console
        #self.connect_method = connect_method

        NetDevices.number_of_devices +=1

    def connect(self, method='SSH'):
        if method == 'SSH':
            self.remote_conn_pre = paramiko.SSHClient()
            self.remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.remote_conn_pre.connect(hostname=self.hostname, port=22, username=self.user,
                                             password=self.password,timeout=self.timeout,look_for_keys=False)

            except paramiko.ssh_exception.socket.gaierror:
                print('Connection Timeout or unknown host on: ' + self.hostname)
                self.logger_error('Connection Timeout or unknown host on: ' +  self.hostname)
                self.logger_debug('Connection Timeout or unknown host on: ' +  self.hostname)
                return

            except paramiko.ssh_exception.socket.timeout:
                print('Connection Timeout or unknown host on: ' + self.hostname)
                self.logger_error('Connection Timeout or unknown host on: ' + self.hostname)
                self.logger_debug('Connection Timeout or unknown host on: ' + self.hostname)
                return

            ###-----catches authentication failures, limit 2 failures and script will stop

            except paramiko.ssh_exception.AuthenticationException:
                print('Authentication failed on: ' + self.hostname)            
                self.logger_error('Authentication failed on: ' + self.hostname)
                self.logger_debug('Authentication failed on: ' + self.hostname)

                NetDevices.failed_login_attempts += 1

                print('Number of failed attempts: ',NetDevices.failed_login_attempts)
                if (NetDevices.failed_login_attempts > NetDevices.max_failed_login):
                    print('Warning!!! Too many authentication failures, danger of your account being locked out!!!')
                    self.logger_error('Too many failed authentication' + NetDevices.failed_login_attempts  
                    	          + 'number of failed attempts, script cancelled.')
                    self.logger_debug('Too many failed authentication' + NetDevices.failed_login_attempts  
                    	          + 'number of failed attempts, script cancelled.')

                    sys.exit('!!!!!!Script will stop!!!!!!')

                return

            ###------interact expect starts and enable mode
            try:
                self.interact = SSHClientInteraction(self.remote_conn_pre, timeout = self.timeout, display = True)
                print('Connection established on: ', self.hostname)
                self.stdout.append(self.interact.current_output_clean)

                self.logger_debug('Connection established on: ' + self.hostname)
                
                self.interact.expect(['.*\#', '.*\>'], timeout=self.timeout)
                if self.interact.last_match == '.*\>':
                    self.interact.send('enable')
                    self.stdout.append(self.interact.current_output_clean)

                    self.interact.expect('.*assword:*.',timeout=self.timeout)
                    self.interact.send(self.password)
                    self.stdout.append(self.interact.current_output_clean)

                self.interact.expect(['.*\#', '.*\>'])
                self.interact.send('terminal length 0')
                self.stdout.append(self.interact.current_output_clean)

                if self.interact.last_match == '.*\>':
                    time.sleep(1)
                    self.interact.send('enable')
                    self.interact.expect('.*assword:*.')
                    time.sleep(1)
                    self.stdout.append(interact.current_output_clean)
                    self.interact.send(self.password)
                    self.interact.expect(['.*\#', '.*\>'])
                    self.interact.send('terminal length 0')
                    self.stdout.append(interact.current_output_clean)
                    if self.interact.last_match == '.*\>':
                        self.stdout.append(self.interact.current_output_clean)
                        self.interact.close()
                        print('Failed to enter Enable mode on: ' , self.hostname)
                        self.logger_error('Failed to enter Enable mode on: ' + self.hostname)
                        self.logger_debug('Failed to enter Enable mode on: ' + self.hostname)
                        self.remote_conn_pre.close()

            except paramiko.ssh_exception.socket.timeout:
                self.interact.close()
                self.remote_conn_pre.close()
                print('\nConnection lost...Exception Socket Timeout')
                self.logger_error('\nConnection lost...Exception Socket Timeout on ' + self.hostname)
                self.logger_debug('\nConnection lost...Exception Socket Timeout on ' + self.hostname)
                return



    def send(self, *commands):

        if self.model == 'linux':
            pass
    	
    	'''
    	can pass commands single or pass *commands list
    	'''
        if self.remote_conn_pre.get_transport() == None:
            return
        try:
            
            for command in commands:
                self.interact.send(command)
                self.stdout.append(self.interact.current_output_clean)
                #print(self.interact.current_output)
                self.interact.expect(['.*\#', '.*\(y/n\) '])
                #print(self.interact.current_output)
                self.stdout.append(self.interact.current_output_clean)
                if self.interact.last_match == '.*\(y/n\) ':
                    self.interact.send('y')
                    self.stdout.append(self.interact.current_output_clean)
                    time.sleep(2)
                    self.interact.expect('.*\#', timeout=180)
                    self.stdout.append(self.interact.current_output_clean)


        except Exception as e:
            self.logger_error("Exception: on sending command" + str(e))
            self.logger_debug()
            self.stdout.append(self.interact.current_output_clean)
            raise
            #traceback.print_exc()

        self.log_output()

        print('\n' + '-'*79 )
        print('\n' + '-'*79 + '\n')
        print('         Hostname: ' + self.hostname.strip())
        print('         ' + datetime.datetime.now().strftime('%c') + '\n')
        print('\n' + '-'*79 + '\n')
        print('----------------------------<---Commands completed--->-------------------------\n')


    def logger_error(self, message):
        import logging

        self.formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s') 
        self.error_logger = logging.getLogger(__name__)
        self.error_logger.setLevel(logging.WARNING)
        self.error_file_handler = logging.FileHandler('error.log')
        self.error_file_handler.setFormatter(self.formatter)
        self.error_logger.addHandler(self.error_file_handler)

        self.error_logger.error(message)



    def logger_debug(self,message):

    	import logging

        self.formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s') 
    	self.debug_logger = logging.getLogger(__name__)
        self.debug_logger.setLevel(logging.DEBUG)
        self.debug_file_handler = logging.FileHandler('debug.log')
        self.debug_file_handler.setFormatter(self.formatter)
        self.debug_logger.addHandler(self.debug_file_handler)

        self.debug_logger.debug(message)


    def log_output(self):
        import datetime
        #currentDateTime = datetime.datime.now()
    	
    	try:
            if not os.path.exists('./device-logs/'):
                os.makedirs('./device-logs/')
                self.logger_error('Path created:  ./device-logs/')
                self.logger_debug('Path created:  ./device-logs/')

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
            self.logger_error(self.hostname + '.log file created.')
            self.logger_debug(self.hostname + '.log file created.')

            with open(os.path.join('./device-logs/',self.hostname + '.log'), 'w') as outputFile:
                outputFile.write('-'*79 + '\n')
                outputFile.write('Hostname: ' + self.hostname)
                outputFile.write('------------' + datetime.datetime.now().strftime('%c') + '------------------\n')
                outputFile.write('------------------------------<---Output Screen--->----------------------------\n')
                outputFile.write('-'*79 + '\n')

                for outline in self.stdout:
                    outputFile.write(outline + '\n')
            outputFile.close()

    def threadMethod(function):
        '''
        @threadMethod
        def func_to_be_threaded(self):
            #main body

            see ---> https://stackoverflow.com/questions/19846332/python-threading-inside-a-class
        '''
        def wrapper(*args, **kwargs):
            threading.Thread(target=function, args=args, kwargs=kwargs).start()
        return wrapper



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
    
    start_time = time.time()

    with open(sys.argv[1]) as device_file:
        for device in device_file:
            if not device.strip() or device.startswith('#'):
                continue
            else:
                currentDevice = device.strip()
                commodity_sw = NetDevices(hostname=currentDevice, user='georchan', password='cisco')
                commodity_sw.connect()

                with open(sys.argv[2]) as cmd_file:               
                    commodity_sw.send(*cmd_file)
                cmd_file.close()

    print("Script took--- %s seconds ---" % (time.time() - start_time))


main()