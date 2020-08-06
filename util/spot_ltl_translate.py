import spot


def rewrite_weakuntil(input_line):
    formula = spot.formula(input_line.strip())
    newformula = "{0:[W]}".format(formula).replace('1', 'true').replace('0', 'false')
    print('{:10}'.format("Original:"), input_line.strip()[2: -2])
    print('{:10}'.format("Spot:"), newformula)
    return newformula


if __name__ == "__main__":

    problem = 'Problem3'
    constrpath = f'/home/tom/projects/lstar/rers/TrainingSeqLtlRers2020/{problem}/constraints-{problem}.txt'
    mappingpath = f'/home/tom/projects/lstar/rers/TrainingSeqLtlRers2020/{problem}/{problem}_alphabet_mapping_C_version.txt'

    with open(constrpath, 'r') as file:
        for line in file.readlines():
            if not line.startswith('#') and len(line.strip()) > 0:
                formula = rewrite_weakuntil(line)
                print('{:10}'.format("Original:"), line.strip()[2: -2])
                print('{:10}'.format("Spot:"), formula)
                print()
