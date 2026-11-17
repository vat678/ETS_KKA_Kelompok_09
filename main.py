import time

from bfs import run_bfs
from dfs import run_dfs
from grid_env import draw_multi_results, get_env
from ucs import run_ucs

ALGORITHM_RUNNERS = {
    "UCS (Uniform Cost Search)": run_ucs,
    "BFS (Breadth-First Search)": run_bfs,
    "DFS (Depth-First Search)": run_dfs,
}


def run_experiment(grid, start, goal, selected_algorithms, battery):
    """Menjalankan semua algoritma terpilih dengan baterai awal yang sama."""
    print(f"\nTitik Awal (Start) : {start}")
    print(f"Titik Tujuan (Goal): {goal}")
    print(f"Baterai Awal       : {battery}%")
    print("-" * 55)

    results = []

    for algo_name in selected_algorithms:
        runner = ALGORITHM_RUNNERS[algo_name]

        started_at = time.perf_counter()
        total_cost, path, visited_count = runner(grid, start, goal)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        if path:
            enough = total_cost <= battery
            remaining = battery - total_cost if enough else 0

            print(f"[{algo_name}]")
            print(f"  Konsumsi: {total_cost}% | Sisa: {remaining}%")
            if not enough:
                print("  ⚠ Baterai Tidak Cukup!")
            print(f"  Langkah: {len(path)} | Node: {visited_count} | Waktu: {elapsed_ms:.2f} ms")
        else:
            enough, remaining = False, battery
            print(f"[{algo_name}] -> Jalur tidak ditemukan.")

        results.append({
            "name": algo_name,
            "cost": total_cost,
            "path": path,
            "visited": visited_count,
            "time_ms": elapsed_ms,
            "battery": battery,
            "remaining": remaining,
            "enough": enough,
        })

    print("-" * 55)
    return results


def main():
    initial = None  

    while True:
        grid, start, goal, selected_algorithms, battery = get_env(initial)

        if not selected_algorithms:
            break

        results = run_experiment(grid, start, goal, selected_algorithms, battery)
        action = draw_multi_results(grid, start, goal, results)

        if action == "same":
            initial = (grid, start, goal, battery)
        elif action == "new":
            initial = None
        else:
            break


if __name__ == "__main__":
    main()
