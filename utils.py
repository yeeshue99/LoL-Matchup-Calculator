def generateRandomlyFromList(arr, seed = None, generator = False):
    l = list(arr)
    import random
    if seed:
        random.seed(seed)
    random.shuffle(l)
    # if (generator):
    #     for element in l:
    #         yield element
    # else:
    return l
    
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]