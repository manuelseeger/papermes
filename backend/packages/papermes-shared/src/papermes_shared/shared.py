import ssl

import httpx
import truststore

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
http_client = httpx.Client(verify=ssl_context)
