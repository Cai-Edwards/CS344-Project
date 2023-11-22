import argparse
import logging

from sys import stdout
from os import path
from subprocess import Popen, PIPE
from itertools import product, permutations, repeat
from multiprocessing import Pool, freeze_support
from tqdm import tqdm

class AvoidingTree:

    def __init__(self, args) -> None:
        """init. Pass in args as dict."""

        self.file, self.n, self.p, self.quiet, self.preorders, self.all_edges, self.only_mixed, self.only_semi = [None]*8

        self.setattrs(args)


    def count(self, n : int, p : str, e: str) -> tuple[list, str]:
        """Count the number of binary trees of size k=1 to n which avoid the
        preorder p with edge types e

        Parameters
        ----------
        n : int
            Maximum size of tree to consider
        p : str
            Preorder of pattern to avoid. 
            It must be a 231 avoiding permutation to be valid.
        e : str
            edgetype list for the preorder.

        Returns
        -------
        tuple[list, str]
            list - result of count
            str - 'p,e'
        """

        avoiding = []
        for k in range(1, n+1):
            cmd = f"-p{p},{e}"
            c = Popen([self.file, f"-n{k}", cmd, "-q", "-c"], stdout=PIPE)
            res = c.stdout.read().decode('utf-8').strip().split(" ")[-1]
            avoiding.append(int(res))
        
        return (avoiding, f'{p},{e}')

    def count_star(self, npe : list) -> tuple[list, str]:
        """Calls :func:`count` with npe spread"""
        return self.count(*npe)

    def setattrs(self, dict):
        """Adds dictionary's items as class attributes"""
        for k,v in dict.items():
            setattr(self, k, v)

    def get_patterns(self, n=None):
        """Calculates all valid preorders of size n, as well as valid edgetype lists for that preorder.

        Parameters
        ----------
        n : int, optional
            size of preorder to calculate, by default self.p

        Returns
        -------
        tuple[list, list, list, list]
            (Preorders, all edgesets, edgesets without semi-contiguous edges, edgesets with semi-contiguous edges)
        """
        if n is None:
            n = self.p
        
        n = int(n)

        patterns = ["".join([str(x) for x in k]) for k in [x for x in permutations(range(1,n+1), n)]]
        seen = []
        p_mirrored = [x for x in patterns if x not in seen and not seen.append(mirrored(x))]
        self.preorders = list(filter(avoid231, p_mirrored))

        all_edges = ["".join([str(x) for x in k]) for k in [x for x in list(product([0,1,2],repeat=n-2))]]
        only_mixed = ["".join([str(x) for x in k]) for k in [x for x in list(product([0,1],repeat=n-2))]]
        
        #Fix this later - needs to remove leaf nodes after splitting mixed and semi
        self.all_edges = [x+"1" for x in all_edges]
        self.only_mixed = [x+"1" for x in only_mixed]
        self.only_semi = [x for x in self.all_edges if x not in self.only_mixed]

        return (self.preorders, self.all_edges, self.only_mixed, self.only_semi)

    def process_pattern(self, process, preorders, edgesets, n=None):
        """Calls btree.exe -N n -p p,e for all n, p, e provided

        Parameters
        ----------
        process : Pool
            process pool
        preorders : list[str]
            list of all preorders to be considered
        edgesets : list[str]
            list of all edgesets to be considered

        Returns
        -------
        tuple[list[list[int]], list[int] dict[int, str]]
            returns list of all unique sequences found, and all p,e which match a given sequence
        """

        if n is None:
            n = self.n

        already_found = []
        unique_sequences = []
        seq_to_pattern = {}
        
        for p in tqdm(list(preorders), disable=self.quiet):
            vals = process.map(self.count_star, zip(repeat(n), repeat(p), edgesets))

            for x, i in vals:
                if x[-1] not in already_found:
                    unique_sequences.append(x)
                    already_found.append(x[-1])
                    seq_to_pattern[x[-1]] = []
                seq_to_pattern[x[-1]].append(i)
        
        return (unique_sequences, already_found, seq_to_pattern)

    def main(self, process_number, n=None, p=None):
        """Calculate the differences between the mixed edgeset and semi edgeset

        Parameters
        ----------
        process_number : int
            number of processors to use
        n : int, optional
            max size of tree to use, by default self.n
        p : int, optional
            max size of preorder to use, by default self.p
        """

        logging.debug('Counting n: %s, p: %s', n or self.n, p or self.p)

        preorders, all_e, m_e, s_e = self.get_patterns(p)
        with Pool(process_number) as process:

            logging.debug("Counting mixed edgesets")
            m_sequences, m_end, m_p = self.process_pattern(process, preorders, m_e, n)
            
            logging.debug("Counting semi edgesets")
            s_sequences, s_end, s_p = self.process_pattern(process, preorders, s_e, n)

            diff = [x for x in s_end if x not in m_end]

            logging.debug("semi_end - %s", s_end)
            logging.debug("difference - %s", diff)

            for x in s_sequences:
                if x[-1] in diff:
                    logging.debug(x)
                    logging.debug(s_p[x[-1]])
            
            total_seq = m_p
            for seq, pat in s_p.items():
                if m_p[seq]:
                    total_seq[seq] += pat
                else:
                    total_seq[seq] = pat

            cols = "|l|l|" + "*{" + str(self.n) + "}{r}|"
            table = r"\begin{longtable}[H]{" + cols + "}\n" \
                     + r"\hline" + "\n" \
                     + r"P & e & \multicolumn{" + str(self.n) + r"}{l|}{Counts} \\ \hline" + "\n"


            pre = {}
            seq_lookup = {s[-1]:s for s in (m_sequences + s_sequences)}

            for seq, pat in total_seq.items():

                for k in pat:
                    order, edge = k.split(",")
                    
                    if order not in pre:
                        pre[order] = []

                    #TEMP METHODS FOR EQUIV TODO
                    pre[order].append((edge[:-1] + "-", " & ".join(str(s) for s in seq_lookup[seq])))

            for order, edges in pre.items():
                first = True

                for r in edges:
                    if first:
                        table += order + " & " + r[0] + " & " + r[1]
                        first = False
                    else:
                        table += r"\\*" + "\n" + " & " + r[0] + " & " + r[1]
            
                table += r" \\" + "\n"+ r"\hline" + "\n"
            
            table += r"\end{longtable}"
            print(table)
                


def mirrored(preorder):
    """Returns the mirrored preorder based on the reordering n+1-i"""

    n = len(preorder)
    return "".join([str(n+1-int(x)) for x in preorder])

def avoid231(preorder):
    """Returns whether the given preorder is 231 avoiding."""

    p = list(map(int, preorder))
    for i, x in enumerate(p[1:-1]):
        left = p[:i+1]
        right = p[i+2:]

        left_max = max(filter(lambda a: a < x, left), default=0)
        right_min = min(right)

        if left_max > right_min:
            return False
    
    return True

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='maximum value of N to calculate', required=True, type=int)
    parser.add_argument('-p', help='Size of pattern to avoid', required=True, type=int)
    parser.add_argument('-f', '--file', help='btree.exe file - default=./btree.exe', default='./btree.exe')
    parser.add_argument('-q', '--quiet', help="Mute commandline output of program", action='store_true')
    parser.add_argument('-k', '--processors', help="Number of processors to use", type=int, default=1)

    args = parser.parse_args()

    generator = AvoidingTree(vars(args))


    logFormatter = logging.Formatter("%(asctime)s:  %(message)s")
    rootLogger = logging.getLogger()

    fileHandler = logging.FileHandler("table.log")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    rootLogger.setLevel(logging.DEBUG)

    if not generator.quiet:
        consoleHandler = logging.StreamHandler(stdout)
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)
        

    target_exe = generator.file

    if not path.isfile(target_exe):
        raise FileNotFoundError('btree.exe could not be found')

    freeze_support()

    logging.debug('Running with %s processors', generator.processors)
    generator.main(generator.processors)