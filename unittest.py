import os
import sys
sys.path.insert(0, os.getcwd())
import geosindex

# query_test = geosindex.QueryGEOSINDEX("/data/gc/rocksdb-index/WarpX/build/bin/diags/diag1/rocksdb")
# result = query_test.queryByXYZ("/data/400/particles/electrons/position/", -0.06996e-25, -0.06996e-24, -0.06996e-5, 0.06996e-5, 4.996e-05, 7.996e-02)
# print(result[0].start, result[0].end)

key = "/data/300/particles/electrons/position/"
rTreeQuery = geosindex.RTreeQuery("/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2", "file", "none")
# minMaxIndex = geosindex.MinMaxQuery("minmaxindex", "file")
result = rTreeQuery.queryRTreeMetaData(key)
for i in result:
    print(i.start, i.end)

test_lambda = lambda iteration, species, type, dimension=None: f"/data/{iteration}/particles/{species}/{type}/" + (f"{dimension}" if dimension else "")
print(test_lambda(300, "electrons", "position", "x"))
print(test_lambda(300, "electrons", "position"))
print()
