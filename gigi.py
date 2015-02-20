import dynmodel

n_helpers = 2
helper_states = 5


def phi(e, p, *helpers):
    if p > 0:
        return 0
    else:
        return sum(1 for h in helpers if h>0)


def foraging_results(e, p, helpers):
    # how many people are helping here?
    workers = 1 + sum(1 for h in helpers if h==(helper_states-1))
    dependants = 1 + sum(1 for h in helpers if h>0)
    surplus = workers*2 - dependants
    # what's the gain for each person because of it?
    food_gain = surplus * 0.1

    return e+food_gain, tuple(h+food_gain for h in helpers)

def possibilities(model, t, e, p, *helpers):
    helpers = tuple(helpers)
    possib = dynmodel.Outcomes(model)
    if e == 0:
        # dead: no choices.
        possib.otherwise(0, qual=0.0, descr="starved")
        return possib

    e, helpers = foraging_results(e, p, helpers)

    if p == 9:
        possib.add(
            decision=0,
            qualgain=0.0,
            prob=1.0,
            nextstate=(t+1, e, 0) + helpers,
            descr="give birth" )

    elif p > 0:
        possib.add(
            decision=0,
            qualgain=0.0,
            prob=1.0,
            nextstate=(t+1, e-0.1, p+1) + helpers,
            descr="stay pregnant" )

    else:
        possib.add(
            decision=0,
            qualgain=0,
            prob=1.0,
            nextstate=(t+1, e+0.1, 0) + helpers,
            descr="abstain" )

        possib.add(
            decision=1,
            qualgain=0,
            prob=0.7,
            nextstate=(t+1, e, 1) + helpers,
            descr="get pregnant" )
        possib.add(
            decision=1,
            qualgain=0,
            prob=0.3,
            nextstate=(t+1, e+0.1, 0) + helpers,
            descr="didn't get pregnant" )

    return possib

tmax = 30*12/2

def buildmodel():
    varE = dynmodel.Variable(10, "energy", continuous=True)
    varP = dynmodel.Variable(10, "pregnancy", continuous=False)
    helpers = [
        dynmodel.Variable(helper_states, "helper%i" % (i), continuous=True)
        for i in range(n_helpers)]
    
    return dynmodel.Model(
            tmax+1, [varE, varP] + helpers,
            terminal_quality=phi,
            possible_outcomes=possibilities,
            )

def main():
    model = buildmodel()

    model.fill_terminal_quality()
    model.fill_quality(max)
    
    for e in range(10):
        print model.quality(0, e, 0, 0, 0)

def profile():
    import cProfile, pstats
    cProfile.run('main()', 'restats')
    p = pstats.Stats('restats')
    p.strip_dirs().sort_stats(-1).print_stats()


if __name__ == '__main__':
    main()
    #profile()



