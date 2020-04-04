
# Longest common subsequence, recursive version
def lcs_rec(seq1, seq2, acc=0):
    i = len(seq1)
    j = len(seq2)

    if i == 0 or j == 0:
        return acc

    if seq1[-1] == seq2[-1]:
        acc += 1
        return lcs(seq1[0:-1], seq2[0:-1], acc)
    else:
        return max(lcs(seq1, seq2[0:-1], acc), lcs(seq1[0:-1], seq2, acc))

# Longest common subsequence, faster version
def lcs(seq1, seq2):
    i = len(seq1)
    j = len(seq2)

    if i == 0 or j == 0:
        return 0

    C = [[0 for x in range(i + 1)] for y in range(j + 1)]

    for y in range(1, j + 1):
        for x in range(1, i + 1):
            if seq1[x-1] == seq2[y-1]:
                C[y][x] = C[y-1][x-1] + 1
            else:
                C[y][x] = max(C[y-1][x], C[y][x-1])

    return C[j][i]


def lcsdistance(seq1, seq2, penalty=0):
    n_diff = set(seq1).symmetric_difference(set(seq2))

    _lcs = lcs(seq1, seq2)
    return (len(seq1) - _lcs) + (len(seq2) - _lcs) + (penalty * len(n_diff))

if __name__ == "__main__":
    print(lcsdistance('123', '1234', penalty=1))