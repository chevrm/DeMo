#!/bin/env perl

use strict;
use warnings;
use Bio::SeqIO;

my $protein_domain_source = './src.faa';

## Get pairwise PIDs for each domain
system("cp $protein_domain_source ./full.faa");
system("diamond makedb --in full.faa -d full") unless(-e 'full.dmnd');
system("diamond blastp -q full.faa -d full -e 1 -f tab -o full.dbp -p 10 -k 1000000") unless(-e 'full.dbp');
