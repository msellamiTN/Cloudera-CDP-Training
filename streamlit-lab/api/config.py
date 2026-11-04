import os

HBASE_HOST = os.getenv("HBASE_THRIFT_HOST", "localhost")
HBASE_PORT = int(os.getenv("HBASE_THRIFT_PORT", "9090"))
HBASE_TABLE = os.getenv("HBASE_TABLE", "product_analytics")
HBASE_TIMEOUT_MS = int(os.getenv("HBASE_TIMEOUT_MS", "5000"))
