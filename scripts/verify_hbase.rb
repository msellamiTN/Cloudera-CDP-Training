puts "=== DataCo HBase validation ==="
status 'simple'
if exists?('product_analytics')
  describe 'product_analytics'
  puts "\n=== Sample rows ==="
  scan 'product_analytics', { LIMIT => 10 }
  puts "\n=== Row count ==="
  count 'product_analytics', INTERVAL => 10
else
  puts "[ERROR] Table product_analytics does not exist"
end
