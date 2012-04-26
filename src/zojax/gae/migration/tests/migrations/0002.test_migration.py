# -*- coding: utf-8 -*-

import time, logging


#from inboxer.model import

def test_step_apply(migration):
    logging.info("Running apply step 1 of migration!! %s " % str(migration))
    for i in range(1,3):
        logging.info("2nd mig, 1st step: %sth cycle" % str(i))
        #time.sleep(2)

def test_step_rollback(migration):
    logging.info(" 2 Running rollback step of migration!!")
    migration.succeed()

def test_step2_apply(migration):

    logging.info("Running apply step 2 of migration!! %s " % str(migration))
    for i in range(1,3):
        logging.info("2nd mig, 2nd step: %sth cycle" % str(i))
        #time.sleep(2)
    migration.succeed()
    #b = 'aa' / 0

def test_step2_rollback(migration):
    logging.info("Running rollback step 2 of migration!! %s " % migration)
    #migration.fail()


# 1st step
step(test_step_apply, test_step_rollback)


# 2nd step
step(test_step2_apply, test_step2_rollback)
