import dynmodel
import random

# input number of helpers, number of energy/maturity states each helper has, and total time in months
n_helpers = 2
helper_states = 5
tmax = 30*12/2

#mortality is set to constant rate for now      
mortality = 0.01

# this is the terminal fitness function (phi) 
def phi(e, p, *helpers):
    if p > 0:
        # can't be pregnant at menopause
        return -9999
    else:
        # more helpers increases fitness, also goes up if energy state above certain threshold 
        dependants_fitness = sum(0 for h in helpers if h==(helper_states<4))
        #mature kids give more fitness return than just dependent kids 
        worker_fitness = sum(5 for h in helpers if h==(helper_states>3))
        #good quality mothers can accumulate fitness post-menopause
        if e>5:
            maternal_fitness = 2
        else:
            maternal_fitness = 0
        return dependants_fitness + maternal_fitness + worker_fitness

def foraging_results(e, p, helpers):
    # how many people are helping here? +1 because mother is also foraging
    workers = 1 + sum(1 for h in helpers if h==(helper_states>3))
    # how many people do you need to feed? +1 because need to feed yourself
    # when h==1, dependant is pre-weaning
    dependants = 1 + sum(1 for h in helpers if h==(1<helper_states<4))
    
    #when the enviornment is 100% predictable: always give 2.5unit of food/forager
    #surplus = workers*2 
    #discount due to environmental stochasticity; ran.randit is a random integer generator, gives a random integer in the range (x1,x2)
    discount = random.randint(5,10) 
    #total food gain (each worker brings 2 units of food, but divided by 10 to correct for the fact that the discount is a whole number)
    surplus = workers*0.5*discount 
    # cost of remaining pregnant is taken at next step, surplus remain surplus     
    #if p > 0:
        #surplus = surplus - 0.5
        
    #if 9 < p < 21:
        
    # what's the gain for each person because of it? 
    
    food_gain = surplus / dependants
    

    return (
        e+food_gain,
        tuple((h+food_gain if h > 1 else h+0) for h in helpers),
        surplus
    )
 
def possibilities(model, t, e, p, *helpers):
    helpers = tuple(helpers)
    possib = dynmodel.Outcomes(model)
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
                break
            else:
                # already full of kids  
                possib.otherwise(0, qual=-1, descr="excess kids!")
                return possib
        helpers = tuple(helpers)

        possib.add(
            decision=0,
            qualgain=1,
            prob=1.0-mortality,
            nextstate=(t+1, e-1, p+1) + helpers,
            descr="give birth" + note )
        possib.otherwise(0, qual=0, descr='got eaten')
            
    elif 9 < p < 21:
        #PA counter, PA is at least 1 year (12 months)
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0-mortality,
                nextstate=(t+1, e-1, p+1) + helpers,
                descr="PA" + note )
            possib.otherwise(0, qual=0, descr='got eaten')
                
    elif p == 21:
        
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
                nextstate=(t+1, e-1, 0) + helpers,
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
                nextstate=(t+1, e-1, 0) + helpers,
                descr="pregnancy terminated" + note )
            possib.otherwise(0, qual=0, descr='got eaten')
        else:
            # be pregnant
            possib.add(
                decision=0,
                qualgain=0.0,
                prob=1.0-mortality,
                nextstate=(t+1, e-1, p+1) + helpers,
                descr="stay pregnant" + note )
            possib.otherwise(0, qual=0, descr='got eaten')

    else:
        possib.add(
            decision=0,
            qualgain=0,
            prob=1.0-mortality,
            nextstate=(t+1, e, 0) + helpers,
            descr="abstain" + note )
        possib.otherwise(0, qual=0, descr='got eaten')
        
        #calculates fecundability: p(getting pregnant per month that she is cycling)
        fecund = -0.00027*t+0.2 

        possib.add(
            decision=1,
            qualgain=0,
            prob=fecund-mortality,
            nextstate=(t+1, e, 1) + helpers,
            descr="get pregnant" + note )
        possib.otherwise(0, qual=0, descr='got eaten')
        
        possib.add(
            decision=1,
            qualgain=0,
            prob=1-fecund-mortality,
            nextstate=(t+1, e, 0) + helpers,
            descr="didn't get pregnant" + note )
        possib.otherwise(0, qual=0, descr='got eaten')

    return possib


def buildmodel():
    varE = dynmodel.Variable(10, "energy", continuous=True)
    varP = dynmodel.Variable(22, "pregnancy", continuous=False)
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

#def print_step(model, dec, descr, t, e, p, *helpers):
  #  print dec, descr, t, e, p, helpers

#def final_results(model, dec, descr, t, e, p, *helpers):
 #   print "I'm done"
    
def print_step(model, dec, descr, t, e, p, *helpers):
    print dec, descr, t, e, p, helpers

def final_results(model, dec, descr, t, e, p, *helpers):
    print "I'm done"    
    
def monte():
    model = buildmodel()
    model.read_files()

    model.monte_carlo_run(
        start=(0,7,0) + (0,0), #(t,e,p) + (h1,h2)
        #start=(0, 4, 0) + ((1,) * n_helpers),
        report_step=print_step,
        report_final=final_results,
    )

#def explore_arrays():
 #   model = buildmodel()
  #  model.read_files()
    
   # arr = model.quality_subarray()
    #subarr = arr[tmax-10, :, 0, :, :] # (t, e, p, h1, h2, ...), number or : for "all"
    #subarr.output("output.csv")

def profile():
    import cProfile, pstats
    cProfile.run('main()', 'restats')
    p = pstats.Stats('restats')
    p.strip_dirs().sort_stats(-1).print_stats()


if __name__ == '__main__':
    generate_arrays()
    monte()
#    explore_arrays()



