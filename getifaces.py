#!/usr/bin/env python3

import sys
import getopt
import netsnmp

LOCIFLINEPROT = ".1.3.6.1.4.1.9.2.2.1.1.2"
IFDESCR = ".1.3.6.1.2.1.2.2.1.2"
IFTYPE = ".1.3.6.1.2.1.2.2.1.3"
IFSPEED = ".1.3.6.1.2.1.2.2.1.5"
IFADMINSTATUS = ".1.3.6.1.2.1.2.2.1.7"
IFOPERSTATUS = ".1.3.6.1.2.1.2.2.1.8"

STATUSUNKNOWN = '4'

IFACESTATUS = {'1':'UP', '2':'DOWN', '3':'TESTING', '4':'UNKNOWN',
               '5':'DORMANT', '6':'NOTPRESENT', '7':'LOWERLAYERDOWN'
              }

ONE = 1.0
KILO = 1000.0
MEGA = 1000000.0
GIGA = 1000000000.0

LABEL = {ONE: '', KILO: 'K', MEGA: 'M', GIGA: 'G'}

def do_get(ipaddr, community, retries, port, timeout):

    iface_list = {}
    for snmp_var in (IFDESCR, IFADMINSTATUS, IFOPERSTATUS, LOCIFLINEPROT, IFSPEED):
        varbinds = netsnmp.VarList(netsnmp.Varbind(snmp_var))
        _ = netsnmp.snmpwalk(varbinds,
                             Version=2,
                             DestHost=ipaddr,
                             Community=community,
                             Retries=retries,
                             RemotePort=port,
                             Timeout=timeout * 1000000,
                             UseNumeric=1)                    

        for varbind in varbinds:
            try:
                iface_id = varbind.iid
                try:
                    varvalue = varbind.val.decode().strip()
                except:
                    varvalue = ''
                try:
                    iface_list[iface_id].append(varvalue)
                except:
                    iface_list[iface_id] = [varvalue]
            except:
                continue

        if not iface_list:
            print(f'\n** Timeout: No Response from {ipaddr}\n')
            sys.exit(0)

    print (f'\nIndex\tAdmin         \tOper          \tProto         \tDescription')
    print (f'-----\t{"-"*14}\t{"-"*14}\t{"-"*14}\t-----------{"-"*30}')

    ifaces = [int(iifid) for iifid in iface_list.keys()]
    ifaces.sort()
    for ifid in ifaces:

        ifid = str(ifid)
        try:
            ifdescr, ifadmstat, ifoperstat, ifprotstat, ifspeed = iface_list[ifid]
        except:
            ifprotstat = ''
            ifdescr, ifadmstat, ifoperstat, ifspeed = iface_list[ifid]

        try:
            adm_status = IFACESTATUS[ifadmstat] 
        except: 
            adm_status = IFACESTATUS[STATUSUNKNOWN]

        try:
            oper_status = IFACESTATUS[ifoperstat] 
        except: 
            oper_status = IFACESTATUS[STATUSUNKNOWN]

        try:
            prot_status = IFACESTATUS[ifprotstat] 
        except: 
            prot_status = IFACESTATUS[STATUSUNKNOWN]
        
        try:
            ifspeed = int(ifspeed)
            if ifspeed >= GIGA:
                div_value = GIGA

            elif ifspeed >= MEGA:
                div_value = MEGA

            elif ifspeed >= KILO:
                div_value = KILO
    
            else:
                div_value = ONE
            
            lbspeed = f'{ifspeed} ({round((ifspeed/div_value), 1)}{LABEL[div_value]})'

        except:
            try:
                lbspeed = ifspeed
            except:
                lbspeed = IFACESTATUS[STATUSUNKNOWN]

        print (f'{ifid.zfill(2)}\t{adm_status.ljust(14)}\t{oper_status.ljust(14)}\t{prot_status.ljust(14)}', end='')
        print (f'\t{ifdescr}, Speed={lbspeed}')

def print_help():
        print("Usage:")
        print("\t[-h] or [--Help]")             
        print("\t<-i ipaddr> or <--IPaddr ipaddr>")
        print("\t<-c community> or <--Community community>") 
        print("\t[-p port] or [--Port port]") 
        print("\t[-t timeout] or [--Timeout timeout]") 
        print("\t[-r retries] or [--Retries retries]")
        print() 


if __name__ == '__main__':

    argumentList = sys.argv[1:]
 
    options = "hi:c:p:t:r:"
 
    long_options = ["Help", "IPaddr=", "Community=", 
                    "Port=", "Timeout=", "Retries="
                    ]

    arguments, values = getopt.getopt(argumentList, options, long_options)

    port = 161
    ipaddr = ''
    retries = 0
    timeout = 5
    community = ''

    for currentArgument, currentValue in arguments:
        if currentArgument in ("-h", "--Help"):
            print_help()
            sys.exit(0)
             
        elif currentArgument in ("-i", "--IPaddr"):
            ipaddr = currentValue
             
        elif currentArgument in ("-c", "--Community"):
            community = currentValue
             
        elif currentArgument in ("-p", "--Port"):
            port = int(currentValue)             

        elif currentArgument in ("-t", "--Timeout"):
            timeout = int(currentValue)

        elif currentArgument in ("-r", "--Retries"):
            retries = int(currentValue)            

    try:
        if not ipaddr or not community:
            raise Exception('Invalid parameters!')
        do_get(ipaddr, community, retries, port, timeout)
    except Exception as err:
        print(f'*** {err}')
        print_help()
