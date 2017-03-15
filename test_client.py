import xmlrpclib


dns_zone_data = """$ORIGIN test.com.
$TTL 0
@ IN SOA IMSX.ROBOT.AUTOMATION.TEST. ROOT.IMSX.COM. ( 20160718 5 5 5 86400 )
@ A 1.2.3.4.
"""

while True:
    print "1: start custom mail server"
    print "2: stop custom mail server"
    print "3: start sshTunnel"
    print "4: stop sshTunnel"
    print "5: stop dns server"
    print "6: start dns server"
    print "7: stop HTTP server"
    print "8: start HTTP server"
    print "9: flush dns server"
    cmd = raw_input()
    s = xmlrpclib.ServerProxy('http://127.0.0.1:8270', allow_none=True)

    if cmd == '1':
        d = {'test': '1', 'test01': '1'}
        s.start_mail_server(('0.0.0.0', 25000), None, True, 'san_cert.pem', 'san_key.pem', 'ca_root.pem', False, d)
        # s.start_mail_server(('0.0.0.0',25001), None)
    elif cmd == '2':
        s.stop_mail_server()
    elif cmd == '3':
        s.start_ssh_tunnel_server(('10.204.169.48', 22), 'root', '111111', ('', 5432), ('127.0.0.1', 5432))
    elif cmd == '4':
        s.stop_ssh_tunnel_server(8272)
    elif cmd == '5':
        s.stop_dns_server()
    elif cmd == '6':
        s.start_dns_server(dns_zone_data)
    elif cmd == '7':
        s.stop_http_server(80)
    elif cmd == '8':
        s.start_http_server(80, 'C:\\')
    elif cmd == '9':
        s.flush_dns_server(dns_zone_data)
