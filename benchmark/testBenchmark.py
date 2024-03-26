from benchmark import BenchmarkGenerator

bg = BenchmarkGenerator(bp_file_path='/data/gc/rocksdb-index/WarpX/build/bin/diags/diag2/', 
                        geos_index_path="/data/gc/rocksdb-index/GEOSIndex/cmake-build-debug/diag2")

result = bg.generateRandomQuery(species="electrons", iteration=300, percentage_range=[0.001, 1.0, 10],
                        select_set={'x'}, expand_set={'x'}, threshold=0.1, repeat_num=10, learning_rate=0.99)

print(result)