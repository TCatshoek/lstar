

# Allows direct calculation of list(product(X, repeat))[index]
# Without having to create a list from the product generator
def index_product(index, items, repeat=1):
    n_items = len(items)
    assert index <= n_items ** repeat, f"Index {index} out of range"

    prod = [0] * repeat

    for i in range(repeat):
        idx = (index % (n_items ** (i + 1)))
        idx = idx // (n_items ** i)

        prod[repeat - i - 1] = items[idx]

    return tuple(prod)


# Allows looking up the index of a certain product result,
# Basically the reverse of "index_product" above
def product_index(prod, items):
    prod = reversed(prod)
    acc = 0
    n = len(items)

    for i, p in enumerate(prod):
        idx = items.index(p)
        acc += n ** i * idx

    return acc

# Calculates the cumulative size of the products of the given
# sequence for all repeats uptil and including repeats_until
# Basically does: sum([len(list(product(X, repeat=x))) for x in range(repeats_until)])
def cumlen(n_items, repeats_until):
    acc = 0
    for i in range(1, repeats_until + 1):
        acc += n_items ** i
    return acc