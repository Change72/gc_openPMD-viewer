import geosindex

query_test = geosindex.QueryGEOSINDEX("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/rocksdb")
result = query_test.queryByXYZ("/data/400/particles/electrons/position/", -0.06996e-25, -0.06996e-24, -0.06996e-5, 0.06996e-5, 4.996e-05, 7.996e-02)
print(result[0].start, result[0].end)

