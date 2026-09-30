from benchmark.evaluator import AEMGBenchmark

def test_benchmark():
    b = AEMGBenchmark()
    print("\n--- Running AEMG (With Memory) ---")
    res_aemg = b.run_benchmark(enable_memory=True)
    print(f"Accuracy: {res_aemg['accuracy_pct']}% | Avg Retries: {res_aemg['avg_retries_per_query']}")
    for r in res_aemg['detailed_results']:
        print(f"  [{r['query_id']}] Success: {r['success']}, Retries: {r['retries']}, Rows: {r['rows_returned']}")

if __name__ == "__main__":
    test_benchmark()
