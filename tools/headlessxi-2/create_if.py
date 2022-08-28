
import os
for i in range(5,250):
    os.system(f'sudo ifconfig eth0:{i} 172.31.176.{i} netmask 255.255.240.0 up')
