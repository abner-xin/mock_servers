all my servers are hold by a RPC server on port 8270. so you can start/stop mock servers by RPC requests.
details info refer to test_client.py

# supported mock servers:
 - SMTP server
  1. support multi-instances
  2. support TLS
  3. support SMTP AUTH
 - HTTP Server: support multi-instances
 - DNS Server
 - SSHTunnel Server: support multi-instances