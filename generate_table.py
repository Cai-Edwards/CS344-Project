from subprocess import Popen, PIPE
from itertools import product, permutations, repeat
from multiprocessing import Pool, freeze_support
from tqdm import tqdm
import csv

def count(n, p, e):
    avoiding = []
    for k in range(1, n+1):
        cmd = f"-p{p},{e}"
        c = Popen([r"E:\Warwick\CS344 work\out.exe", f"-n{k}", cmd, f"-q", f"-c"], stdout=PIPE)
        res = c.stdout.read().decode('utf-8').strip().split(" ")[-1]
        avoiding.append(int(res))
    
    return (avoiding, f'{p},{e}')

def count_star(npe):
    return count(*npe)

def mirrored(pattern):
    n = len(pattern)
    return "".join([str(n+1-int(x)) for x in pattern])

def avoid231(pattern):
    p = list(map(int, pattern))
    for i, x in enumerate(p[1:-1]):
        left = p[:i+1]
        right = p[i+2:]

        left_max = max(filter(lambda a: a < x, left), default=0)
        right_min = min(right)

        if left_max > right_min:
            return False
    
    return True

def check(N, n):
    patterns = ["".join([str(x) for x in k]) for k in [x for x in permutations(range(1,n+1), n)]]
    seen = []
    p_mirrored = [x for x in patterns if x not in seen and not seen.append(mirrored(x))]
    p_avoids231 = list(filter(avoid231, p_mirrored))

    all_edges = ["".join([str(x) for x in k]) for k in [x for x in list(product([0,1,2],repeat=n-2))]]
    mixed_edges = ["".join([str(x) for x in k]) for k in [x for x in list(product([0,1],repeat=n-2))]]
    all_edges = [x+"0" for x in all_edges]
    mixed_edges = [x+"0" for x in mixed_edges]

    only_semi = [x for x in all_edges if x not in mixed_edges]

    print("Processing mixed values")
    existing = []
    mixed_sequences = []

    with Pool(24) as process:
        for p in tqdm(list(p_avoids231)):
            vals = process.map(count_star, zip(repeat(N), repeat(p), mixed_edges))

            for x, _ in vals:
                if x[-1] not in existing:
                    mixed_sequences.append(x)
                    existing.append(x[-1])

        print(f"existing: {existing}")
        
        new_existing = []
        semi_sequences = []
        inps = {}

        print("Processing semi values:")
        for p in tqdm(list(p_avoids231)):
            vals = process.map(count_star, zip(repeat(N), repeat(p), only_semi))

            for x, i in vals:
                if x[-1] not in new_existing:
                    semi_sequences.append(x)
                    new_existing.append(x[-1])
                    inps[x[-1]] = []
                inps[x[-1]].append(i)
        
        diff = [x for x in new_existing if x not in existing]
        print(f"new_existing: {new_existing}")
        print(f"difference: {diff}")

        for x in semi_sequences:
            if x[-1] in diff:
                print(x)
                print(inps[x[-1]])
        
    with open(f'3max{N}p{n}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        
        for x in semi_sequences:
            for k in inps[x[-1]]:
                writer.writerow(k.split(',') + x)
        

if __name__ == "__main__":
    freeze_support()
    check(12, 5)