import dynmodel
import random

# input number of helpers, number of energy/maturity states each helper has, and total time in months
n_helpers = 3
helper_states = 37
#tmax = 30*12/3
tmax = 3

# this is the terminal fitness function (phi) 
def phi(e, p, *helpers):
    if p > 0:
        # can't be pregnant at menopause
        return -9999
    else:
        #dependant, worker, and mother's final energy state make up terminal fitness function   
        dependants_fitness = sum(h for h in helpers if h==(1<helper_states<36))
        #mature kids give more fitness return than just dependent kids 
        worker_fitness = sum(45 for h in helpers if h==(helper_states>35))
        #good quality mothers can accumulate fitness post-menopause
        if e>5:
            maternal_fitness = 10
        else:
            maternal_fitness = 0
        return dependants_fitness + maternal_fitness + worker_fitness

def foraging_results(e, p, helpers):
    # how many people are helping here?
    workers = sum(1 for h in helpers if h==(helper_states>35))
    # how many people do you need to feed?  
    # when h==1, dependant is pre-weaning
    dependants = sum(1 for h in helpers if h==(1<helper_states<36))
    
    #when the enviornment is 100% predictable: always give 2.5unit of food/forager
    #surplus = workers*2 
    #discount due to environmental stochasticity; ran.randit is a random integer generator, gives a random integer in the range (x1,x2)
    discount = random.randint(5,10) 
    #total food gain (each worker brings 2 units of food, +1 because mother is foraging herself, but divided by 10 to correct for the fact that the discount is a whole number)
    #here, plus additional 2 because youngest 2 kids should be old enough to start contributing to the family
    surplus = (1+2+workers)*0.1*discount 
    # cost of remaining pregnant is taken at next step, surplus remain surplus     
    #if p > 0:
        #surplus = surplus - 0.5
        
    #if 9 < p < 21:
        
    # what's the gain for each person because of it?
    #+1 for self when calculating proportions     
    
    food_gain = surplus / (dependants+1)
    #for easier book-keeping, create new variable such that kids advance one time step regardless of how much food is left over
    if food_gain >= 1:
        kid_food = 1
    else: 
        kid_food = 0

    return (
        e+food_gain,
        tuple((h+kid_food if h > 1 else h+0) for h in helpers),
        surplus
    )



 
def possibilities(model, t, e, p, *helpers):
    helpers = tuple(helpers)
    possib = dynmodel.Outcomes(model)
    #mortality is set is linearly increasing from 0.01 to 0.02 by the end of time (from Hill et al 2007)      
    mortality = 0.000334*t+0.01    
    #calculates fecundability: p(getting pregnant per month that she is cycling)
    fecund = -0.00027*t+0.2 
    dependants = sum(1 for h in helpers if h==(1<helper_states<36))

    if e == 0:
        # dead: no choices.
        possib.otherwise(0, qual=0.0, descr="starved")
        return possib

    e, helpers, surplus = foraging_results(e, p, helpers)
    note = ' (%s)' % (surplus)

    if p == 9:
        # give birth: a 0 helper becomes a 1 helper
        helpers = list(helpers)
        for i, h in enumerate(helpers):
            if h == 0:
                helpers[i] = 1
                
            else:
                # already full of kids  
                possib.otherwise(0, qual=-1, descr="excess kids!")
                return possib
        helpers = tuple(helpers)

        possib.add(
            decision=0,
            qualgain=1,
            prob=1.0-mortality,
            nextstate=(t+1, e-1-dependants, p+1) + helpers,
            descr="give birth" + note )
        possib.otherwise(0, qual=0, descr='got eaten')
            
    elif 9 < p < 33:
        #PA counter, PA is 2 years (24 months)
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0-mortality,
                #PA is extra costly, additional -1
                nextstate=(t+1, e-1-1-dependants, p+1) + helpers,
                descr="PA" + note )
            possib.otherwise(0, qual=0, descr='got eaten')
                
    elif p == 33:
        
            #this weans the kid 
            helpers = list(helpers)
            for i, h in enumerate(helpers):
                if h == 1:
                    helpers[i] = 2
            helpers = tuple(helpers)
                
            #reset pregnancy counter
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0-mortality,
                nextstate=(t+1, e-1-dependants, 0) + helpers,
                descr="end PA" + note )
            possib.otherwise(0, qual=0, descr='got eaten')
        
                
    elif 0 < p < 9:
        # pregnant
        if e == 1:
            # starving... pregnancy terminates
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0-mortality,
                nextstate=(t+1, e-1-dependants, 0) + helpers,
                descr="pregnancy terminated" + note )
            possib.otherwise(0, qual=0, descr='got eaten')
        else:
            # be pregnant
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0-mortality,
                #maaintaining a pregnancy is extremely costly, hence the additional -1
                nextstate=(t+1, e-1-1-dependants, p+1) + helpers,
                descr="stay pregnant" + note )
            possib.otherwise(0, qual=0, descr='got eaten')

    else:
        possib.add(
            decision=0,
            qualgain=0,
            prob=1.0-mortality,
            nextstate=(t+1, e-1-dependants, 0) + helpers,
            descr="abstain" + note )
        possib.otherwise(0, qual=0, descr='got eaten')
    

        possib.add(
            decision=1,
            qualgain=0,
            prob=fecund-mortality,
            #this step requires more energy than usual, hence the additional -1
            nextstate=(t+1, e-1-1-dependants, 1) + helpers,
            descr="get pregnant" + note )
        possib.otherwise(0, qual=0, descr='got eaten')
        
        possib.add(
            decision=1,
            qualgain=0,
            prob=1-fecund-mortality,
            nextstate=(t+1, e-1-dependants, 0) + helpers,
            descr="didn't get pregnant" + note )
        possib.otherwise(0, qual=0, descr='got eaten')

    return possib


def buildmodel():
    varE = dynmodel.Variable(10, "energy", continuous=True)
    varP = dynmodel.Variable(34, "pregnancy", continuous=False)
    helpers = [
        dynmodel.Variable(helper_states, "helper%i" % (i), continuous=True)
        for i in range(n_helpers)]
    
    return dynmodel.Model(
            tmax+1, [varE, varP] + helpers,
            terminal_quality=phi,
            possible_outcomes=possibilities,
            )

def generate_arrays():
    print "buildmodel"
    model = buildmodel()    
    print "terminal"
    model.fill_terminal_quality()
    print "backwards"
    model.fill_quality(max)

#def print_step(model, dec, descr, t, e, p, *helpers):
  #  print dec, descr, t, e, p, helpers

#def final_results(model, dec, descr, t, e, p, *helpers):
 #   print "I'm done"
    
def print_step(model, dec, descr, t, e, p, *helpers):
    print dec, descr, t, e, p, helpers

def final_results(model, dec, descr, t, e, p, *helpers):
    print "I'm done"    
    
#def monte():
    #model = buildmodel()
    #model.read_files()

    #model.monte_carlo_run(
        #start=(0,7,3) + (0,0,0), #(t,e,p) + (h1,h2)
        #start=(0, 4, 0) + ((1,) * n_helpers),
        #report_step=print_step,
        #report_final=final_results,
    #)

def explore_arrays():
    model = buildmodel()
    model.read_files()
    
    #could inspect either the decision or quality subarray. input model.xxx_subarray()    

    
    arr = model.decision_subarray()    
    
    for j in range(0,9):

            subarr = arr[:, j, 0, 0, 0, 0] # (t, e, p, h1, h2, ...), number or : for "all"
            subarr.output('3no_helper%s.csv' %j)
    

    for k in range(0,9):

            subarr = arr[:, k, 0, 36, 0, 0] # (t, e, p, h1, h2, ...), number or : for "all"
            subarr.output('3one_helper%s.csv' %k)
    
     
    for l in range(0,9):

            subarr = arr[:, l, 0, 36, 36, 0] # (t, e, p, h1, h2, ...), number or : for "all"
            subarr.output('3two_helper%s.csv' %l)
            
    for m in range(0,9):

            subarr = arr[:, m, 0, 36, 36, 36] # (t, e, p, h1, h2, ...), number or : for "all"
            subarr.output('3three_helper%s.csv' %m)
        
    
    #arr = model.decision_subarray()    
    #subarr = arr[:, 1, 0, 0, 0, 0, 0, 0] # (t, e, p, h1, h2, ...), number or : for "all"
    #subarr.output("thirdperiod1.csv")


def check_similarity(t):
    model = buildmodel()
    model.read_files()
    total = 0
    different = 0
    for state in model.vars.allvalues():
        total += 1
        if model.decision(0, state) != model.decision(t, state):
            different += 1
    print 'time=%i, %i/%i different' % (t, different, total)
            

def profile():
    import cProfile, pstats
    cProfile.run('main()', 'restats')
    p = pstats.Stats('restats')
    p.strip_dirs().sort_stats(-1).print_stats()


if __name__ == '__main__':
    generate_arrays()
    #monte()
    #explore_arrays()
    check_similarity(1)
    check_similarity(6)
    check_similarity(12)



