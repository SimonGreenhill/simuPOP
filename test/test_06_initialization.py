#!/usr/bin/env python
#
# test initiailization operators
#
# # Bo Peng (bpeng@rice.edu)
#
# $LastChangedRevision$
# $LastChangedDate$
#


import simuOpt
simuOpt.setOptions(quiet=True)

from simuPOP import *
import unittest, os, sys, exceptions, random

class TestInitialization(unittest.TestCase):

    def clearGenotype(self, pop):
        pop.setGenotype([0])

    def getGenotype(self, pop, atLoci=[], subPop=[], atPloidy=[]):
        geno = []
        if type(atPloidy) == type(1):
            ploidy = [atPloidy]
        elif len(atPloidy) > 0:
            ploidy = atPloidy
        else:
            ploidy = range(0, pop.ploidy())
        if len(atLoci) > 0:
            loci = atLoci
        else:
            loci = range(pop.totNumLoci())
        gs = pop.genoSize()
        tl = pop.totNumLoci()
        if len(subPop) > 0:
            for sp in subPop:
                for ind in pop.individuals(sp):
                        for p in ploidy:
                            for loc in loci:
                                geno.append(ind.allele(loc, p))
        else:
            arr = pop.genotype()
            if len(ploidy) == 0 and len(atLoci) == 0:
                geno = pop.arrGenotype(True)
            else:
                for i in range(pop.popSize()):
                    for p in ploidy:
                        for loc in loci:
                            geno.append( arr[ gs*i + p*tl +loc] )
        return geno

    def assertGenotype(self, pop, genotype, loci=[], subPop=[], atPloidy=[]):
        'Assert if the genotype of subPop of pop is genotype '
        geno = self.getGenotype(pop, loci, subPop, atPloidy)
        if moduleInfo()['alleleType'] == 'binary':
            if type(genotype) == type(1):
                self.assertEqual(geno, [genotype>0]*len(geno))
            else:
                self.assertEqual(geno, [x>0 for x in genotype])
        else:
            if type(genotype) == type(1):
                self.assertEqual(geno, [genotype]*len(geno))
            else:
                self.assertEqual(geno, genotype)

    def assertGenotypeFreq(self, pop, freqLow, freqHigh,loci=[], subPop=[], atPloidy=[]):
        'Assert if the genotype has the correct allele frequency'
        geno = self.getGenotype(pop, loci, subPop, atPloidy)
        if moduleInfo()['alleleType'] == 'binary':
            if len(freqLow) == 1:    # only one
                freq0 = geno.count(0)*1.0 / len(geno)
                self.assertTrue(freq0 >= freqLow[0], 
            "Expression freq0 (test value %f) be greater than or equal to freqLow[0]. This test may occasionally fail due to the randomness of outcome." % (freq0))
                self.assertTrue(freq0 <= freqHigh[0], 
            "Expression freq0 (test value %f) be less than or equal to freqHigh[0]. This test may occasionally fail due to the randomness of outcome." % (freq0))
            else:    # 0 and 1, but group all other freq.
                f0 = [freqLow[0], sum(freqLow[1:])]
                f1 = [freqHigh[0], sum(freqHigh[1:])]
                freq0 = geno.count(0)*1.0 / len(geno)
                freq1 = geno.count(1)*1.0 / len(geno)
                self.assertTrue(freq0 >= f0[0] , 
            "Expression freq0 (test value %f) be greater than or equal to f0[0] . This test may occasionally fail due to the randomness of outcome." % (freq0))
                self.assertTrue(freq0 <= f1[0], 
            "Expression freq0 (test value %f) be less than or equal to f1[0]. This test may occasionally fail due to the randomness of outcome." % (freq0))
                self.assertTrue(freq1 >= f0[1] , 
            "Expression freq1 (test value %f) be greater than or equal to f0[1] . This test may occasionally fail due to the randomness of outcome." % (freq1))
                self.assertTrue(freq1 <= f1[1], 
            "Expression freq1 (test value %f) be less than or equal to f1[1]. This test may occasionally fail due to the randomness of outcome." % (freq1))
        else:    # all loci
            for i in range(len(freqLow)):
                freq = geno.count(i)*1.0 / len(geno)
                self.assertTrue(freq >= freqLow[i] , 
            "Expression freq (test value %f) should be greater than or equal to %f . This test may occasionally fail due to the randomness of outcome." % (freq, freqLow[i]))
                self.assertTrue(freq <= freqHigh[i], 
            "Expression freq (test value %f) should be less than or equal to %f. This test may occasionally fail due to the randomness of outcome." % (freq, freqHigh[i]))

    
    def testInitSex(self):
        'Testing operator InitSex'
        pop = Population(size=[500, 1000], loci=[1])
        initSex(pop, sex=[MALE, FEMALE, FEMALE])
        for idx, ind in enumerate(pop.individuals()):
            if idx % 3 == 0:
                self.assertEqual(ind.sex(), MALE)
            else:
                self.assertEqual(ind.sex(), FEMALE)
        # maleFreq
        initSex(pop, maleFreq=0.3)
        count = 0
        for ind in pop.individuals():
            if ind.sex() == MALE:
                count += 1
        print count
        self.assertTrue(count / 1500. > 0.25 , 
            "Expression count / 1500. (test value %f) be greater than to 0.25 . This test may occasionally fail due to the randomness of outcome." % (count / 1500.))
        self.assertTrue(count /1500. < 0.35, 
            "Expression count /1500. (test value %f) be less than 0.35. This test may occasionally fail due to the randomness of outcome." % (count /1500.))
        # male proportion
        initSex(pop, maleProp=0.4)
        count = 0
        for ind in pop.individuals(0):
            if ind.sex() == MALE:
                count += 1
        self.assertEqual(count, 200)
        count = 0
        for ind in pop.individuals(1):
            if ind.sex() == MALE:
                count += 1
        self.assertEqual(count, 400)
        # subPop, virtual subPop
        pop = Population(size=[500, 1000], loci=[1], infoFields=['x'])
        for ind in pop.individuals():
            ind.setInfo(random.randint(10, 20), 'x')
        pop.setVirtualSplitter(InfoSplitter('x', values=range(10, 15)))
        initSex(pop, sex=[MALE, FEMALE, FEMALE], subPops=[[0,0],[1,0]])
        idx = 0
        for sp in range(2):
            for ind in pop.individuals([sp,0]):
                if idx % 3 == 0:
                    self.assertEqual(ind.sex(), MALE)
                else:
                    self.assertEqual(ind.sex(), FEMALE)
                idx += 1

    def testInitGenotype(self):
        'Testing operator InitByFreq '
        pop = Population(size=[500, 1000, 500], loci=[2,4,2])
        # initialize all
        initGenotype(pop, freq=[.2, .3, .5])
        self.assertGenotypeFreq(pop, [.15, .25, .45],
            [.25, .35, .55])
        #
        self.clearGenotype(pop)
        initGenotype(pop, freq=[.2, .3, .4, .1], loci=[2,4,6])
        self.assertGenotypeFreq(pop, [.15, .25, .35, .05],
            [.25, .35, .45, .15], loci=[2,4,6])
        self.assertGenotype(pop, 0, loci=[0,1,3,5,7])
        #
        self.clearGenotype(pop)
        initGenotype(pop, freq=[.2,.8], subPops=0)
        initGenotype(pop, freq=[.8,.2], subPops=1)
        initGenotype(pop, freq=[.5,.5], subPops=2)
        self.assertGenotypeFreq(pop, [.15, .75], [.25, .85], subPop=[0])
        self.assertGenotypeFreq(pop, [.75, .15], [.85, .25], subPop=[1])
        self.assertGenotypeFreq(pop, [.45, .45], [.55, .55], subPop=[2])
        #
        # ploidy in InitByFreq'
        pop = Population(size=[500, 1000, 500], loci=[2,4,2])
        self.clearGenotype(pop)
        initGenotype(pop, freq=[.2, .3, .5], loci=[2,4,6], ploidy=[0])
        self.assertGenotypeFreq(pop, [.15, .25, .45], [.25, .35, .55],
            loci=[2,4,6], atPloidy=0)
        self.assertGenotype(pop, 0, loci=[0,3,5,7])
        self.assertGenotype(pop, 0, atPloidy=1)
        # virtual subPop
        pop = Population(size=[5000, 10000, 5000], loci=[2,4,2], infoFields=['x'])
        for ind in pop.individuals():
            ind.setInfo(random.randint(10, 20), 'x')
        pop.setVirtualSplitter(InfoSplitter('x', values=range(10, 15)))
        for idx in range(3):
            freq=[[0.2, 0.3, 0.5], [0.2,0.8], [0.5, 0.5]]
            subPops=[[0,0],[1,1], [2,0]]
            initGenotype(pop, freq=freq[idx], subPops=[subPops[idx]],
            loci=[2,4,6])
        self.assertGenotypeFreq(pop, [.15, .25, .45], [.25, .35, .55], 
            subPop=[[0,0]], loci=[2,4,6])
        self.assertGenotypeFreq(pop, [.15, .75], [.25, .85], 
            subPop=[[1,1]], loci=[2,4,6])
        self.assertGenotypeFreq(pop, [.45, .45], [.55, .55], 
            subPop=[[2,0]], loci=[2,4,6])
        # corner case
        self.clearGenotype(pop)
        for idx in range(3):
            freq=[[0, 0, 1], [0, 1], [1]]
            subPops=[[0,0],[1,1], [2,1]]
            initGenotype(pop, freq=freq[idx], subPops=[subPops[idx]])
        for ind in pop.individuals([0,0]):
            if moduleInfo()['alleleType'] == 'binary':
                for allele in ind.genotype():
                     self.assertEqual(allele, 1) 
            else:
                for allele in ind.genotype():
                     self.assertEqual(allele, 2) 
        for ind in pop.individuals([1,1]):
            for allele in ind.genotype():
                 self.assertEqual(allele, 1)
        for ind in pop.individuals([2,1]):
            for allele in ind.genotype():
                 self.assertEqual(allele, 0)
        self.clearGenotype(pop)
        self.assertRaises(exceptions.ValueError,initGenotype, pop, freq=[-1,2])
        #
        pop = Population(size=[500,1000, 500], loci=[2,4,2], infoFields=['x'])
        for ind in pop.individuals():
            ind.setInfo(random.randint(10, 20), 'x')
        pop.setVirtualSplitter(InfoSplitter('x', values=range(10, 15)))
        # can initialize an invidiausl
        initGenotype(pop, genotype=[0]*5 + [2]*3 + [3]*5 +[4]*3)
        self.assertGenotype(pop, ([0]*5 + [2]*3 + [3]*5 +[4]*3)*pop.popSize())
        # one copy of chromosomes
        self.clearGenotype(pop)
        initGenotype(pop, genotype=[0]*5 + [7]*3)
        self.assertGenotype(pop, ([0]*5 + [7]*3)*(pop.popSize()*pop.ploidy()))
        # ploidy
        self.clearGenotype(pop)
        initGenotype(pop, genotype=[0]*5 + [1]*3 , ploidy=[1])
        self.assertGenotype( pop, ([0]*5 + [1]*3)*pop.popSize(), atPloidy=1)
        self.assertGenotype(pop, 0, atPloidy=0)
        # subPop, virtual subPop
        self.clearGenotype(pop)
        initGenotype(pop, genotype=[0]*5 + [2]*3 + [3]*5 +[4]*3, subPops=[[0,1], [1,0]])
        self.assertGenotype(pop, ([0]*5 + [2]*3 + [3]*5 +[4]*3)*
            (pop.subPopSize([0,1])+pop.subPopSize([1,0])), subPop=[[0,1], [1,0]])
        # loci
        self.clearGenotype(pop)
        initGenotype(pop, genotype=[0,1,5], loci=[2,4,5], subPops=[[0,0], [2,1]])
        self.assertGenotype(pop, [0,1,5]*2*(pop.subPopSize([0,0])+
            pop.subPopSize([2,1])), loci=[2,4,5], subPop=[[0,0], [2,1]])
        self.assertGenotype(pop, 0, loci=[0,1,3,6,7])

    def testInitByHaplotypes(self):
        'Testing initialization by haplotypes (operator InitGenotype)'
        pop = Population(size=[500, 1000, 500], loci=[2,4,2], infoFields=['x'])
        initGenotype(pop, haplotypes=[[0, 0], [1, 1]])
        self.assertGenotypeFreq(pop, [.45, .45], [.55, .55], loci=range(8))
        initGenotype(pop, haplotypes=[[0, 0, 1, 0], [1, 1, 0, 0]])
        self.assertGenotypeFreq(pop, [.45, .45], [.55, .55], loci=[0, 1, 2, 4, 5])
        self.assertGenotypeFreq(pop, [1, 0], [1, 0], loci=[3])
        initGenotype(pop, haplotypes=[[0, 0, 1, 1], [1, 1, 0, 0]], prop=[.2, .8])
        self.assertGenotypeFreq(pop, [.2, .8], [.2, .8], loci=[0, 1])
        self.assertGenotypeFreq(pop, [.8, .2], [.8, .2], loci=[2, 3])
        self.assertGenotypeFreq(pop, [.2, .8], [.2, .8], loci=[4, 5])
        

if __name__ == '__main__':
    unittest.main()
