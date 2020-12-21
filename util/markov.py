from collections import Counter
import random

class MarkovChain:
    def __init__(self):
        self.probabilities = {}
        self.start_probabilities = {}
        self.symbols = set()
        self.n = None

    def fit(self, sequences, n):
        self.n = n

        # Collect n-grams and their next value
        patterns = []
        start_patterns = []
        for sequence in sequences:
            patterns += [(tuple(sequence[x: x+n]), sequence[x+n]) for x in range(len(sequence) - n)]
            start_patterns.append(tuple(sequence[0: n]))
            self.symbols = self.symbols.union(set(sequence))

        # For each n-gram, calculate the probability distribution over the next output
        tmp_probability_counter = {}
        for (ngram, next_value) in patterns:

            if ngram not in tmp_probability_counter:
                tmp_probability_counter[ngram] = {}

            if next_value not in tmp_probability_counter[ngram]:
                tmp_probability_counter[ngram][next_value] = 1
            else:
                tmp_probability_counter[ngram][next_value] += 1

        # Fill in the transition probabilities
        for (ngram, next_counts) in tmp_probability_counter.items():
            total_count = sum(next_counts.values())
            self.probabilities[ngram] = {k:(v / total_count) for k, v in next_counts.items()}

        # Also calculate the start probabilities
        start_counter = Counter(start_patterns)
        total_count_start = sum(start_counter.values())
        self.start_probabilities = {k:(v / total_count_start) for k, v in start_counter.items()}

    def next(self, ngram):
        if ngram not in self.probabilities.keys():
            return random.choice(list(self.symbols))

        (next_symbols, probabilities) = zip(*self.probabilities[ngram].items())
        next_symbol = random.choices(next_symbols, probabilities)[0]
        return next_symbol


    def generate(self, length):
        # Determine starting sequence
        start_sequences = list(self.start_probabilities.keys())
        start_probabilities = list(self.start_probabilities.values())
        start_ngram = random.choices(
            population=start_sequences,
            weights=start_probabilities,
            k=1
        )[0]

        sequence = start_ngram
        while len(sequence) < length:
            cur_ngram = sequence[-self.n:]
            sequence += (self.next(cur_ngram),)

        return sequence

if __name__ == "__main__":
    import pickle
    sequences = pickle.load(open('/home/tom/projects/lstar/experiments/mutatingproblem12/counterexamples_Problem12_large.p', 'rb'))

    m = MarkovChain()
    m.fit(sequences, 3)

    for i in range(100):
        print(m.generate(50))



