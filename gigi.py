import dynmodel

# input number of helpers, number of energy/maturity states each helper has, and total time in months
n_helpers = 5
helper_states = 5
tmax = 30*12/2

# this is the terminal fitness function (phi) 
def phi(e, p, *helpers):
    if p > 0:
        # can't be pregnant at menopause
        return -1
    else:
        # more helpers increases fitness, also goes up if energy state above certain threshold 
        helper_fitness = sum(1 for h in helpers if h>0)
        if e>5:
            maternal_fitness = 1
        else:
            maternal_fitness = 0
        return helper_fitness + maternal_fitness


def foraging_results(e, p, helpers):
    # how many people are helping here?
    workers = 1 + sum(1 for h in helpers if h==(helper_states>4))
    # how many people do you need to feed?
    dependants = 1 + sum(1 for h in helpers if h==(helper_states<4))
    surplus = workers*2.5 - dependants
    # cost of remaining pregnant     
    if p > 0:
        surplus = surplus - 0.5
    # what's the gain for each person because of it?
    food_gain = surplus / (h+1)

    return (
        e+food_gain,
        tuple((h+food_gain if h else 0) for h in helpers),
????        surplus
    )

def possibilities(model, t, e, p, *helpers):
    helpers = tuple(helpers)
    possib = dynmodel.Outcomes(model)
    if e == 0:
        # dead: no choices.
        possib.otherwise(0, qual=0.0, descr="starved")
        return possib

    e, helpers, surplus = foraging_results(e, p, helpers)
????    note = ' (%s)' % (surplus)

    if p == 9:
        # give birth: a 0 helper becomes a 1 helper
        helpers = list(helpers)
        for i, h in enumerate(helpers):
            if h == 0:
                helpers[i] = 1
                break
        else:
            # already full of kids
            possib.otherwise(0, qual=-1, descr="excess kids!")
            return possib
        helpers = tuple(helpers)

        possib.add(
            decision=0,
            qualgain=0.0,
            prob=1.0,
            nextstate=(t+1, e-1, 0) + helpers,
            descr="give birth" + note )

    elif p > 0:
        # pregnant
        if e == 1:
            # starving... pregnancy terminates
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0,
                nextstate=(t+1, e-1, 0) + helpers,
                descr="pregnancy terminated" + note )
        else:
            # be pregnant
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0,
                nextstate=(t+1, e-0.1, p+1) + helpers,
                descr="stay pregnant" + note )

    else:
        possib.add(
            decision=0,
            qualgain=0,
            prob=1.0,
            nextstate=(t+1, e, 0) + helpers,
            descr="abstain" + note )

        possib.add(
            decision=1,
            qualgain=0,
            prob=0.2,
            nextstate=(t+1, e-1, 1) + helpers,
            descr="get pregnant" + note )
        possib.add(
            decision=1,
            qualgain=0,
            prob=0.8,
            nextstate=(t+1, e, 0) + helpers,
            descr="didn't get pregnant" + note )

    return possib


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

def generate_arrays():
    model = buildmodel()
    model.fill_terminal_quality()
    model.fill_quality(max)

def print_step(model, dec, descr, t, e, p, *helpers):
    print dec, descr, t, e, p, helpers

def final_results(model, dec, descr, t, e, p, *helpers):
    print "I'm done"
    
def monte():
    model = buildmodel()
    model.read_files()

    model.monte_carlo_run(
        start=(0, 4, 0) + ((0,) * n_helpers),
        report_step=print_step,
        report_final=final_results,
    )

def profile():
    import cProfile, pstats
    cProfile.run('main()', 'restats')
    p = pstats.Stats('restats')
    p.strip_dirs().sort_stats(-1).print_stats()


if __name__ == '__main__':
    generate_arrays()
    monte()
    #profile()



