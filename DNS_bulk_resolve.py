#!/usr/bin/env python
#
#
import argparse
import dns.resolver
##Replace these...or provide arguments
DEFAULT_RESOLVER1 = "8.8.8.8"
DEFAULT_RESOLVER2 = "4.4.2.2"

def initialize():
    parser = argparse.ArgumentParser(
        description='DNS Result Comparison Utility'
    )
    parser.add_argument(
        '-r1', '--resolver1', dest='resolver1', metavar='resolver1',
        action='store', default=DEFAULT_RESOLVER1, type=str,
        help='First resolver to query (default: {0})'.format(DEFAULT_RESOLVER1)
        )
    parser.add_argument(
        '-r2', '--resolver2', dest='resolver2', metavar='resolver2',
        action='store', default=DEFAULT_RESOLVER2, type=str,
        help='Second resolver to query (default: {0})'.format(DEFAULT_RESOLVER2)
        )
    parser.add_argument("-v", "--verbose", dest='verbose', help="treats query failure types differently, writes matches to std out.", 
    	action="store_true")
    parser.add_argument(
        'recordfile',  metavar='recordfile', action='store', type=str,
        help='File containing list of the DNS record/s to query during testing (one on a line)'
    )
    args = parser.parse_args()

    if len(args.resolver1) == 0:
    	parser.error('Need two resolvers specified.')
   	if len(args.resolver2) == 0:
   		parser.error('Need two resolvers specified.')
    if len(args.recordfile) == 0:
    	parser.error('No DNS record file specified.')
    record_list = open(args.recordfile).readlines()
    if len(record_list) == 0:
    	parser.error('Invalid DNS record file.')

    return (args.resolver1, args.resolver2, record_list, args.verbose)


def dns_answer(nameserver, record):
	resolver = dns.resolver.Resolver(configure=False)
	ns_list = [nameserver]
	resolver.nameservers = ns_list
	result = None
	try:
		answer = resolver.query(record, 'A')
	except dns.resolver.NXDOMAIN:
		if verbose:
			result = 'NXDOMAIN'
		else:
			result = 'UNRESOLVED'
	except dns.resolver.NoAnswer:
		if verbose:
			result = 'NO ANSWER'
		else:
			result = 'UNRESOLVED'
	except dns.resolver.NoNameservers:
		if verbose:
			result = 'SERVFAIL'
		else:
			result = 'UNRESOLVED'
	if result is not None:
		return result
	else:
		for data in answer:
			return data.address

def rr_gslb_check(nameserver, record):
	#Returns a santized list of all UNIQUE answers after 10 queries.
	ns_ans_list = []
	for n in range(0,9):
		ns_answer = dns_answer(nameserver, record)
		ns_ans_list.append(ns_answer)
	ns_ans_sorted = sorted(set(ns_ans_list))
	return ns_ans_sorted

def rec_list_compare(ns_list1, ns_list2):
	list_comp = [blah for blah in ns_list1 if blah not in ns_list2]
	return list_comp


##So let's do this
(ns1, ns2, record_list, verbose) = initialize()
for record_ugly in record_list:
	record = record_ugly.rstrip('\r\n')
	ns1_answer = dns_answer(ns1, record)
	ns2_answer = dns_answer(ns2, record)
	if ns1_answer == ns2_answer:
		#Nothing, rly if verbose=true
		if verbose:	
			print "Nameservers agree on DNS answer for {0}: {1}.".format(record, ns1_answer)
		else:
			pass
	else:
		rr_check1 = rr_gslb_check(ns1, record)
		rr_check2 = rr_gslb_check(ns2, record)
		rr_results = rec_list_compare(rr_check1, rr_check2)
		if len(rr_results) > 0:
			#Houston...we have a mismatch
			print "###################"
			print "MISMATCH:"
			print "Record: {0}".format(record)
			print "{0} possible answers: {1}".format(ns1, rr_check1)
			print "{0} possible answers: {1}".format(ns2, rr_check2)
			print "###################"
		else:
			if verbose:
				print "Nameservers agree on possible DNS answers for {0}: {1}.".format(record, rr_check1)
			else:
				pass
				##and be done


