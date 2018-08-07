#!/usr/bin/env python

import sys
import math
import itertools
import pandas as pd
import numpy as np
import Bio.Phylo
from Bio.Phylo.TreeConstruction import _Matrix, _DistanceMatrix
from Bio.Phylo.TreeConstruction import _Matrix, _DistanceMatrix
from Bio.Phylo.TreeConstruction import DistanceTreeConstructor

class Munkres:
    """
    Modified from Munkres version 1.0.5.4 http://bmc.github.com/munkres/
    """
    """
    Calculate the Munkres solution to the classical assignment problem.
    See the module documentation for usage.
    """
    def __init__(self):
        """Create a new instance"""
        self.C = None
        self.row_covered = []
        self.col_covered = []
        self.n = 0
        self.Z0_r = 0
        self.Z0_c = 0
        self.marked = None
        self.path = None
    def make_cost_matrix(profit_matrix, inversion_function):
        """
        **DEPRECATED**

        Please use the module function ``make_cost_matrix()``.
        """
        import munkres
        return munkres.make_cost_matrix(profit_matrix, inversion_function)
    make_cost_matrix = staticmethod(make_cost_matrix)
    def pad_matrix(self, matrix, pad_value=0):
        """
        Pad a possibly non-square matrix to make it square.
        :Parameters:
            matrix : list of lists
                matrix to pad

            pad_value : int
                value to use to pad the matrix

        :rtype: list of lists
        :return: a new, possibly padded, matrix
        """
        max_columns = 0
        total_rows = len(matrix)
        for row in matrix:
            max_columns = max(max_columns, len(row))
        total_rows = max(max_columns, total_rows)
        new_matrix = []
        for row in matrix:
            row_len = len(row)
            new_row = row[:]
            if total_rows > row_len:
                # Row too short. Pad it.
                new_row += [0] * (total_rows - row_len)
            new_matrix += [new_row]
        while len(new_matrix) < total_rows:
            new_matrix += [[0] * total_rows]
        return new_matrix
    def compute(self, cost_matrix):
        """
        Compute the indexes for the lowest-cost pairings between rows and
        columns in the database. Returns a list of (row, column) tuples
        that can be used to traverse the matrix.
        :Parameters:
            cost_matrix : list of lists
                The cost matrix. If this cost matrix is not square, it
                will be padded with zeros, via a call to ``pad_matrix()``.
                (This method does *not* modify the caller's matrix. It
                operates on a copy of the matrix.)

                **WARNING**: This code handles square and rectangular
                matrices. It does *not* handle irregular matrices.

        :rtype: list
        :return: A list of ``(row, column)`` tuples that describe the lowest
                 cost path through the matrix
        """
        self.C = self.pad_matrix(cost_matrix)
        self.n = len(self.C)
        self.original_length = len(cost_matrix)
        self.original_width = len(cost_matrix[0])
        self.row_covered = [False for i in range(self.n)]
        self.col_covered = [False for i in range(self.n)]
        self.Z0_r = 0
        self.Z0_c = 0
        self.path = self.__make_matrix(self.n * 2, 0)
        self.marked = self.__make_matrix(self.n, 0)
        done = False
        step = 1
        steps = { 1 : self.__step1,
                  2 : self.__step2,
                  3 : self.__step3,
                  4 : self.__step4,
                  5 : self.__step5,
                  6 : self.__step6 }
        while not done:
            try:
                func = steps[step]
                step = func()
            except KeyError:
                done = True
        # Look for the starred columns
        results = []
        for i in range(self.original_length):
            for j in range(self.original_width):
                if self.marked[i][j] == 1:
                    results += [(i, j)]
        return results
    def __copy_matrix(self, matrix):
        """Return an exact copy of the supplied matrix"""
        return copy.deepcopy(matrix)
    def __make_matrix(self, n, val):
        """Create an *n*x*n* matrix, populating it with the specific value."""
        matrix = []
        for i in range(n):
            matrix += [[val for j in range(n)]]
        return matrix
    def __step1(self):
        """
        For each row of the matrix, find the smallest element and
        subtract it from every element in its row. Go to Step 2.
        """
        C = self.C
        n = self.n
        for i in range(n):
            minval = min(self.C[i])
            # Find the minimum value for this row and subtract that minimum
            # from every element in the row.
            for j in range(n):
                self.C[i][j] -= minval
        return 2
    def __step2(self):
        """
        Find a zero (Z) in the resulting matrix. If there is no starred
        zero in its row or column, star Z. Repeat for each element in the
        matrix. Go to Step 3.
        """
        n = self.n
        for i in range(n):
            for j in range(n):
                if (self.C[i][j] == 0) and \
                   (not self.col_covered[j]) and \
                   (not self.row_covered[i]):
                    self.marked[i][j] = 1
                    self.col_covered[j] = True
                    self.row_covered[i] = True

        self.__clear_covers()
        return 3
    def __step3(self):
        """
        Cover each column containing a starred zero. If K columns are
        covered, the starred zeros describe a complete set of unique
        assignments. In this case, Go to DONE, otherwise, Go to Step 4.
        """
        n = self.n
        count = 0
        for i in range(n):
            for j in range(n):
                if self.marked[i][j] == 1:
                    self.col_covered[j] = True
                    count += 1
        if count >= n:
            step = 7 # done
        else:
            step = 4
        return step
    def __step4(self):
        """
        Find a noncovered zero and prime it. If there is no starred zero
        in the row containing this primed zero, Go to Step 5. Otherwise,
        cover this row and uncover the column containing the starred
        zero. Continue in this manner until there are no uncovered zeros
        left. Save the smallest uncovered value and Go to Step 6.
        """
        step = 0
        done = False
        row = -1
        col = -1
        star_col = -1
        while not done:
            (row, col) = self.__find_a_zero()
            if row < 0:
                done = True
                step = 6
            else:
                self.marked[row][col] = 2
                star_col = self.__find_star_in_row(row)
                if star_col >= 0:
                    col = star_col
                    self.row_covered[row] = True
                    self.col_covered[col] = False
                else:
                    done = True
                    self.Z0_r = row
                    self.Z0_c = col
                    step = 5
        return step
    def __step5(self):
        """
        Construct a series of alternating primed and starred zeros as
        follows. Let Z0 represent the uncovered primed zero found in Step 4.
        Let Z1 denote the starred zero in the column of Z0 (if any).
        Let Z2 denote the primed zero in the row of Z1 (there will always
        be one). Continue until the series terminates at a primed zero
        that has no starred zero in its column. Unstar each starred zero
        of the series, star each primed zero of the series, erase all
        primes and uncover every line in the matrix. Return to Step 3
        """
        count = 0
        path = self.path
        path[count][0] = self.Z0_r
        path[count][1] = self.Z0_c
        done = False
        while not done:
            row = self.__find_star_in_col(path[count][1])
            if row >= 0:
                count += 1
                path[count][0] = row
                path[count][1] = path[count-1][1]
            else:
                done = True
            if not done:
                col = self.__find_prime_in_row(path[count][0])
                count += 1
                path[count][0] = path[count-1][0]
                path[count][1] = col
        self.__convert_path(path, count)
        self.__clear_covers()
        self.__erase_primes()
        return 3
    def __step6(self):
        """
        Add the value found in Step 4 to every element of each covered
        row, and subtract it from every element of each uncovered column.
        Return to Step 4 without altering any stars, primes, or covered
        lines.
        """
        minval = self.__find_smallest()
        for i in range(self.n):
            for j in range(self.n):
                if self.row_covered[i]:
                    self.C[i][j] += minval
                if not self.col_covered[j]:
                    self.C[i][j] -= minval
        return 4
    def __find_smallest(self):
        """Find the smallest uncovered value in the matrix."""
        minval = sys.maxint
        for i in range(self.n):
            for j in range(self.n):
                if (not self.row_covered[i]) and (not self.col_covered[j]):
                    if minval > self.C[i][j]:
                        minval = self.C[i][j]
        return minval
    def __find_a_zero(self):
        """Find the first uncovered element with value 0"""
        row = -1
        col = -1
        i = 0
        n = self.n
        done = False
        while not done:
            j = 0
            while True:
                if (self.C[i][j] == 0) and \
                   (not self.row_covered[i]) and \
                   (not self.col_covered[j]):
                    row = i
                    col = j
                    done = True
                j += 1
                if j >= n:
                    break
            i += 1
            if i >= n:
                done = True
        return (row, col)
    def __find_star_in_row(self, row):
        """
        Find the first starred element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 1:
                col = j
                break

        return col
    def __find_star_in_col(self, col):
        """
        Find the first starred element in the specified row. Returns
        the row index, or -1 if no starred element was found.
        """
        row = -1
        for i in range(self.n):
            if self.marked[i][col] == 1:
                row = i
                break
        return row
    def __find_prime_in_row(self, row):
        """
        Find the first prime element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 2:
                col = j
                break
        return col
    def __convert_path(self, path, count):
        for i in range(count+1):
            if self.marked[path[i][0]][path[i][1]] == 1:
                self.marked[path[i][0]][path[i][1]] = 0
            else:
                self.marked[path[i][0]][path[i][1]] = 1
    def __clear_covers(self):
        """Clear all covered matrix cells"""
        for i in range(self.n):
            self.row_covered[i] = False
            self.col_covered[i] = False
    def __erase_primes(self):
        """Erase all prime markings"""
        for i in range(self.n):
            for j in range(self.n):
                if self.marked[i][j] == 2:
                    self.marked[i][j] = 0

def make_cost_matrix(profit_matrix, inversion_function):
    """
    Create a cost matrix from a profit matrix by calling
    'inversion_function' to invert each value. The inversion
    function must take one numeric argument (of any type) and return
    another numeric argument which is presumed to be the cost inverse
    of the original profit.
    This is a static method. Call it like this:
    .. python::
        cost_matrix = Munkres.make_cost_matrix(matrix, inversion_func)
    For example:
    .. python::
        cost_matrix = Munkres.make_cost_matrix(matrix, lambda x : sys.maxint - x)
    :Parameters:
        profit_matrix : list of lists
            The matrix to convert from a profit to a cost matrix

        inversion_function : function
            The function to use to invert each entry in the profit matrix
    :rtype: list of lists
    :return: The converted matrix
    """
    cost_matrix = []
    for row in profit_matrix:
        cost_matrix.append([inversion_function(value) for value in row])
    return cost_matrix

def print_matrix(matrix, msg=None):
    """
    Convenience function: Displays the contents of a matrix of integers.
    :Parameters:
        matrix : list of lists
            Matrix to print
        msg : str
            Optional message to print before displaying the matrix
    """
    import math
    if msg is not None:
        print(msg)
    # Calculate the appropriate format width.
    width = 0
    for row in matrix:
        for val in row:
            width = max(width, int(math.log10(val)) + 1)
    # Make the format string
    format = '%%%dd' % width
    # Print the matrix
    for row in matrix:
        sep = '['
        for val in row:
            sys.stdout.write(sep + format % val)
            sep = ', '
        sys.stdout.write(']\n')


def calculate_GK(A, B, nbhood): #nbhood = 5, can be changed
    # calculate the Goodman-Kruskal gamma index
    GK = 0.
    if len(set(A) & set(B)) > 1:
        pairsA = set( [(A[i],A[j]) for i in xrange(len(A)-nbhood) for j in xrange(i+1,i+nbhood)] )
        pairsB = set( [(B[i],B[j]) for i in xrange(len(B)-nbhood) for j in xrange(i+1,i+nbhood)] )
        allPairs = set(list(pairsA) + list(pairsB))
        Ns, Nr = 0.,0.
        for p in allPairs:
            if p in pairsA and p in pairsB: Ns += 1
            elif p in pairsA and tuple(p[::-1]) in pairsB: Nr += 1
            elif tuple(p[::-1]) in pairsA and p in pairsB: Nr += 1
            else: pass
        if (Nr + Ns) == 0:
            gamma = 0
        else:
            gamma = abs(Nr-Ns) / (Nr+Ns)
        GK = (1+gamma)/2.
    return GK

def cluster_distance(A, B, nbhood, pathways, dist, annotation):
    clusterA = pathways[A]
    clusterB = pathways[B]
    try:
        Jaccard = len(set(clusterA.keys()) & set(clusterB.keys())) / float( len(set(clusterA.keys())) + len(set(clusterB.keys())) - len(set(clusterA.keys()) & set(clusterB.keys())))
    except ZeroDivisionError:
        print("Zerodivisionerror during the Jaccard distance calculation. Can only happen when one or more clusters contains no domains.")
        print("keys of clusterA", A, clusterA.keys())
        print("keys of clusterB", B, clusterB.keys())
    intersect = set(clusterA.keys() ).intersection(clusterB.keys()) #shared domains
    not_intersect = []
    DDS,S = 0,0
    SumDistance = 0
    pair = ""
    for domain in set(clusterA.keys() + clusterB.keys()):
        if domain not in intersect:
            not_intersect.append(domain)
    for unshared_domain in not_intersect: 
        dom_set = []
        try:
            dom_set = clusterA[unshared_domain]
        except KeyError:
            dom_set = clusterB[unshared_domain]
        DDS += len(dom_set)
        S += len(dom_set)
    for shared_domain in intersect:
        seta = clusterA[shared_domain]
        setb = clusterB[shared_domain]
        if len(seta+setb) == 2: #The domain occurs only once in both clusters
            pair = tuple(sorted([seta[0],setb[0]]))
            for p in pair:
                try:
                    S += max(len(seta),len(setb))
                    DDS += dist[p[0]][p[1]]
                except KeyError:
                    print("KeyError on "+" ".join([str(pair), str(p[0]), str(p[1])]))
        else: #The domain occurs more than once in both clusters
            DistanceMatrix = [[1 for col in range(len(setb))] for row in range(len(seta))]
            for domsa in range(len(seta)):
                for domsb in range(domsa, len(setb)):
                    pair = tuple(sorted([seta[domsa], setb[domsb]]))
                    for p in pair:
                        try:
                            DistanceMatrix[domsa][domsb] = dist[p[0]][p[1]]
                        except KeyError:
                            print("KeyError on "+str(pair))
            #Only use the best scoring pairs
            Hungarian = Munkres()
            #print "DistanceMatrix", DistanceMatrix
            BestIndexes = Hungarian.compute(DistanceMatrix)
            # print "BestIndexes", BestIndexes
            accumulated_distance = sum([DistanceMatrix[bi[0]][bi[1]] for bi in BestIndexes])
            # print "accumulated_distance", accumulated_distance
            SumDistance = (abs(len(seta)-len(setb)) + accumulated_distance)  #diff in abundance + sequence distance
            # print 'SumDistance2', SumDistance
            S += max(len(seta),len(setb))
            DDS += SumDistance

## HERE
    #  calculate the Goodman-Kruskal gamma index
    A_pseudo_seq = annotation[A]
    B_pseudo_seq = annotation[B]
    Ar = [item for item in A_pseudo_seq]
    Ar.reverse()
    GK = max([calculate_GK(A_pseudo_seq, B_pseudo_seq, nbhood = nbhood), calculate_GK(Ar, B_pseudo_seq, nbhood = nbhood)])
    DDS /= float(S)
    DDS /= float(S)
    DDS = math.exp(-DDS) #transform from distance to similarity score
    Distance = 1 - (Jaccardw * Jaccard) - (DDSw * DDS) - (GKw * GK)
    Similarity_score = (Jaccardw * Jaccard) + (DDSw * DDS) + (GKw * GK)
    if Distance < 0:
        print("\t".join(["negative distance", str(Distance), "DDS", str(DDS), str(pair)]))
        print("Probably a rounding issue")
        print("Distance is set to 0 for these clusters")
        Distance = 0
    return Similarity_score

def generate_distance_matrix(pathways, domain_names, annotation,
                             dist, Jaccardw, GKw, DDSw,
                             scale, nbhood, outfile):
    pnames = pathways.keys()
    r = len(pnames)
    c = len(pnames)
    Dist = [[0 for x in range(r)] for y in range(c)]
    df = pd.DataFrame(Dist, index=pnames, columns=pnames)
    pairs = list(itertools.combinations(pnames, 2))
    for p in pairs:
        sim_score = cluster_distance(p[1], p[0], nbhood, pathways, dist, annotation)
        rowname = p[1]
        colname = p[0]
        df.ix[rowname, colname] = 1- sim_score/scale
    df.to_csv(outfile)
    return df


"""
 This assumes that the annotation matrix col names are:
  0: pathway name
  1: number of domains in pathway
  2: first domain
  n: last domain

 Headers for the blast/diamond queries/hits are assumed to be
  pathway|domain
 where both pathway and domain match the annotation file (row and col names, respectively)

"""

## Set the weights
Jaccardw = 0.5
GKw = 0.25
DDSw = 0.25

## Define inputs
annotation_matrix = "./annotateKS_per_pred_transATPKS_mc_manualderep.txt"
blasttable = "./full.dbp" ## Tab blast

## Define outputs
outfile = "distance.txt"
tree_outfile = "upgmma.nwk"

## Parse inputs
pathways = {}
domain_names = []
annotation = {}
with open(annotation_matrix) as a:
    l = 0  
    for ln in a.read().splitlines():
        s = ln.split("\t")
        if(l==0):
            domain_names = s[2:]
        else:
            if s[0] not in pathways:
                pathways[s[0]] = {}
            d = s[2:]
            for i, spec in enumerate(d):
                if spec == 'NA':
                    continue
                domain = '|'.join([s[0], domain_names[i]])
                if s[0] not in annotation:
                    annotation[s[0]] = []
                annotation[s[0]].append(spec)
                if spec not in pathways[s[0]]:
                    pathways[s[0]][spec] = []
                    pathways[s[0]][spec].append(domain)
        l += 1
dist = {}      
with open(blasttable) as b:
      for ln in b.read().splitlines():
        s = ln.split("\t")
        if s[0] not in dist:
            dist[s[0]] = {}
        dist[s[0]][s[1]] = 1-float(s[2])

## Distance matrix
dist_score_assembly_line = generate_distance_matrix(pathways, domain_names, annotation,
                                                    dist, Jaccardw, GKw, DDSw,
                                                    scale=1, nbhood=3, outfile=outfile)

#-- Plot the tree
names = pathways.keys()
score = [s for s in open(outfile, 'r').read().split('\n')[1:] if s != '']
matrix = []
for i in range(len(score)):
    input_i = score[i].split(',')[1:(i+2)]
    input_i_int = [float(n) for n in input_i]
    matrix.append(input_i_int)
m = _DistanceMatrix(names, matrix)
constructor = DistanceTreeConstructor()
tree1 = constructor.upgma(m)
#Bio.Phylo.draw_ascii(tree1)
Bio.Phylo.write(tree1, tree_outfile, 'newick')


